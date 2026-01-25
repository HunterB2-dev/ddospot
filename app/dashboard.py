"""
Flask web dashboard for the DDoSPot honeypot.
Provides real-time visualization of attacks and statistics.
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from flask import Response
from core.database import HoneypotDatabase
from core.geolocation import get_geolocation_service
from telemetry.alerts import get_alert_manager
from telemetry.logger import get_logger
from telemetry.prometheus_metrics import get_metrics
from telemetry.ratelimit import RateLimiter
import os
from functools import wraps
from ml.model import get_model
from ml.features import FeatureExtractor
import json
import asyncio
import time
from datetime import datetime, timedelta

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


def init_db():
    """Initialize database connection"""
    global db, geo_service, alert_manager, ml_model, feature_extractor
    db = HoneypotDatabase("honeypot.db")
    geo_service = get_geolocation_service("honeypot.db")
    alert_manager = get_alert_manager("logs/honeypot.db", "config/alert_config.json")
    ml_model = get_model()
    feature_extractor = FeatureExtractor()
    
    # Update initial metrics
    metrics.update_service_status("dashboard", True)
    metrics.update_system_metrics()
    metrics.update_log_metrics()


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
    
    hours = request.args.get('hours', default=24, type=int)
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
    
    minutes = request.args.get('minutes', default=60, type=int)
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
    
    hours = request.args.get('hours', default=24, type=int)
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
    
    events = db.get_recent_events(24, 100000)  # Last 24 hours
    
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

@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('index.html')


@app.route('/profile/<ip>')
def profile_page(ip):
    """Detailed profile page"""
    return render_template('profile.html', ip=ip)


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
