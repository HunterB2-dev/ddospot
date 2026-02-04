"""
Flask web dashboard for the DDoSPot honeypot.
Provides real-time visualization of attacks and statistics.
"""

from flask import Flask, render_template, jsonify, request, g
from flask_cors import CORS
from flask import Response
from core.database import HoneypotDatabase
from core.geolocation import get_geolocation_service
from core.performance import get_performance_monitor
from telemetry.alerts import get_alert_manager
from telemetry.logger import get_logger
from telemetry.prometheus_metrics import get_metrics
from telemetry.ratelimit import RateLimiter
from app.api_auth import require_api_key, RateLimiter as APIRateLimiter, add_rate_limit_headers, APIKeyAuth
import os
from functools import wraps
from ml.model import get_model
from ml.features import FeatureExtractor
import json
import asyncio
from typing import Dict
from datetime import datetime
import time

# Initialize Flask app
app = Flask(__name__, template_folder='../templates', static_folder='../static')
CORS(app)

logger = get_logger("ddospot.dashboard")

# Prometheus metrics
metrics = get_metrics()

# ------------------------
# Security configuration
# ------------------------
def _env_bool(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return str(val).strip().lower() in ("1", "true", "yes", "on")

def _load_config_token() -> str | None:
    try:
        cfg_path = os.path.join(os.path.dirname(__file__), "config", "config.json")
        if os.path.exists(cfg_path):
            with open(cfg_path) as f:
                cfg = json.load(f)
                api_cfg = cfg.get("api", {})
                token = api_cfg.get("token")
                if token:
                    return str(token)
    except Exception:
        pass
    return None

SEC_TOKEN = os.getenv("DDOSPOT_API_TOKEN") or _load_config_token()
SEC_REQUIRE_TOKEN = _env_bool("DDOSPOT_REQUIRE_TOKEN", False)
SEC_METRICS_PUBLIC = _env_bool("DDOSPOT_METRICS_PUBLIC", True)
SEC_REQUIRE_TOKEN_FOR_HEALTH = _env_bool("DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH", False)

def _get_api_token() -> str | None:
    """Expose API token for tests and diagnostics (dynamic)."""
    return os.getenv("DDOSPOT_API_TOKEN") or _load_config_token()

# Rate limiter (defaults are conservative; configurable via env)
RATE_LIMIT_MAX = int(os.getenv("DDOSPOT_RATE_LIMIT_MAX", "300") or 300)
RATE_LIMIT_WINDOW = int(os.getenv("DDOSPOT_RATE_LIMIT_WINDOW", "60") or 60)
RATE_LIMIT_BLACKLIST = int(os.getenv("DDOSPOT_RATE_LIMIT_BLACKLIST", "120") or 120)
_rate_limiter = RateLimiter(max_events=RATE_LIMIT_MAX,
                            window_seconds=RATE_LIMIT_WINDOW,
                            blacklist_seconds=RATE_LIMIT_BLACKLIST)

# Whitelist localhost and local IPs from rate limiting
RATE_LIMIT_WHITELIST = {'127.0.0.1', 'localhost', '::1', '0.0.0.0'}

def _client_ip() -> str:
    # Prefer X-Forwarded-For if behind proxy, else remote_addr
    fwd = request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
    return fwd or (request.remote_addr or "unknown")

def _extract_token() -> str | None:
    auth = request.headers.get("Authorization", "").strip()
    if auth.lower().startswith("bearer "):
        return auth[7:].strip()
    header_token = request.headers.get("X-API-Token")
    if header_token:
        return header_token.strip()
    query_token = request.args.get("token")
    if query_token:
        return str(query_token).strip()
    return None

def require_token(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Evaluate requirement dynamically to respect env set during tests
        if not _env_bool("DDOSPOT_REQUIRE_TOKEN", False):
            return func(*args, **kwargs)
        provided = _extract_token()
        current_token = _get_api_token()
        if not current_token:
            logger.warning("Token authentication required but no token configured")
            return jsonify({"error": "unauthorized"}), 401
        if provided != current_token:
            return jsonify({"error": "unauthorized"}), 401
        return func(*args, **kwargs)
    return wrapper

def ensure_token_if(condition):
    """
    Ensure a valid token if condition is truthy.
    Condition may be a bool or a callable returning bool; evaluated per-request.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cond_value = condition() if callable(condition) else condition
            if not cond_value:
                return func(*args, **kwargs)
            provided = _extract_token()
            current_token = _get_api_token()
            if not current_token or provided != current_token:
                return jsonify({"error": "unauthorized"}), 401
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Database and geolocation instances
db = None
geo_service = None
alert_manager = None
ml_model = None
feature_extractor = None


# Performance tracking middleware
@app.before_request
def track_request_start():
    """Track the start of a request"""
    g.request_start_time = time.time()


@app.after_request
def track_request_end(response):
    """Track the end of a request and record metrics"""
    try:
        if hasattr(g, 'request_start_time'):
            response_time = time.time() - g.request_start_time
            endpoint = request.path
            method = request.method
            status_code = response.status_code
            
            # Track the request
            perf_monitor = get_performance_monitor()
            perf_monitor.track_request(f"{method} {endpoint}", response_time, status_code, method)
            
            # Update system resources every 10 requests
            if perf_monitor.request_counts.get(f"{method} {endpoint}", 0) % 10 == 0:
                perf_monitor.update_system_resources()
    except Exception as e:
        logger.debug(f"Error tracking request metrics: {e}")
    
    return response


def init_db():
    """Initialize database connection"""
    global db, geo_service, alert_manager, ml_model, feature_extractor
    db = HoneypotDatabase("logs/honeypot.db")
    geo_service = get_geolocation_service("logs/honeypot.db")
    alert_manager = get_alert_manager("logs/honeypot.db", "config/alert_config.json")
    ml_model = get_model()
    feature_extractor = FeatureExtractor()
    
    # Initialize evasion detection API
    try:
        from app.evasion_api import evasion_api, init_evasion_api
        init_evasion_api(db)
        app.register_blueprint(evasion_api)
        logger.info("Evasion detection API initialized and registered")
    except Exception as e:
        logger.warning(f"Could not initialize evasion detection API: {e}")
    
    # Initialize threat intelligence API
    try:
        from app.threat_intelligence_api import threat_intelligence_api, init_threat_intelligence_api
        init_threat_intelligence_api(db)
        app.register_blueprint(threat_intelligence_api)
        logger.info("Threat intelligence API initialized and registered")
    except Exception as e:
        logger.warning(f"Could not initialize threat intelligence API: {e}")
    
    # Initialize response system API
    try:
        from app.response_api import response_api, init_response_api
        init_response_api(db)
        app.register_blueprint(response_api)
        logger.info("Response system API initialized and registered")
    except Exception as e:
        logger.warning(f"Could not initialize response system API: {e}")
    
    # Update initial metrics
    metrics.update_service_status("dashboard", True)
    metrics.update_system_metrics()
    metrics.update_log_metrics()


def get_database():
    """Get the global database instance"""
    global db
    if db is None:
        init_db()
    return db


# ========================
# API ENDPOINTS
# ========================

@app.before_request
def before_request():
    """Track request start time for metrics and enforce rate limits"""
    request._prometheus_start_time = time.time()

    # Apply rate limiting to API, metrics, and health endpoints
    path = (request.path or "")
    if path.startswith("/api") or path.startswith("/metrics") or path.startswith("/health"):
        # Skip rate limiting during tests
        if getattr(app, "testing", False) or _env_bool("DDOSPOT_TESTING", False):
            return None
        ip = _client_ip()
        # Skip rate limiting for localhost/local IPs
        if ip in RATE_LIMIT_WHITELIST:
            return None
        allowed = _rate_limiter.register_event(ip)
        if not allowed:
            return jsonify({"error": "too_many_requests"}), 429

@app.after_request
def after_request(response):
    """Record request metrics"""
    if hasattr(request, '_prometheus_start_time'):
        duration = time.time() - request._prometheus_start_time
        endpoint = request.endpoint or 'unknown'
        metrics.record_http_request(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
            duration=duration
        )
    return response

@app.route('/metrics', methods=['GET'])
@ensure_token_if(lambda: not _env_bool("DDOSPOT_METRICS_PUBLIC", True))
def prometheus_metrics():
    """Prometheus metrics endpoint"""
    try:
        # Update dynamic metrics before exporting
        metrics.update_system_metrics()
        metrics.update_log_metrics()
        
        # Update database metrics
        if db:
            try:
                size_info = db.get_database_size()
                metrics.update_database_metrics(
                    size_bytes=int(size_info['size_mb'] * 1024 * 1024),
                    event_count=size_info['event_count'],
                    profile_count=size_info['profile_count']
                )
                
                stats = db.get_statistics()
                metrics.unique_attackers.set(stats.get('unique_ips', 0))
                metrics.blacklisted_ips.set(stats.get('blacklisted_ips', 0))
                
                # Update geolocation metrics
                if geo_service and hasattr(geo_service, 'cache'):
                    map_data = geo_service.cache.get_map_data()
                    countries = set(point['country'] for point in map_data)
                    metrics.geolocation_countries_total.set(len(countries))
            except Exception as e:
                logger.debug(f"Error updating metrics: {e}")
        
        # Generate metrics
        output = metrics.get_metrics()
        return Response(output, mimetype='text/plain; version=0.0.4; charset=utf-8')
    except Exception as e:
        logger.error(f"Error generating metrics: {e}")
        return Response(f"# Error: {e}\n", mimetype='text/plain'), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall honeypot statistics"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    hours = request.args.get('hours', default=720, type=int)
    stats = db.get_statistics(hours)
    
    return jsonify(stats)


@app.route('/api/top-attackers', methods=['GET'])
def get_top_attackers():
    """Get top attacking IPs"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    limit = request.args.get('limit', default=10, type=int)
    attackers = db.get_top_attackers(limit)
    
    # Convert to JSON-serializable format
    result = []
    for attacker in attackers:
        result.append({
            'ip': attacker['ip'],
            'events': attacker['total_events'],
            'type': attacker['attack_type'],
            'rate': round(attacker['events_per_minute'], 2),
            'protocols': attacker['protocols_used'].split(',') if attacker['protocols_used'] else [],
            'severity': 'unknown',
        })
    
    return jsonify(result)


@app.route('/api/blacklist', methods=['GET'])
def get_blacklist():
    """Get current blacklist"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    blacklist = db.get_blacklist()
    
    result = []
    now = datetime.now().timestamp()
    for entry in blacklist:
        expires_in = int(entry['expiration_time'] - now)
        result.append({
            'ip': entry['ip'],
            'reason': entry['reason'],
            'severity': entry['severity'],
            'expires_in': expires_in,
            'expires_at': datetime.fromtimestamp(entry['expiration_time']).isoformat(),
        })
    
    return jsonify(result)


@app.route('/api/profile/<ip>', methods=['GET'])
def get_profile(ip):
    """Get detailed profile for an IP"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    profile = db.get_profile(ip)
    if not profile:
        return jsonify({"error": f"No profile found for {ip}"}), 404
    
    # Get recent events
    events = db.get_events_by_ip(ip, limit=50)
    event_list = []
    for event in events:
        event_list.append({
            'timestamp': datetime.fromtimestamp(event['timestamp']).isoformat(),
            'port': event['port'],
            'protocol': event['protocol'],
            'size': event['payload_size'],
            'type': event['event_type'],
        })
    
    return jsonify({
        'ip': profile['ip'],
        'first_seen': datetime.fromtimestamp(profile['first_seen']).isoformat(),
        'last_seen': datetime.fromtimestamp(profile['last_seen']).isoformat(),
        'total_events': profile['total_events'],
        'rate': round(profile['events_per_minute'], 2),
        'attack_type': profile['attack_type'],
        'protocols': profile['protocols_used'].split(',') if profile['protocols_used'] else [],
        'avg_payload': round(profile['avg_payload_size'], 0),
        'severity': profile['severity'],
        'recent_events': event_list,
    })


@app.route('/api/recent-events', methods=['GET'])
def get_recent_events():
    """Get recent attack events"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    minutes = request.args.get('minutes', default=43200, type=int)  # 30 days default
    page_size = request.args.get('page_size', default=50, type=int)
    page = request.args.get('page', default=1, type=int)
    ip = request.args.get('ip', default='', type=str).strip() or None
    protocol = request.args.get('protocol', default='', type=str).strip() or None
    event_type = request.args.get('type', default='', type=str).strip() or None
    
    page = max(1, page)
    page_size = max(1, min(page_size, 200))
    offset = (page - 1) * page_size
    
    total = db.count_recent_events_filtered(minutes, ip=ip, protocol=protocol, event_type=event_type)
    events = db.get_recent_events_filtered(minutes, limit=page_size, offset=offset,
                                           ip=ip, protocol=protocol, event_type=event_type)
    
    items = []
    for event in events:
        items.append({
            'timestamp': datetime.fromtimestamp(event['timestamp']).isoformat(),
            'ip': event['source_ip'],
            'port': event['port'],
            'protocol': event['protocol'],
            'size': event['payload_size'],
            'type': event['event_type'],
        })
    
    return jsonify({
        'items': items,
        'page': page,
        'page_size': page_size,
        'total': total,
        'filters': {
            'ip': ip or '',
            'protocol': protocol or '',
            'type': event_type or ''
        }
    })


@app.route('/api/timeline', methods=['GET'])
def get_timeline():
    """Get attack timeline for charting"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    hours = request.args.get('hours', default=720, type=int)
    bucket_minutes = request.args.get('bucket', default=5, type=int)
    
    timeline = db.get_attack_timeline(hours, bucket_minutes)
    
    result = []
    for point in timeline:
        result.append({
            'time': datetime.fromtimestamp(point['bucket_time']).isoformat(),
            'events': point['event_count'],
            'unique_ips': point['unique_ips'],
            'avg_payload': round(point['avg_payload'], 0) if point['avg_payload'] else 0,
        })
    
    return jsonify(result)


@app.route('/api/severity-breakdown', methods=['GET'])
def get_severity_breakdown():
    """Get attack breakdown by severity"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    result = {}
    for severity in ['low', 'medium', 'high', 'critical']:
        profiles = db.get_profiles_by_severity(severity)
        result[severity] = {
            'count': len(profiles),
            'events': sum(p['total_events'] for p in profiles),
            'ips': [p['ip'] for p in profiles],
        }
    
    return jsonify(result)


@app.route('/api/protocol-breakdown', methods=['GET'])
def get_protocol_breakdown():
    """Get attack breakdown by protocol"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    events = db.get_recent_events(43200, 100000)  # Last 30 days (43200 minutes)
    
    protocols = {}
    for event in events:
        proto = event['protocol']
        if proto not in protocols:
            protocols[proto] = 0
        protocols[proto] += 1
    
    return jsonify(protocols)


@app.route('/api/database-info', methods=['GET'])
def get_database_info():
    """Get database information"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    info = db.get_database_size()
    
    return jsonify({
        'size_mb': info['size_mb'],
        'event_count': info['event_count'],
        'profile_count': info['profile_count'],
        'path': info['file_path'],
    })


# ========================
# GEOLOCATION ENDPOINTS
# ========================

@app.route('/api/geolocation/<ip>', methods=['GET'])
def get_ip_geolocation(ip):
    """Get geolocation data for an IP"""
    if not geo_service:
        return jsonify({"error": "Geolocation service not initialized"}), 500
    
    try:
        # Run async function in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        geo_data = loop.run_until_complete(geo_service.get_geolocation(ip))
        loop.close()
        
        if geo_data:
            return jsonify(geo_data)
        else:
            return jsonify({"error": "Could not fetch geolocation"}), 404
    except Exception as e:
        logger.error(f"Geolocation error for {ip}: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/map-data', methods=['GET'])
def get_map_data():
    """Get geolocation data for all attacking IPs for map visualization"""
    if not geo_service:
        return jsonify({"error": "Geolocation service not initialized"}), 500
    
    try:
        map_data = geo_service.cache.get_map_data()
        return jsonify(map_data)
    except Exception as e:
        logger.error(f"Map data error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/country-stats', methods=['GET'])
def get_country_stats():
    """Get attack statistics by country"""
    if not geo_service:
        return jsonify({"error": "Geolocation service not initialized"}), 500
    
    try:
        stats = geo_service.cache.get_country_stats()
        return jsonify(stats)
    except Exception as e:
        logger.error(f"Country stats error: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# ALERT ENDPOINTS
# ========================

@app.route('/api/alerts/config', methods=['GET'])
def get_alert_config():
    """Get current alert configuration"""
    if not alert_manager:
        return jsonify({"error": "Alert manager not initialized"}), 500
    
    return jsonify(alert_manager.config.config)


@app.route('/api/alerts/config', methods=['POST'])
@require_token
def update_alert_config():
    """Update alert configuration"""
    if not alert_manager:
        return jsonify({"error": "Alert manager not initialized"}), 500
    
    try:
        data = request.get_json(silent=True)
        if not isinstance(data, dict):
            return jsonify({"error": "invalid_payload"}), 400
        
        # Update nested config values
        for key, value in data.items():
            alert_manager.config.set(key, value)
        
        return jsonify({"status": "success", "message": "Alert config updated"})
    except Exception as e:
        logger.error(f"Alert config update error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/test', methods=['POST'])
@require_token
def test_alert():
    """Send test alert"""
    if not alert_manager:
        return jsonify({"error": "Alert manager not initialized"}), 500
    
    try:
        alert_type = request.args.get('type', 'critical_attack')
        
        if alert_type == 'critical_attack':
            success = alert_manager.alert_critical_attack(
                ip='192.0.2.1',
                severity='critical',
                event_count=150,
                protocols=['HTTP', 'SSDP']
            )
        elif alert_type == 'blacklist':
            success = alert_manager.alert_ip_blacklisted(
                ip='192.0.2.1',
                reason='volumetric_attack',
                severity='high'
            )
        elif alert_type == 'sustained':
            success = alert_manager.alert_sustained_attack(
                duration_minutes=30,
                event_count=500
            )
        else:
            return jsonify({"error": "Unknown alert type"}), 400
        
        return jsonify({
            "status": "success" if success else "failed",
            "message": "Test alert sent" if success else "Test alert failed"
        })
    except Exception as e:
        logger.error(f"Test alert error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/history', methods=['GET'])
def get_alert_history():
    """Get alert history"""
    if not alert_manager:
        return jsonify({"error": "Alert manager not initialized"}), 500
    
    try:
        limit = request.args.get('limit', 50, type=int)
        history = alert_manager.get_alert_history(limit)
        return jsonify(history)
    except Exception as e:
        logger.error(f"Alert history error: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# WEB PAGES
# ========================

@app.route('/favicon.ico')
def favicon():
    """Return 204 No Content for favicon requests"""
    return '', 204


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/simple')
def simple_dashboard():
    """Simple dashboard with basic features"""
    return render_template('simple.html')


@app.route('/advanced')
def advanced_dashboard():
    """Advanced dashboard with full features"""
    return render_template('advanced-dashboard.html')


@app.route('/profile/<ip>')
def profile_page(ip):
    """Detailed profile page"""
    return render_template('profile.html', ip=ip)


@app.route('/settings')
def settings_page():
    """Settings configuration page (Feature #11)"""
    # Using global db instead of creating new connection
    db.init_default_config()
    return render_template('settings.html')


@app.route('/mobile')
def mobile_dashboard():
    """Mobile dashboard page with PWA support (Feature #12)"""
    return render_template('mobile-dashboard.html')


@app.route('/manifest.json')
def manifest():
    """PWA manifest file (Feature #12)"""
    return app.send_static_file('manifest.json')


@app.route('/health', methods=['GET'])
@ensure_token_if(lambda: _env_bool("DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH", False))
def health():
    """Health check endpoint"""
    try:
        if db:
            # Try a simple query
            db.get_statistics(1)
            return jsonify({"status": "healthy"}), 200
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 500
    
    return jsonify({"status": "unknown"}), 500


@app.route('/health-status', methods=['GET'])
@ensure_token_if(lambda: _env_bool("DDOSPOT_REQUIRE_TOKEN_FOR_HEALTH", False))
def health_status():
    """Health status page (HTML)"""
    return render_template('health.html')


# ========================
# ERROR HANDLERS
# ========================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({"error": "Not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({"error": "Internal server error"}), 500


# ========================
# EXPORT ENDPOINTS
# ========================

@app.route('/api/export/events/csv', methods=['GET'])
def export_events_csv():
    """Export recent events as CSV"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        import csv
        from io import StringIO
        
        hours = request.args.get('hours', default=720, type=int)
        events = db.get_recent_events(hours, 10000)
        
        # Create CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=['timestamp', 'ip', 'port', 'protocol', 'size', 'type', 'country'])
        writer.writeheader()
        
        for event in events:
            writer.writerow({
                'timestamp': datetime.fromtimestamp(event['timestamp']).isoformat(),
                'ip': event['source_ip'],
                'port': event['destination_port'],
                'protocol': event['protocol'],
                'size': event['payload_size'],
                'type': event['event_type'],
                'country': event.get('country', 'Unknown')
            })
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=ddospot_events.csv'}
        )
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/events/json', methods=['GET'])
def export_events_json():
    """Export recent events as JSON"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        hours = request.args.get('hours', default=720, type=int)
        events = db.get_recent_events(hours, 10000)
        
        result = []
        for event in events:
            result.append({
                'timestamp': datetime.fromtimestamp(event['timestamp']).isoformat(),
                'ip': event['source_ip'],
                'port': event['destination_port'],
                'protocol': event['protocol'],
                'size': event['payload_size'],
                'type': event['event_type'],
                'country': event.get('country', 'Unknown')
            })
        
        return Response(
            json.dumps(result, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=ddospot_events.json'}
        )
    except Exception as e:
        logger.error(f"JSON export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/stats/json', methods=['GET'])
def export_stats_json():
    """Export statistics as JSON"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        hours = request.args.get('hours', default=720, type=int)
        stats = db.get_statistics(hours)
        
        return Response(
            json.dumps(stats, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=ddospot_stats.json'}
        )
    except Exception as e:
        logger.error(f"Stats export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/profiles/json', methods=['GET'])
def export_profiles_json():
    """Export IP profiles as JSON"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        profiles = db.get_profiles(limit=10000)
        
        result = []
        for profile in profiles:
            result.append({
                'ip': profile['ip'],
                'total_events': profile['total_events'],
                'severity': profile['severity'],
                'last_seen': datetime.fromtimestamp(profile['last_seen']).isoformat() if profile['last_seen'] else None,
                'first_seen': datetime.fromtimestamp(profile['first_seen']).isoformat() if profile['first_seen'] else None,
                'protocols': profile.get('protocols', {})
            })
        
        return Response(
            json.dumps(result, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=ddospot_profiles.json'}
        )
    except Exception as e:
        logger.error(f"Profiles export error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/export/report/json', methods=['GET'])
def export_report_json():
    """Export comprehensive report as JSON"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        hours = request.args.get('hours', default=720, type=int)
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period_hours': hours,
            'statistics': db.get_statistics(hours),
            'top_attackers': [p['ip'] for p in db.get_profiles(limit=10)],
            'blacklist_count': len(db.get_blacklist()),
            'protocols': {},
            'severity_breakdown': {}
        }
        
        # Add protocol breakdown
        events = db.get_recent_events(hours, 10000)
        protocols = {}
        for event in events:
            proto = event['protocol']
            protocols[proto] = protocols.get(proto, 0) + 1
        report['protocols'] = protocols
        
        # Add severity breakdown
        for severity in ['low', 'medium', 'high', 'critical']:
            profiles = db.get_profiles_by_severity(severity)
            report['severity_breakdown'][severity] = {
                'count': len(profiles),
                'events': sum(p['total_events'] for p in profiles)
            }
        
        return Response(
            json.dumps(report, indent=2),
            mimetype='application/json',
            headers={'Content-Disposition': 'attachment; filename=ddospot_report.json'}
        )
    except Exception as e:
        logger.error(f"Report export error: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# ML MODEL ENDPOINTS
# ========================

@app.route('/api/ml/model-stats', methods=['GET'])
def get_model_stats():
    """Get ML model statistics and performance"""
    if not ml_model:
        return jsonify({"error": "ML model not available"}), 500
    
    try:
        stats = ml_model.get_stats()
        importance = ml_model.get_feature_importance()
        
        return jsonify({
            'is_trained': ml_model.is_trained,
            'model_path': ml_model.model_path,
            'features_count': stats.get('features_count', 0),
            'attack_types': stats.get('attack_types', []),
            'top_features': sorted(
                importance.items(),
                key=lambda x: x[1],
                reverse=True
            )[:5] if importance else [],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Model stats error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ml/predict/<ip>', methods=['GET'])
def predict_attack(ip):
    """Predict attack type for a given IP"""
    if not ml_model or not db or not feature_extractor:
        return jsonify({"error": "ML components not available"}), 500
    
    try:
        events = db.get_events_by_ip(ip, limit=1000)
        
        if not events:
            return jsonify({"prediction": "no_data", "confidence": 0.0})
        
        # Extract features
        features_dict = feature_extractor.extract_from_events(events)
        feature_names = feature_extractor.get_feature_names()
        feature_vector = [features_dict.get(name, 0) for name in feature_names]
        
        # Predict
        attack_type, confidence = ml_model.predict(feature_vector)
        
        return jsonify({
            'ip': ip,
            'event_count': len(events),
            'prediction': attack_type,
            'confidence': float(confidence),
            'features': features_dict,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ml/train', methods=['POST'])
@require_token
def train_model():
    """Train model on current database"""
    if not ml_model or not db:
        return jsonify({"error": "ML components not available"}), 500
    
    try:
        from ml.train import train_from_database
        
        metrics = train_from_database(db_path='honeypot.db', use_synthetic=False)
        
        return jsonify({
            'status': 'training_started',
            'metrics': metrics,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Training error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/ml/batch-predict', methods=['POST'])
@require_token
def batch_predict():
    """Predict attack types for multiple IPs"""
    if not ml_model or not db or not feature_extractor:
        return jsonify({"error": "ML components not available"}), 500
    
    try:
        data = request.get_json(silent=True) or {}
        ips = data.get('ips', [])
        limit = data.get('limit', 100)

        if not isinstance(ips, list) or any(not isinstance(x, str) for x in ips):
            return jsonify({"error": "invalid_ips"}), 400
        try:
            limit = int(limit)
        except Exception:
            return jsonify({"error": "invalid_limit"}), 400
        limit = max(1, min(limit, 1000))
        
        predictions = {}
        for ip in ips[:10]:  # Limit to 10 IPs per request
            try:
                events = db.get_events_by_ip(ip, limit=limit)
                if events:
                    features_dict = feature_extractor.extract_from_events(events)
                    feature_names = feature_extractor.get_feature_names()
                    feature_vector = [features_dict.get(name, 0) for name in feature_names]
                    attack_type, confidence = ml_model.predict(feature_vector)
                    predictions[ip] = {
                        'prediction': attack_type,
                        'confidence': float(confidence),
                        'events': len(events)
                    }
            except Exception as e:
                logger.debug(f"Prediction error for {ip}: {e}")
        
        return jsonify({
            'predictions': predictions,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Batch prediction error: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# ADVANCED SEARCH & FILTERING
# ========================

@app.route('/api/search/advanced', methods=['GET'])
def advanced_search():
    """Advanced search with filtering by IP, date range, country, protocol"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        # Get query parameters
        search_ip = request.args.get('ip', '').strip()
        protocol = request.args.get('protocol', '').strip().upper()
        country = request.args.get('country', '').strip()
        hours = request.args.get('hours', default=720, type=int)
        limit = request.args.get('limit', default=100, type=int)
        offset = request.args.get('offset', default=0, type=int)
        
        # Validate inputs
        hours = max(1, min(hours, 720))  # 1 to 30 days
        limit = max(1, min(limit, 1000))  # 1 to 1000
        offset = max(0, offset)
        
        # Get filtered events
        events = db.get_recent_events_filtered(
            minutes=hours*60,
            ip=search_ip if search_ip else None,
            protocol=protocol if protocol else None,
            limit=limit,
            offset=offset
        )
        
        # Filter by country if specified (skip geolocation for now - just return without geo)
        result_events = events
        if country:
            # For now, just return without country filtering since geolocation is async
            # This will be added in a future enhancement
            pass
        
        # Count total for pagination
        total = db.count_recent_events_filtered(
            minutes=hours*60,
            ip=search_ip if search_ip else None,
            protocol=protocol if protocol else None
        )
        
        return jsonify({
            'events': result_events,
            'total': total,
            'limit': limit,
            'offset': offset,
            'returned': len(result_events),
            'filters': {
                'ip': search_ip,
                'protocol': protocol,
                'country': country,
                'hours': hours
            }
        })
        
    except Exception as e:
        logger.error(f"Advanced search error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/countries', methods=['GET'])
def get_search_countries():
    """Get list of countries with attacks for dropdown"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        # Get all events from last 30 days
        # Events already have country field populated from database
        all_events = db.get_recent_events_filtered(minutes=30*24*60, limit=10000)
        countries = set()
        
        for event in all_events:
            country = event.get('country')
            if country and country.strip():
                countries.add(country.strip())
        
        return jsonify({
            'countries': sorted(list(countries))
        })
        
    except Exception as e:
        logger.error(f"Country list error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/export', methods=['GET'])
def export_search_results():
    """Export search results as CSV"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        search_ip = request.args.get('ip', '').strip()
        protocol = request.args.get('protocol', '').strip().upper()
        country = request.args.get('country', '').strip()
        hours = request.args.get('hours', default=720, type=int)
        
        # Get filtered events
        events = db.get_recent_events_filtered(
            minutes=hours*60,
            ip=search_ip if search_ip else None,
            protocol=protocol if protocol else None,
            limit=10000
        )
        
        # Filter by country (from event data)
        if country:
            filtered_events = []
            for event in events:
                event_country = event.get('country', '').strip()
                if event_country.lower() == country.lower():
                    filtered_events.append(event)
            events = filtered_events
        
        # Generate CSV
        import csv
        from io import StringIO
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['Timestamp', 'Source IP', 'Country', 'Port', 'Protocol', 'Payload Size', 'Event Type'])
        
        for event in events:
            ts = datetime.fromtimestamp(event['timestamp']).strftime('%Y-%m-%d %H:%M:%S')
            writer.writerow([
                ts,
                event['source_ip'],
                event.get('country', 'Unknown'),
                event['port'],
                event['protocol'],
                event['payload_size'],
                event['event_type']
            ])
        
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=search_results.csv'}
        )
        
    except Exception as e:
        logger.error(f"Export error: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# ALERT RULES ENDPOINTS
# ========================

@app.route('/api/alerts/rules', methods=['GET'])
def get_alert_rules():
    """Get all alert rules"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        enabled_only = request.args.get('enabled_only', 'false').lower() == 'true'
        rules = db.get_alert_rules(enabled_only=enabled_only)
        
        return jsonify({
            'rules': rules,
            'total': len(rules)
        })
    except Exception as e:
        logger.error(f"Error fetching alert rules: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/rules', methods=['POST'])
def create_alert_rule():
    """Create new alert rule"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required = ['name', 'condition_type', 'condition_field', 'condition_operator', 
                   'condition_value', 'action']
        if not all(k in data for k in required):
            return jsonify({"error": "Missing required fields"}), 400
        
        rule_id = db.create_alert_rule(
            name=data['name'],
            description=data.get('description', ''),
            condition_type=data['condition_type'],
            condition_field=data['condition_field'],
            condition_operator=data['condition_operator'],
            condition_value=data['condition_value'],
            action=data['action'],
            action_target=data.get('action_target'),
            threshold=data.get('threshold', 1),
            time_window_minutes=data.get('time_window_minutes', 1)
        )
        
        return jsonify({
            'success': True,
            'rule_id': rule_id,
            'message': f'Alert rule "{data["name"]}" created'
        }), 201
        
    except Exception as e:
        logger.error(f"Error creating alert rule: {e}")
        if "UNIQUE constraint failed" in str(e):
            return jsonify({"error": "Rule name already exists"}), 400
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/rules/<int:rule_id>', methods=['PUT'])
def update_alert_rule(rule_id):
    """Update alert rule"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        data = request.get_json()
        success = db.update_alert_rule(rule_id, **data)
        
        if not success:
            return jsonify({"error": "Rule not found"}), 404
        
        return jsonify({
            'success': True,
            'message': 'Alert rule updated'
        })
        
    except Exception as e:
        logger.error(f"Error updating alert rule: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/rules/<int:rule_id>', methods=['DELETE'])
def delete_alert_rule(rule_id):
    """Delete alert rule"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        success = db.delete_alert_rule(rule_id)
        
        if not success:
            return jsonify({"error": "Rule not found"}), 404
        
        return jsonify({
            'success': True,
            'message': 'Alert rule deleted'
        })
        
    except Exception as e:
        logger.error(f"Error deleting alert rule: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/alerts/rules/<int:rule_id>/test', methods=['POST'])
def test_alert_rule(rule_id):
    """Test alert rule with sample data"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        rule = db.get_alert_rule(rule_id)
        if not rule:
            return jsonify({"error": "Rule not found"}), 404
        
        data = request.get_json() or {}
        test_event = data.get('test_event', {})
        
        # Evaluate the rule against test data
        result = evaluate_alert_rule(rule, test_event)
        
        return jsonify({
            'success': True,
            'rule_id': rule_id,
            'matched': result,
            'message': 'Alert rule test completed'
        })
        
    except Exception as e:
        logger.error(f"Error testing alert rule: {e}")
        return jsonify({"error": str(e)}), 500


def evaluate_alert_rule(rule: Dict, event: Dict) -> bool:
    """Evaluate if an event matches an alert rule"""
    try:
        field_value = event.get(rule['condition_field'])
        condition_value = rule['condition_value']
        operator = rule['condition_operator']
        
        # Convert values to appropriate types for comparison
        if operator in ['>', '<', '>=', '<=']:
            field_value = float(field_value) if field_value else 0
            condition_value = float(condition_value)
        
        # Evaluate condition
        if operator == '==':
            return str(field_value).lower() == str(condition_value).lower()
        elif operator == '!=':
            return str(field_value).lower() != str(condition_value).lower()
        elif operator == 'contains':
            return str(condition_value).lower() in str(field_value).lower()
        elif operator == 'not_contains':
            return str(condition_value).lower() not in str(field_value).lower()
        elif operator == '>':
            return field_value > condition_value
        elif operator == '<':
            return field_value < condition_value
        elif operator == '>=':
            return field_value >= condition_value
        elif operator == '<=':
            return field_value <= condition_value
        
        return False
    except Exception as e:
        logger.error(f"Error evaluating alert rule: {e}")
        return False


# ========================
# ATTACK PATTERN REPORTS
# ========================

@app.route('/api/reports/patterns', methods=['GET'])
def get_patterns_report():
    """Get attack patterns summary"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        hours = request.args.get('hours', default=720, type=int)
        hours = max(1, min(hours, 720))  # 1 to 30 days
        
        patterns = db.get_attack_patterns(hours=hours)
        
        return jsonify({
            'success': True,
            'data': patterns,
            'time_period_hours': hours
        })
    except Exception as e:
        logger.error(f"Error generating patterns report: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/timeline', methods=['GET'])
def get_timeline_report():
    """Get attack timeline with frequency bucketing"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        hours = request.args.get('hours', default=720, type=int)
        bucket_minutes = request.args.get('bucket_minutes', default=60, type=int)
        
        hours = max(1, min(hours, 720))
        bucket_minutes = max(5, min(bucket_minutes, 1440))
        
        timeline = db.get_attack_timeline(hours=hours, bucket_size=bucket_minutes)
        
        return jsonify({
            'success': True,
            'timeline': timeline,
            'time_period_hours': hours,
            'bucket_minutes': bucket_minutes
        })
    except Exception as e:
        logger.error(f"Error generating timeline report: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/daily', methods=['GET'])
def get_daily_report():
    """Get daily attack summary"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        days = request.args.get('days', default=7, type=int)
        days = max(1, min(days, 90))
        
        daily_data = db.get_daily_patterns(days=days)
        hourly_data = db.get_hourly_patterns(hours=720)
        protocols = db.get_protocol_distribution(hours=24*days)
        
        return jsonify({
            'success': True,
            'daily': daily_data,
            'hourly_last_24h': hourly_data,
            'protocols': protocols,
            'days': days
        })
    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/statistics', methods=['GET'])
def get_statistics_report():
    """Get comprehensive statistics report"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        hours = request.args.get('hours', default=720, type=int)
        top_limit = request.args.get('top_limit', default=20, type=int)
        
        hours = max(1, min(hours, 720))
        top_limit = max(5, min(top_limit, 100))
        
        top_ips = db.get_top_attacking_ips(limit=top_limit, hours=hours)
        protocols = db.get_protocol_distribution(hours=hours)
        ports = db.get_port_distribution(hours=hours, limit=top_limit)
        event_types = db.get_event_type_distribution(hours=hours)
        patterns = db.get_attack_patterns(hours=hours)
        
        return jsonify({
            'success': True,
            'summary': patterns,
            'top_ips': top_ips,
            'protocols': protocols,
            'ports': ports,
            'event_types': event_types,
            'time_period_hours': hours
        })
    except Exception as e:
        logger.error(f"Error generating statistics report: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/reports/export', methods=['GET'])
def export_report():
    """Export report as JSON or CSV"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
    
    try:
        report_type = request.args.get('type', 'statistics')  # statistics, daily, timeline
        format_type = request.args.get('format', 'json')  # json, csv
        hours = request.args.get('hours', default=720, type=int)
        
        if report_type == 'statistics':
            data = {
                'summary': db.get_attack_patterns(hours=hours),
                'top_ips': db.get_top_attacking_ips(hours=hours),
                'protocols': db.get_protocol_distribution(hours=hours),
                'ports': db.get_port_distribution(hours=hours),
            }
        elif report_type == 'daily':
            data = {
                'daily': db.get_daily_patterns(days=7),
                'protocols': db.get_protocol_distribution(hours=24*7),
            }
        elif report_type == 'timeline':
            data = {
                'timeline': db.get_attack_timeline(hours=hours),
            }
        else:
            data = {}
        
        if format_type == 'json':
            return jsonify({
                'success': True,
                'report_type': report_type,
                'data': data,
                'exported_at': datetime.now().isoformat()
            })
        elif format_type == 'csv':
            import csv
            from io import StringIO
            
            output = StringIO()
            
            if report_type == 'statistics' and 'top_ips' in data:
                writer = csv.writer(output)
                writer.writerow(['IP Address', 'Attack Count', 'Protocols Used', 'Ports Hit', 
                               'Avg Payload', 'First Attack', 'Last Attack'])
                for ip in data['top_ips']:
                    writer.writerow([
                        ip['source_ip'], ip['attack_count'], ip['protocols_used'],
                        ip['ports_hit'], round(ip['avg_payload'], 2),
                        datetime.fromtimestamp(ip['first_attack']).isoformat(),
                        datetime.fromtimestamp(ip['last_attack']).isoformat()
                    ])
            elif report_type == 'daily' and 'daily' in data:
                writer = csv.writer(output)
                writer.writerow(['Date', 'Event Count', 'Unique IPs', 'Avg Payload'])
                for day in data['daily']:
                    writer.writerow([day['day'], day['event_count'], day['unique_ips'],
                                   round(day['avg_payload'], 2) if day['avg_payload'] else 0])
            
            return Response(
                output.getvalue(),
                mimetype='text/csv',
                headers={'Content-Disposition': f'attachment; filename=report_{report_type}.csv'}
            )
        else:
            return jsonify({"error": "Unsupported format"}), 400
        
    except Exception as e:
        logger.error(f"Error exporting report: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# REAL-TIME LOG VIEWER
# ========================

@app.route('/api/logs/recent', methods=['GET'])
def get_recent_logs():
    """Get recent attack events with pagination and filtering for real-time viewer"""
    try:
        limit = min(int(request.args.get('limit', 50)), 500)
        offset = int(request.args.get('offset', 0))
        source_ip = request.args.get('source_ip')
        protocol = request.args.get('protocol')
        port = request.args.get('port', type=int)
        last_timestamp = request.args.get('last_timestamp', type=float)
        
        # Using global db instead of creating new connection
        events, total = db.get_recent_events_paginated(
            limit=limit,
            offset=offset,
            source_ip=source_ip,
            protocol=protocol,
            port=port,
            last_timestamp=last_timestamp
        )
        
        return jsonify({
            'success': True,
            'events': events,
            'total': total,
            'limit': limit,
            'offset': offset,
            'has_more': (offset + limit) < total
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching recent logs: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs/stream', methods=['GET'])
def stream_live_events():
    """Get live event stream (for real-time updates)"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
        
    try:
        since_timestamp = request.args.get('since', type=float)
        limit = min(int(request.args.get('limit', 20)), 100)
        
        events = db.get_live_event_stream(
            since_timestamp=since_timestamp,
            limit=limit
        )
        
        return jsonify({
            'success': True,
            'events': events,
            'count': len(events),
            'latest_timestamp': events[-1]['timestamp'] if events else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error streaming live events: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/logs/filters', methods=['GET'])
def get_log_filters():
    """Get available filters for log viewer (unique values)"""
    try:
        # Using global db instead of creating new connection
        cursor = db.conn.cursor()
        
        # Get unique protocols
        cursor.execute("SELECT DISTINCT protocol FROM events ORDER BY protocol")
        protocols = [row[0] for row in cursor.fetchall()]
        
        # Get unique ports (most recent ones)
        cursor.execute("""
            SELECT port
            FROM events
            GROUP BY port
            ORDER BY MAX(timestamp) DESC
            LIMIT 100
        """)
        ports = [row[0] for row in cursor.fetchall()]
        
        # Get unique event types
        cursor.execute("SELECT DISTINCT event_type FROM events ORDER BY event_type")
        event_types = [row[0] for row in cursor.fetchall()]
        
        
        return jsonify({
            'success': True,
            'protocols': protocols,
            'ports': sorted(ports),
            'event_types': event_types
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching log filters: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# ML ANOMALY DETECTION
# ========================

@app.route('/api/anomalies/detect', methods=['GET'])
def detect_anomalies():
    """Detect anomalous events using statistical analysis"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
        
    try:
        hours = min(int(request.args.get('hours', 720)), 720)
        sensitivity = float(request.args.get('sensitivity', 2.0))
        
        # Clamp sensitivity to reasonable range
        sensitivity = max(1.0, min(sensitivity, 5.0))
        
        anomalies = db.detect_anomalies(hours=hours, sensitivity=sensitivity)
        baseline = db.get_anomaly_baseline(hours=hours)
        
        return jsonify({
            'success': True,
            'anomalies': anomalies,
            'baseline': baseline,
            'sensitivity': sensitivity,
            'hours': hours,
            'total_anomalies': len(anomalies)
        }), 200
        
    except Exception as e:
        logger.error(f"Error detecting anomalies: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/anomalies/profile/<source_ip>', methods=['GET'])
def get_ip_profile(source_ip):
    """Get behavioral profile and anomaly analysis for a specific IP"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
        
    try:
        hours = min(int(request.args.get('hours', 720)), 720)
        
        profile = db.get_ip_behavior_profile(source_ip, hours=hours)
        
        if not profile:
            return jsonify({'error': 'IP not found in database'}), 404
        
        # Calculate anomaly indicators based on profile
        profile['is_anomalous'] = (
            profile['events_per_minute'] > 10 or  # Very high rate
            profile['protocol_count'] > 3 or  # Multi-protocol
            profile['port_count'] > 10  # Scanning many ports
        )
        
        return jsonify({
            'success': True,
            'profile': profile
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching IP profile: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/anomalies/ml-score', methods=['POST'])
def get_ml_anomaly_score():
    """Get ML-based anomaly score for an attack pattern"""
    try:
        from ml.features import FeatureExtractor
        
        data = request.get_json()
        events = data.get('events', [])
        
        if not events:
            return jsonify({'error': 'No events provided'}), 400
        
        # Extract features
        extractor = FeatureExtractor()
        features = extractor.extract_from_events(events)
        
        # Get ML model predictions
        model = get_model()
        attack_type, confidence = model.predict(
            list(features.values())
        )
        
        return jsonify({
            'success': True,
            'attack_type': attack_type,
            'confidence': confidence,
            'features': features,
            'feature_importance': model.get_feature_importance()
        }), 200
        
    except Exception as e:
        logger.error(f"Error scoring with ML model: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/anomalies/summary', methods=['GET'])
def get_anomaly_summary():
    """Get summary of anomaly detection status"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
        
    try:
        hours = min(int(request.args.get('hours', 720)), 720)
        
        anomalies = db.detect_anomalies(hours=hours, sensitivity=2.0)
        baseline = db.get_anomaly_baseline(hours=hours)
        
        # Count anomaly types
        anomaly_types = {}
        for anomaly in anomalies:
            atype = anomaly.get('anomaly_type', 'unknown')
            anomaly_types[atype] = anomaly_types.get(atype, 0) + 1
        
        # Get top anomalous IPs
        cursor = db.conn.cursor()
        start_time = time.time() - (hours * 3600)
        cursor.execute("""
            SELECT source_ip, COUNT(*) as count
            FROM events
            WHERE timestamp > ?
            GROUP BY source_ip
            ORDER BY count DESC
            LIMIT 10
        """, (start_time,))
        
        top_ips = [{'ip': row[0], 'events': row[1]} for row in cursor.fetchall()]
        
        return jsonify({
            'success': True,
            'total_anomalies': len(anomalies),
            'anomaly_types': anomaly_types,
            'baseline': baseline,
            'top_anomalous_ips': top_ips,
            'severity': 'high' if len(anomalies) > baseline['unique_ips'] else 'medium' if len(anomalies) > 10 else 'low'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting anomaly summary: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# GEOGRAPHIC HEAT MAP
# ========================

@app.route('/api/geo/locations', methods=['GET'])
def get_geographic_locations():
    """Get attack locations with geolocation data"""
    try:
        hours = min(int(request.args.get('hours', 720)), 720)
        limit = min(int(request.args.get('limit', 50)), 500)
        
        # Using global db instead of creating new connection
        locations = db.get_hotspot_locations(limit=limit, hours=hours)
        geo_service = get_geolocation_service()
        
        # Create event loop for async geo calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Enrich with geolocation data
        enriched_locations = []
        for loc in locations:
            ip = loc['source_ip']
            geo = loop.run_until_complete(geo_service.get_geolocation(ip)) if geo_service else None
            
            enriched_locations.append({
                'source_ip': ip,
                'event_count': loc['event_count'],
                'total_payload': loc['total_payload'],
                'severity': loc['severity'],
                'country': geo.get('country', 'Unknown') if geo else 'Unknown',
                'region': geo.get('region', 'Unknown') if geo else 'Unknown',
                'city': geo.get('city', 'Unknown') if geo else 'Unknown',
                'latitude': float(geo.get('latitude', 0)) if geo and geo.get('latitude') else 0,
                'longitude': float(geo.get('longitude', 0)) if geo and geo.get('longitude') else 0,
                'isp': geo.get('isp', 'Unknown') if geo else 'Unknown'
            })
        
        loop.close()
        
        return jsonify({
            'success': True,
            'locations': enriched_locations,
            'total': len(enriched_locations),
            'hours': hours
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching geographic locations: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/geo/heatmap', methods=['GET'])
def get_heatmap_data():
    """Get heatmap data for map visualization"""
    try:
        hours = min(int(request.args.get('hours', 720)), 720)
        
        # Using global db instead of creating new connection
        locations = db.get_hotspot_locations(limit=100, hours=hours)
        geo_service = get_geolocation_service()
        
        # Create event loop for async geo calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Convert to heatmap format (latitude, longitude, intensity)
        heatmap_data = []
        for loc in locations:
            ip = loc['source_ip']
            geo = loop.run_until_complete(geo_service.get_geolocation(ip)) if geo_service else None
            
            if geo and geo.get('latitude') and geo.get('longitude'):
                # Intensity based on event count (0-1.0)
                intensity = min(loc['event_count'] / 1000, 1.0)
                
                heatmap_data.append({
                    'lat': float(geo['latitude']),
                    'lng': float(geo['longitude']),
                    'intensity': intensity,
                    'events': loc['event_count'],
                    'country': geo.get('country', 'Unknown')
                })
        
        loop.close()
        
        return jsonify({
            'success': True,
            'heatmap': heatmap_data,
            'count': len(heatmap_data),
            'hours': hours
        }), 200
        
    except Exception as e:
        logger.error(f"Error generating heatmap data: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/geo/countries', methods=['GET'])
def get_country_statistics():
    """Get attack statistics aggregated by country"""
    try:
        hours = min(int(request.args.get('hours', 720)), 720)
        
        # Using global db instead of creating new connection
        ip_stats = db.get_country_stats(hours=hours)
        geo_service = get_geolocation_service()
        
        # Create event loop for async geo calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Aggregate by country
        country_stats = {}
        for ip_stat in ip_stats:
            ip = ip_stat['source_ip']
            geo = loop.run_until_complete(geo_service.get_geolocation(ip)) if geo_service else None
            country = geo.get('country', 'Unknown') if geo else 'Unknown'
            
            if country not in country_stats:
                country_stats[country] = {
                    'country': country,
                    'event_count': 0,
                    'unique_ips': 0,
                    'avg_events_per_ip': 0
                }
            
            country_stats[country]['event_count'] += ip_stat['event_count']
            country_stats[country]['unique_ips'] += 1
        
        # Calculate averages
        for country in country_stats:
            if country_stats[country]['unique_ips'] > 0:
                country_stats[country]['avg_events_per_ip'] = (
                    country_stats[country]['event_count'] / country_stats[country]['unique_ips']
                )
        
        # Sort by event count
        sorted_countries = sorted(
            country_stats.values(), 
            key=lambda x: x['event_count'], 
            reverse=True
        )
        
        loop.close()
        
        return jsonify({
            'success': True,
            'countries': sorted_countries[:100],  # Top 100 countries
            'total_countries': len(sorted_countries),
            'hours': hours
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching country statistics: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/geo/country/<country>', methods=['GET'])
def get_country_details(country):
    """Get details for a specific country"""
    try:
        hours = min(int(request.args.get('hours', 720)), 720)
        
        # Using global db instead of creating new connection
        ip_stats = db.get_country_stats(hours=hours)
        geo_service = get_geolocation_service()
        
        # Create event loop for async geo calls
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        country_ips = []
        for ip_stat in ip_stats:
            ip = ip_stat['source_ip']
            geo = loop.run_until_complete(geo_service.get_geolocation(ip)) if geo_service else None
            if geo and geo.get('country') == country:
                country_ips.append({
                    'source_ip': ip,
                    'event_count': ip_stat['event_count'],
                    'city': geo.get('city', 'Unknown'),
                    'region': geo.get('region', 'Unknown'),
                    'isp': geo.get('isp', 'Unknown')
                })
        
        
        # Sort by event count
        country_ips.sort(key=lambda x: x['event_count'], reverse=True)
        
        loop.close()
        
        return jsonify({
            'success': True,
            'country': country,
            'ips': country_ips[:100],  # Top 100 IPs
            'total_ips': len(country_ips),
            'total_events': sum(ip['event_count'] for ip in country_ips),
            'hours': hours
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching country details: {e}")
        return jsonify({"error": str(e)}), 500


# ========================
# THREAT INTELLIGENCE
# ========================

def calculate_threat_score(ip_info: Dict) -> tuple:
    """Calculate threat score based on IP characteristics"""
    score = 0
    threat_type = 'normal'
    
    # Check for proxy/VPN
    if ip_info.get('proxy') or ip_info.get('vpn'):
        score += 3
        threat_type = 'anonymization'
    
    # Check for data center
    if ip_info.get('hosting'):
        score += 2
        threat_type = 'datacenter'
    
    # Regional risks (simplified)
    country = ip_info.get('country', '').upper()
    high_risk_countries = ['CN', 'RU', 'KP', 'IR']
    if country in high_risk_countries:
        score += 2
    
    # Calculate based on attack frequency if available
    # This is done in the enrichment layer
    
    return min(score, 10.0), threat_type


@app.route('/api/threat/score/<source_ip>', methods=['GET'])
def get_threat_score(source_ip):
    """Get threat intelligence score for an IP"""
    try:
        # Using global db instead of creating new connection
        
        # Check if we have cached threat data
        threat_intel = db.get_threat_intelligence(source_ip)
        if threat_intel:
            return jsonify({
                'success': True,
                'source_ip': source_ip,
                'threat_intel': threat_intel,
                'from_cache': True
            }), 200
        
        # Get geolocation
        geo_data = None
        geo_service = get_geolocation_service()
        if geo_service:
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                geo_data = loop.run_until_complete(geo_service.get_geolocation(source_ip))
                loop.close()
            except Exception as e:
                logger.warning(f"Geolocation fetch failed for {source_ip}: {e}")
        
        # Calculate threat score
        threat_score, threat_type = calculate_threat_score(geo_data or {})
        
        # Get attack stats
        profile = db.get_ip_behavior_profile(source_ip, hours=7*24)  # 7 days
        
        # Calculate additional risk based on behavior
        if profile:
            if profile['events_per_minute'] > 100:
                threat_score += 3
                threat_type = 'high_frequency_attack'
            elif profile['protocol_count'] > 3:
                threat_score += 2
                threat_type = 'multi_protocol_attack'
            elif profile['port_count'] > 10:
                threat_score += 2
                threat_type = 'port_scanning'
        
        # Cap at 10
        threat_score = min(threat_score, 10.0)
        
        # Store in threat intelligence table
        threat_data = {
            'risk_score': threat_score,
            'threat_type': threat_type,
            'is_vpn': geo_data.get('proxy', False) if geo_data else False,
            'is_proxy': geo_data.get('vpn', False) if geo_data else False,
            'is_datacenter': geo_data.get('hosting', False) if geo_data else False,
            'description': f'{threat_type}: Risk Score {threat_score:.1f}/10'
        }
        db.add_threat_intelligence(source_ip, threat_data)
        db.close()
        
        return jsonify({
            'success': True,
            'source_ip': source_ip,
            'threat_score': threat_score,
            'threat_type': threat_type,
            'geolocation': geo_data,
            'behavior': {
                'events': profile['event_count'] if profile else 0,
                'protocols': profile['protocol_count'] if profile else 0,
                'ports': profile['port_count'] if profile else 0,
                'rate': profile['events_per_minute'] if profile else 0
            } if profile else None
        }), 200
        
    except Exception as e:
        logger.error(f"Error calculating threat score: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/threat/high-risk', methods=['GET'])
def get_high_risk_ips():
    """Get IPs flagged as high risk"""
    try:
        threshold = float(request.args.get('threshold', 7.0))
        limit = min(int(request.args.get('limit', 50)), 200)
        
        # Using global db instead of creating new connection
        high_risk = db.get_high_risk_ips(threshold=threshold, limit=limit)
        
        return jsonify({
            'success': True,
            'high_risk_ips': high_risk,
            'count': len(high_risk),
            'threshold': threshold
        }), 200
        
    except Exception as e:
        logger.error(f"Error fetching high-risk IPs: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/threat/summary', methods=['GET'])
def get_threat_summary():
    """Get summary of threat landscape"""
    if not db:
        return jsonify({"error": "Database not initialized"}), 500
        
    try:
        # Get high-risk IPs count
        high_risk = db.get_high_risk_ips(threshold=7.0, limit=10000)
        
        # Count by threat type
        threat_types = {}
        for ip_threat in high_risk:
            threat_type = ip_threat.get('threat_type', 'unknown')
            threat_types[threat_type] = threat_types.get(threat_type, 0) + 1
        
        # Get score distribution
        score_distribution = {
            'critical': len([t for t in high_risk if t.get('risk_score', 0) >= 9]),
            'high': len([t for t in high_risk if 7 <= t.get('risk_score', 0) < 9]),
            'medium': len([t for t in high_risk if 4 <= t.get('risk_score', 0) < 7]),
            'low': len([t for t in high_risk if t.get('risk_score', 0) < 4])
        }
        
        return jsonify({
            'success': True,
            'high_risk_count': len(high_risk),
            'threat_types': threat_types,
            'score_distribution': score_distribution,
            'overall_threat_level': 'critical' if score_distribution['critical'] > 5 else 
                                   'high' if score_distribution['high'] > 10 else
                                   'medium'
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting threat summary: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/threat/bulk-scan', methods=['POST'])
def bulk_scan_threats():
    """Scan multiple IPs for threats"""
    try:
        data = request.get_json()
        ips = data.get('ips', [])[:100]  # Limit to 100
        
        if not ips:
            return jsonify({'error': 'No IPs provided'}), 400
        
        # Using global db instead of creating new connection
        results = []
        geo_service = get_geolocation_service()
        
        for ip in ips:
            threat_intel = db.get_threat_intelligence(ip)
            if threat_intel:
                results.append(threat_intel)
            else:
                # Quick threat assessment with async handling
                geo_data = None
                if geo_service:
                    try:
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        geo_data = loop.run_until_complete(geo_service.get_geolocation(ip))
                        loop.close()
                    except Exception as e:
                        logger.warning(f"Geolocation fetch failed for {ip}: {e}")
                
                score, threat_type = calculate_threat_score(geo_data or {})
                results.append({
                    'source_ip': ip,
                    'risk_score': score,
                    'threat_type': threat_type
                })
        
        
        return jsonify({
            'success': True,
            'scanned': len(results),
            'results': results
        }), 200
        
    except Exception as e:
        logger.error(f"Error in bulk threat scan: {e}")
        return jsonify({"error": str(e)}), 500


# ========== AUTOMATED RESPONSE ACTIONS - FEATURE #8 ==========

@app.route('/api/response/block-ip', methods=['POST'])
def block_ip_endpoint():
    """Block an IP address"""
    try:
        data = request.get_json()
        source_ip = data.get('ip')
        reason = data.get('reason', 'Automated threat response')
        threat_type = data.get('threat_type', '')
        risk_score = data.get('risk_score', 0)
        permanent = data.get('permanent', True)
        expires_in_hours = data.get('expires_in_hours', 24)
        
        if not source_ip:
            return jsonify({'error': 'IP address required'}), 400
        
        # Using global db instead of creating new connection
        success = db.block_ip(source_ip, reason, threat_type, risk_score, permanent, expires_in_hours)
        
        return jsonify({
            'success': success,
            'ip': source_ip,
            'status': 'blocked' if success else 'failed',
            'reason': reason
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error blocking IP: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/response/unblock-ip', methods=['POST'])
def unblock_ip_endpoint():
    """Unblock an IP address"""
    try:
        data = request.get_json()
        source_ip = data.get('ip')
        
        if not source_ip:
            return jsonify({'error': 'IP address required'}), 400
        
        # Using global db instead of creating new connection
        success = db.unblock_ip(source_ip)
        
        return jsonify({
            'success': success,
            'ip': source_ip,
            'status': 'unblocked' if success else 'failed'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error unblocking IP: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/response/blocked-ips', methods=['GET'])
def get_blocked_ips_endpoint():
    """Get list of blocked IPs"""
    try:
        limit = request.args.get('limit', 100, type=int)
        
        # Using global db instead of creating new connection
        blocked_ips = db.get_blocked_ips(limit)
        
        return jsonify({
            'success': True,
            'count': len(blocked_ips),
            'blocked_ips': blocked_ips
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving blocked IPs: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/response/webhook/add', methods=['POST'])
def add_webhook_endpoint():
    """Add a webhook for automated notifications"""
    try:
        data = request.get_json()
        url = data.get('url')
        event_type = data.get('event_type', 'all_threats')
        
        if not url:
            return jsonify({'error': 'Webhook URL required'}), 400
        
        # Using global db instead of creating new connection
        success = db.add_webhook(url, event_type)
        
        return jsonify({
            'success': success,
            'url': url,
            'event_type': event_type,
            'status': 'added' if success else 'failed'
        }), 200 if success else 500
        
    except Exception as e:
        logger.error(f"Error adding webhook: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/response/webhooks', methods=['GET'])
def get_webhooks_endpoint():
    """Get configured webhooks"""
    try:
        active_only = request.args.get('active_only', True, type=bool)
        
        # Using global db instead of creating new connection
        webhooks = db.get_webhooks(active_only)
        
        return jsonify({
            'success': True,
            'count': len(webhooks),
            'webhooks': webhooks
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving webhooks: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/response/actions', methods=['GET'])
def get_response_actions_endpoint():
    """Get automated response actions summary"""
    try:
        # Using global db instead of creating new connection
        
        # Get statistics
        blocked_ips = db.get_blocked_ips()
        webhooks = db.get_webhooks()
        action_log = db.get_action_log(limit=10)
        
        # Count actions by type
        action_counts = {}
        for action in action_log:
            action_type = action.get('action_type', 'unknown')
            action_counts[action_type] = action_counts.get(action_type, 0) + 1
        
        
        return jsonify({
            'success': True,
            'blocked_ips_count': len(blocked_ips),
            'active_webhooks': len([w for w in webhooks if w.get('is_active')]),
            'total_webhooks': len(webhooks),
            'action_counts': action_counts,
            'recent_actions': [dict(a) for a in action_log[:5]]
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving response actions: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/response/action-log', methods=['GET'])
def get_action_log_endpoint():
    """Get action logs"""
    try:
        limit = request.args.get('limit', 50, type=int)
        action_type = request.args.get('action_type', '')
        
        # Using global db instead of creating new connection
        action_log = db.get_action_log(limit, action_type)
        
        return jsonify({
            'success': True,
            'count': len(action_log),
            'actions': [dict(a) for a in action_log]
        }), 200
        
    except Exception as e:
        logger.error(f"Error retrieving action log: {e}")
        return jsonify({"error": str(e)}), 500


# ========== API MANAGEMENT ENDPOINTS - FEATURE #10 ==========

@app.route('/api/auth/keys', methods=['GET'])
def list_api_keys():
    """List all API keys (requires admin permission)"""
    try:
        api_key = request.headers.get('X-API-Key')
        if not api_key:
            return jsonify({'error': 'Admin API key required'}), 401
        
        key_data = APIKeyAuth.validate_key(api_key)
        if not key_data or 'admin' not in key_data.get('permissions', []):
            return jsonify({'error': 'Admin permission required'}), 403
        
        # Return key list (without exposing full keys)
        keys_info = []
        for key, data in APIKeyAuth.API_KEYS.items():
            keys_info.append({
                'key': key[:10] + '...',
                'name': data.get('name'),
                'permissions': data.get('permissions'),
                'active': data.get('active'),
                'created_at': data.get('created_at').isoformat() if data.get('created_at') else None
            })
        
        return jsonify({
            'success': True,
            'count': len(keys_info),
            'keys': keys_info
        }), 200
        
    except Exception as e:
        logger.error(f"Error listing API keys: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/keys/create', methods=['POST'])
def create_api_key():
    """Create a new API key (requires admin permission)"""
    try:
        data = request.get_json()
        api_key = request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({'error': 'Admin API key required'}), 401
        
        key_data = APIKeyAuth.validate_key(api_key)
        if not key_data or 'admin' not in key_data.get('permissions', []):
            return jsonify({'error': 'Admin permission required'}), 403
        
        # Create new key
        name = data.get('name', 'Unnamed Key')
        permissions = data.get('permissions', ['read'])
        
        new_key = APIKeyAuth.get_or_create_key(name, permissions)
        
        return jsonify({
            'success': True,
            'key': new_key,
            'name': name,
            'permissions': permissions
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/auth/keys/<key_prefix>/revoke', methods=['POST'])
def revoke_api_key(key_prefix):
    """Revoke an API key (requires admin permission)"""
    try:
        admin_key = request.headers.get('X-API-Key')
        
        if not admin_key:
            return jsonify({'error': 'Admin API key required'}), 401
        
        key_data = APIKeyAuth.validate_key(admin_key)
        if not key_data or 'admin' not in key_data.get('permissions', []):
            return jsonify({'error': 'Admin permission required'}), 403
        
        # Find and revoke key
        from app.api_auth import API_KEYS
        for key in API_KEYS.keys():
            if key.startswith(key_prefix):
                success = APIKeyAuth.revoke_key(key)
                return jsonify({
                    'success': success,
                    'message': 'Key revoked' if success else 'Key not found'
                }), 200
        
        return jsonify({'error': 'Key not found'}), 404
        
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/status/health', methods=['GET'])
@APIRateLimiter(calls=100, period=60)
def health_check():
    """Health check endpoint (no auth required, rate limited)"""
    try:
        # Using global db instead of creating new connection
        
        # Check database connectivity
        cursor = db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM events")
        event_count = cursor.fetchone()[0]
        
        
        return jsonify({
            'status': 'healthy',
            'timestamp': __import__('datetime').datetime.now().isoformat(),
            'database': 'connected',
            'event_count': event_count
        }), 200
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'degraded',
            'error': str(e)
        }), 503


@app.route('/api/status/rate-limits', methods=['GET'])
def get_rate_limit_status():
    """Get current rate limit status and usage"""
    try:
        now = time.time()
        
        # Get current IP
        client_ip = _client_ip()
        
        # Rate limiter info
        rate_limit_info = {
            'limit': RATE_LIMIT_MAX,
            'window_seconds': RATE_LIMIT_WINDOW,
            'blacklist_duration': RATE_LIMIT_BLACKLIST,
            'current_ip': client_ip,
            'is_whitelisted': client_ip in RATE_LIMIT_WHITELIST,
            'is_blacklisted': _rate_limiter.is_blacklisted(client_ip),
        }
        
        # Get events for current IP
        if client_ip in _rate_limiter.events:
            events = list(_rate_limiter.events[client_ip])
            # Count events in current window
            valid_events = [e for e in events if now - e <= RATE_LIMIT_WINDOW]
            rate_limit_info['current_usage'] = len(valid_events)
            rate_limit_info['usage_percentage'] = (len(valid_events) / RATE_LIMIT_MAX * 100) if RATE_LIMIT_MAX > 0 else 0
        else:
            rate_limit_info['current_usage'] = 0
            rate_limit_info['usage_percentage'] = 0
        
        # Get blacklist info
        rate_limit_info['blacklist_count'] = len(_rate_limiter.blacklist)
        rate_limit_info['blacklist_entries'] = []
        
        for ip, until_time in list(_rate_limiter.blacklist.items()):
            remaining = until_time - now
            if remaining > 0:
                rate_limit_info['blacklist_entries'].append({
                    'ip': ip,
                    'remaining_seconds': int(remaining),
                    'expires_at': __import__('datetime').datetime.fromtimestamp(until_time).isoformat()
                })
        
        # Get top IPs by event count
        top_ips = []
        for ip, events_deque in list(_rate_limiter.events.items()):
            if len(events_deque) > 0:
                top_ips.append({
                    'ip': ip,
                    'event_count': len(events_deque),
                    'is_blacklisted': _rate_limiter.is_blacklisted(ip)
                })
        
        top_ips.sort(key=lambda x: x['event_count'], reverse=True)
        rate_limit_info['top_ips'] = top_ips[:10]  # Top 10 IPs
        
        return jsonify({
            'success': True,
            'rate_limits': rate_limit_info,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/performance/metrics', methods=['GET'])
def get_performance_metrics():
    """Get performance metrics for the dashboard"""
    try:
        perf_monitor = get_performance_monitor()
        
        # Get summary metrics
        metrics = perf_monitor.get_metrics_summary()
        
        # Get response time history
        response_history = perf_monitor.get_response_time_history(limit=50)
        
        return jsonify({
            'success': True,
            'metrics': metrics,
            'response_time_history': response_history,
            'timestamp': time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/status/stats', methods=['GET'])
@APIRateLimiter(calls=50, period=60)
@require_api_key(permission='read')
def api_stats():
    """Get API statistics and usage (requires read permission)"""
    try:
        from app.api_auth import get_api_stats
        
        stats = get_api_stats()
        
        return jsonify({
            'success': True,
            'stats': stats,
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting API stats: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/threat-intel/<ip>', methods=['GET'])
def get_threat_intel(ip):
    """Get threat intelligence profile for an IP"""
    try:
        from telemetry.threat_intelligence import get_threat_profile
        import re
        
        # Validate IP format
        if not re.match(r'^(\d{1,3}\.){3}\d{1,3}$', ip):
            return jsonify({
                'success': False,
                'error': 'Invalid IP address format'
            }), 400
        
        # Get attack profile from database
        db = get_database()
        ip_profile = db.get_profile(ip)
        
        attack_profile = {}
        if ip_profile:
            attack_profile = {
                'total_events': ip_profile.get('total_events', 0),
                'events_per_minute': ip_profile.get('events_per_minute', 0),
                'protocols_used': set(ip_profile.get('protocols_used', '').split(',')),
                'avg_payload_size': ip_profile.get('avg_payload_size', 0),
                'attack_type': ip_profile.get('attack_type', 'unknown'),
                'country': ip_profile.get('country', 'XX')
            }
        
        # Get threat profile
        threat_profile = get_threat_profile(ip, attack_profile)
        
        # Store in database
        try:
            db.store_reputation(
                ip,
                threat_profile['reputation_score'],
                threat_profile['threat_level'],
                threat_profile.get('indicators'),
                bool(threat_profile['botnet_analysis']),
                threat_profile['botnet_analysis'].get('botnet_family') if threat_profile['botnet_analysis'] else None
            )
        except Exception as e:
            logger.warning(f"Could not store reputation: {e}")
        
        return jsonify({
            'success': True,
            'threat_profile': threat_profile,
            'timestamp': time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting threat intelligence: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/threat-intel/top-threats', methods=['GET'])
def get_top_threats():
    """Get top threat IPs from the database"""
    try:
        db = get_database()
        limit = request.args.get('limit', 20, type=int)
        
        # Get high reputation IPs
        threats = db.get_high_reputation_ips(threshold=60, limit=limit)
        
        return jsonify({
            'success': True,
            'threats': threats,
            'timestamp': time.time()
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting top threats: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.before_request
def before_request():
    """Before each request - for cleanup and logging"""
    # Log API requests
    if request.path.startswith('/api/'):
        client = g.get('api_key', request.remote_addr)
        logger.debug(f"API request: {request.method} {request.path} from {client[:20]}...")


@app.after_request
def after_request(response):
    """After each request - add rate limit headers"""
    # Add rate limit headers to response
    response = add_rate_limit_headers(response)
    return response


# ============= Configuration Management (Feature #11) =============

@app.route('/api/config/honeypot', methods=['GET'])
@APIRateLimiter(calls=50, period=60)
@require_api_key(permission='read')
def api_get_honeypot_config():
    """Get honeypot configuration"""
    try:
        # Using global db instead of creating new connection
        config = db.get_all_config(category='honeypot')
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting honeypot config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/honeypot', methods=['POST'])
@APIRateLimiter(calls=10, period=60)
@require_api_key(permission='write')
def api_update_honeypot_config():
    """Update honeypot configuration"""
    try:
        data = request.get_json() or {}
        # Using global db instead of creating new connection
        
        # Update configuration values
        for key, value in data.items():
            if key.startswith('honeypot_'):
                db.set_config(key, str(value), config_type='string', category='honeypot')
        
        # Log action
        db.log_action(
            action_type='config_update', details=f'Updated honeypot config: {list(data.keys())}'
        )
        
        
        return jsonify({
            'success': True,
            'message': 'Honeypot configuration updated',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error updating honeypot config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/alerts', methods=['GET'])
@APIRateLimiter(calls=50, period=60)
@require_api_key(permission='read')
def api_get_alert_config():
    """Get alert configuration"""
    try:
        # Using global db instead of creating new connection
        config = db.get_all_config(category='alert')
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting alert config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/alerts', methods=['POST'])
@APIRateLimiter(calls=10, period=60)
@require_api_key(permission='write')
def api_update_alert_config():
    """Update alert configuration"""
    try:
        data = request.get_json() or {}
        # Using global db instead of creating new connection
        
        # Update configuration values
        for key, value in data.items():
            if key.startswith('alert_'):
                db.set_config(key, str(value), config_type='string', category='alert')
        
        # Log action
        db.log_action(
            action_type='config_update', details=f'Updated alert config: {list(data.keys())}'
        )
        
        
        return jsonify({
            'success': True,
            'message': 'Alert configuration updated',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error updating alert config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/responses', methods=['GET'])
@APIRateLimiter(calls=50, period=60)
@require_api_key(permission='read')
def api_get_response_config():
    """Get response actions configuration"""
    try:
        # Using global db instead of creating new connection
        config = db.get_all_config(category='response')
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting response config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/responses', methods=['POST'])
@APIRateLimiter(calls=10, period=60)
@require_api_key(permission='write')
def api_update_response_config():
    """Update response actions configuration"""
    try:
        data = request.get_json() or {}
        # Using global db instead of creating new connection
        
        # Update configuration values
        for key, value in data.items():
            if key.startswith('response_'):
                db.set_config(key, str(value), config_type='string', category='response')
        
        # Log action
        db.log_action(
            action_type='config_update', details=f'Updated response config: {list(data.keys())}'
        )
        
        
        return jsonify({
            'success': True,
            'message': 'Response configuration updated',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error updating response config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/ui', methods=['GET'])
@APIRateLimiter(calls=50, period=60)
def api_get_ui_config():
    """Get UI preferences (no auth required)"""
    try:
        # Using global db instead of creating new connection
        config = db.get_all_config(category='ui')
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting UI config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/ui', methods=['POST'])
@APIRateLimiter(calls=10, period=60)
@require_api_key(permission='write')
def api_update_ui_config():
    """Update UI preferences"""
    try:
        data = request.get_json() or {}
        # Using global db instead of creating new connection
        
        # Update configuration values
        for key, value in data.items():
            if key.startswith('ui_'):
                db.set_config(key, str(value), config_type='string', category='ui')
        
        # Log action
        db.log_action(
            action_type='config_update', details=f'Updated UI config: {list(data.keys())}'
        )
        
        
        return jsonify({
            'success': True,
            'message': 'UI configuration updated',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error updating UI config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/system', methods=['GET'])
@APIRateLimiter(calls=50, period=60)
@require_api_key(permission='read')
def api_get_system_config():
    """Get system configuration"""
    try:
        # Using global db instead of creating new connection
        config = db.get_all_config(category='system')
        
        return jsonify({
            'success': True,
            'config': config,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error getting system config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/system', methods=['POST'])
@APIRateLimiter(calls=10, period=60)
@require_api_key(permission='admin')
def api_update_system_config():
    """Update system configuration (admin only)"""
    try:
        data = request.get_json() or {}
        # Using global db instead of creating new connection
        
        # Update configuration values
        for key, value in data.items():
            if key.startswith('system_'):
                db.set_config(key, str(value), config_type='string', category='system')
        
        # Log action
        db.log_action(
            action_type='config_update', details=f'Updated system config: {list(data.keys())}'
        )
        
        
        return jsonify({
            'success': True,
            'message': 'System configuration updated',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error updating system config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/test/email', methods=['POST'])
@APIRateLimiter(calls=5, period=60)
@require_api_key(permission='admin')
def api_test_email_config():
    """Test email configuration"""
    try:
        data = request.get_json() or {}
        
        # In production, would actually send test email
        # For now, just validate configuration
        smtp_server = data.get('smtp_server')
        smtp_port = data.get('smtp_port', 587)
        test_email = data.get('test_email')
        
        if not smtp_server or not test_email:
            return jsonify({
                'success': False,
                'error': 'Missing smtp_server or test_email'
            }), 400
        
        logger.info(f"Email test: Would send to {test_email} via {smtp_server}:{smtp_port}")
        
        return jsonify({
            'success': True,
            'message': 'Email test would be sent (feature not fully implemented)',
            'test_recipient': test_email,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error testing email config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/test/webhook', methods=['POST'])
@APIRateLimiter(calls=5, period=60)
@require_api_key(permission='write')
def api_test_webhook_config():
    """Test webhook configuration"""
    try:
        data = request.get_json() or {}
        webhook_url = data.get('webhook_url')
        
        if not webhook_url:
            return jsonify({
                'success': False,
                'error': 'Missing webhook_url'
            }), 400
        
        # In production, would actually send test webhook
        logger.info(f"Webhook test: Would POST to {webhook_url}")
        
        return jsonify({
            'success': True,
            'message': 'Webhook test would be sent',
            'webhook_url': webhook_url,
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error testing webhook config: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/config/restart', methods=['POST'])
@APIRateLimiter(calls=2, period=60)
@require_api_key(permission='admin')
def api_restart_services():
    """Request service restart (admin only)"""
    try:
        # Using global db instead of creating new connection
        
        # Log action
        db.log_action(action_type='service_restart', details='Service restart requested via API')
        
        
        return jsonify({
            'success': True,
            'message': 'Services restart scheduled',
            'note': 'In production, this would restart the honeypot services',
            'timestamp': datetime.now().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Error restarting services: {e}")
        return jsonify({'error': str(e)}), 500


# ========================
# APPLICATION SETUP
# ========================


def create_app():
    """Application factory"""
    init_db()
    logger.info("Dashboard initialized")
    return app


if __name__ == '__main__':
    app = create_app()
    logger.info("Starting dashboard on http://127.0.0.1:5000")
    app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
