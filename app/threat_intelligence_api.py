"""
Threat Intelligence API
REST endpoints for IP reputation, geolocation, threat feeds, and analysis
"""

from flask import Blueprint, jsonify, request
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Create Blueprint
threat_intelligence_api = Blueprint('threat_intel', __name__, url_prefix='/api/threat-intel')

# Global database and manager references
_db = None
_threat_manager = None

def init_threat_intelligence_api(db):
    """Initialize threat intelligence API with database reference"""
    global _db, _threat_manager
    _db = db
    
    from core.threat_intelligence import get_threat_intelligence_manager
    _threat_manager = get_threat_intelligence_manager()
    
    logger.info("Threat Intelligence API initialized")

# ============================================================================
# IP REPUTATION ENDPOINTS
# ============================================================================

@threat_intelligence_api.route('/reputation/<ip>', methods=['GET'])
def get_ip_reputation(ip):
    """Get IP reputation score"""
    try:
        if not _threat_manager or not _db:
            return jsonify({'error': 'Service not initialized'}), 503
        
        # Check cache first
        cached = _db.get_ip_reputation(ip)
        if cached:
            return jsonify({
                'ip': ip,
                'reputation': cached,
                'source': 'cache',
                'timestamp': datetime.now().isoformat()
            })
        
        # Analyze IP
        analysis = _threat_manager.analyze_ip(ip)
        
        # Cache result
        rep = analysis['reputation']
        _db.cache_ip_reputation(
            ip, 
            rep.get('score', 0),
            rep.get('sources', []),
            rep.get('confidence', 0),
            rep.get('details', {}).get('reports', 0),
            rep.get('details', {}).get('threat_types', [])
        )
        
        return jsonify({
            'ip': ip,
            'reputation': analysis['reputation'],
            'source': 'analysis',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_ip_reputation: {e}")
        return jsonify({'error': str(e)}), 500

@threat_intelligence_api.route('/reputation/<ip>/details', methods=['GET'])
def get_ip_reputation_details(ip):
    """Get detailed IP reputation analysis"""
    try:
        if not _threat_manager:
            return jsonify({'error': 'Service not initialized'}), 503
        
        analysis = _threat_manager.analyze_ip(ip)
        
        return jsonify({
            'ip': ip,
            'reputation': analysis['reputation'],
            'threat_feeds': analysis['threat_feeds'],
            'geolocation': analysis['geolocation'],
            'composite_score': analysis['composite_threat_score'],
            'threat_level': analysis['threat_level'],
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_ip_reputation_details: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# GEOLOCATION ENDPOINTS
# ============================================================================

@threat_intelligence_api.route('/geo/<ip>', methods=['GET'])
def get_geo_data(ip):
    """Get geolocation data for IP"""
    try:
        if not _threat_manager or not _db:
            return jsonify({'error': 'Service not initialized'}), 503
        
        # Check cache first
        cached = _db.get_geolocation(ip)
        if cached:
            return jsonify({
                'ip': ip,
                'geolocation': cached,
                'source': 'cache',
                'timestamp': datetime.now().isoformat()
            })
        
        # Analyze IP
        analysis = _threat_manager.analyze_ip(ip)
        geo = analysis['geolocation']
        
        # Cache result
        _db.cache_geolocation(
            ip,
            geo.get('country', 'UNKNOWN'),
            geo.get('country_name', ''),
            geo.get('city', ''),
            geo.get('isp', ''),
            geo.get('risk_score', 0),
            geo.get('lat', 0.0),
            geo.get('lon', 0.0)
        )
        
        return jsonify({
            'ip': ip,
            'geolocation': geo,
            'source': 'analysis',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_geo_data: {e}")
        return jsonify({'error': str(e)}), 500

@threat_intelligence_api.route('/geo/<ip>/risk', methods=['GET'])
def get_geo_risk(ip):
    """Get geographic risk assessment"""
    try:
        if not _threat_manager:
            return jsonify({'error': 'Service not initialized'}), 503
        
        analysis = _threat_manager.analyze_ip(ip)
        geo = analysis['geolocation']
        
        risk_level = 'UNKNOWN'
        if geo['risk_score'] >= 80:
            risk_level = 'CRITICAL'
        elif geo['risk_score'] >= 60:
            risk_level = 'HIGH'
        elif geo['risk_score'] >= 40:
            risk_level = 'MEDIUM'
        else:
            risk_level = 'LOW'
        
        return jsonify({
            'ip': ip,
            'country': geo.get('country'),
            'risk_score': geo.get('risk_score'),
            'risk_level': risk_level,
            'recommendations': [f"Geographic origin: {geo.get('country_name')}"]
        })
    except Exception as e:
        logger.error(f"Error in get_geo_risk: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# THREAT FEED ENDPOINTS
# ============================================================================

@threat_intelligence_api.route('/feeds/check/<ip>', methods=['GET'])
def check_threat_feeds(ip):
    """Check IP against threat feeds"""
    try:
        if not _threat_manager or not _db:
            return jsonify({'error': 'Service not initialized'}), 503
        
        analysis = _threat_manager.analyze_ip(ip)
        feeds = analysis['threat_feeds']
        
        # Cache feed results
        for feed_name, feed_data in feeds.get('details', {}).items():
            _db.cache_threat_feed(
                ip,
                feed_name,
                feed_data.get('matched', False),
                str(feed_data),
                feed_data.get('confidence', 0)
            )
        
        return jsonify({
            'ip': ip,
            'feeds_checked': feeds.get('total_feeds_checked'),
            'matches': feeds.get('matches'),
            'details': feeds.get('details'),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in check_threat_feeds: {e}")
        return jsonify({'error': str(e)}), 500

@threat_intelligence_api.route('/feeds/list', methods=['GET'])
def list_threat_feeds():
    """List available threat feeds"""
    try:
        if not _threat_manager:
            return jsonify({'error': 'Service not initialized'}), 503
        
        feeds = _threat_manager.threat_feed_manager.feed_sources.keys()
        
        return jsonify({
            'available_feeds': list(feeds),
            'feed_count': len(feeds),
            'feeds': {
                'abuse_ipdb': 'IP Abuse Database',
                'alienVault_otx': 'AlienVault OTX',
                'urlhaus': 'URLhaus Malware',
                'shodan': 'Shodan Honeypot Database',
            }
        })
    except Exception as e:
        logger.error(f"Error in list_threat_feeds: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# TREND & ANALYSIS ENDPOINTS
# ============================================================================

@threat_intelligence_api.route('/trends/<ip>', methods=['GET'])
def get_attack_trends(ip):
    """Get attack trends for IP"""
    try:
        if not _threat_manager or not _db:
            return jsonify({'error': 'Service not initialized'}), 503
        
        analysis = _threat_manager.analyze_ip(ip)
        trends = analysis['trends']
        
        # Record trend
        _db.record_attack_trend(
            ip,
            trends.get('protocols', ['unknown'])[0],
            trends.get('attack_count', 0),
            trends.get('trend_score', 0),
            trends.get('velocity', 0),
            trends.get('consistency', 0),
            trends.get('anomaly_score', 0),
            trends.get('protocol_diversity', 0)
        )
        
        return jsonify({
            'ip': ip,
            'trends': trends,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_attack_trends: {e}")
        return jsonify({'error': str(e)}), 500

@threat_intelligence_api.route('/score/<ip>', methods=['GET'])
def get_threat_score(ip):
    """Get comprehensive threat score"""
    try:
        if not _threat_manager or not _db:
            return jsonify({'error': 'Service not initialized'}), 503
        
        analysis = _threat_manager.analyze_ip(ip)
        
        # Save score to database
        _db.save_threat_intelligence_score(
            ip,
            analysis['reputation'].get('score', 0),
            analysis['geolocation'].get('risk_score', 0),
            min(100, analysis['threat_feeds'].get('matches', 0) * 20),
            analysis['trends'].get('trend_score', 0),
            analysis['composite_threat_score'],
            analysis['threat_level'],
            analysis['recommendations']
        )
        
        return jsonify({
            'ip': ip,
            'reputation_score': analysis['reputation'].get('score', 0),
            'geo_risk_score': analysis['geolocation'].get('risk_score', 0),
            'feed_match_score': min(100, analysis['threat_feeds'].get('matches', 0) * 20),
            'trend_score': analysis['trends'].get('trend_score', 0),
            'composite_threat_score': analysis['composite_threat_score'],
            'threat_level': analysis['threat_level'],
            'components': {
                'reputation': 30,
                'geolocation': 20,
                'threat_feeds': 30,
                'attack_trends': 20
            }
        })
    except Exception as e:
        logger.error(f"Error in get_threat_score: {e}")
        return jsonify({'error': str(e)}), 500

@threat_intelligence_api.route('/recommend/<ip>', methods=['GET'])
def get_recommendations(ip):
    """Get response recommendations for IP"""
    try:
        if not _threat_manager:
            return jsonify({'error': 'Service not initialized'}), 503
        
        analysis = _threat_manager.analyze_ip(ip)
        
        return jsonify({
            'ip': ip,
            'threat_level': analysis['threat_level'],
            'threat_score': analysis['composite_threat_score'],
            'recommendations': analysis['recommendations'],
            'confidence': 85,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_recommendations: {e}")
        return jsonify({'error': str(e)}), 500

# ============================================================================
# STATISTICS & MONITORING ENDPOINTS
# ============================================================================

@threat_intelligence_api.route('/top-threats', methods=['GET'])
def get_top_threats():
    """Get top threat IPs"""
    try:
        if not _threat_manager or not _db:
            return jsonify({'error': 'Service not initialized'}), 503
        
        limit = request.args.get('limit', default=20, type=int)
        limit = min(limit, 100)  # Cap at 100
        
        top_ips = _db.get_top_threat_ips(limit)
        
        return jsonify({
            'top_threats': top_ips,
            'count': len(top_ips),
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_top_threats: {e}")
        return jsonify({'error': str(e)}), 500

@threat_intelligence_api.route('/statistics', methods=['GET'])
def get_statistics():
    """Get threat intelligence system statistics"""
    try:
        if not _threat_manager or not _db:
            return jsonify({'error': 'Service not initialized'}), 503
        
        threat_stats = _threat_manager.get_statistics()
        db_stats = _db.get_threat_statistics()
        
        return jsonify({
            'manager_stats': threat_stats,
            'database_stats': db_stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in get_statistics: {e}")
        return jsonify({'error': str(e)}), 500

@threat_intelligence_api.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        manager_ok = _threat_manager is not None
        db_ok = _db is not None
        
        return jsonify({
            'status': 'healthy' if (manager_ok and db_ok) else 'degraded',
            'components': {
                'threat_manager': 'ok' if manager_ok else 'down',
                'database': 'ok' if db_ok else 'down',
                'reputation_cache': manager_ok,
                'geolocation_service': manager_ok,
                'threat_feeds': manager_ok,
                'trend_analysis': manager_ok,
            }
        })
    except Exception as e:
        logger.error(f"Error in health_check: {e}")
        return jsonify({'status': 'error', 'error': str(e)}), 500

@threat_intelligence_api.route('/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    return jsonify({
        'api': 'Threat Intelligence REST API',
        'version': '1.0',
        'description': 'Real-time threat intelligence for honeypot data enrichment',
        'endpoints': {
            'IP Reputation': {
                'GET /api/threat-intel/reputation/<ip>': 'Get IP reputation score',
                'GET /api/threat-intel/reputation/<ip>/details': 'Get detailed reputation analysis',
            },
            'Geolocation': {
                'GET /api/threat-intel/geo/<ip>': 'Get geolocation data',
                'GET /api/threat-intel/geo/<ip>/risk': 'Get geographic risk assessment',
            },
            'Threat Feeds': {
                'GET /api/threat-intel/feeds/check/<ip>': 'Check threat feeds',
                'GET /api/threat-intel/feeds/list': 'List available feeds',
            },
            'Analysis': {
                'GET /api/threat-intel/trends/<ip>': 'Get attack trends',
                'GET /api/threat-intel/score/<ip>': 'Get comprehensive threat score',
                'GET /api/threat-intel/recommend/<ip>': 'Get recommendations',
            },
            'Statistics': {
                'GET /api/threat-intel/top-threats?limit=20': 'Get top threat IPs',
                'GET /api/threat-intel/statistics': 'Get system statistics',
                'GET /api/threat-intel/health': 'Health check',
                'GET /api/threat-intel/docs': 'This documentation',
            }
        },
        'threat_levels': ['INFO', 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'],
        'scoring_weights': {
            'reputation': 0.30,
            'geolocation': 0.20,
            'threat_feeds': 0.30,
            'attack_trends': 0.20,
        }
    })
