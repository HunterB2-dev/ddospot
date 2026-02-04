#!/usr/bin/env python3
"""
REST API endpoints for Advanced Evasion Detection
Integrates evasion detection with the dashboard API
"""

from flask import Blueprint, jsonify, request
from core.evasion_detection import get_evasion_manager
from core.database import HoneypotDatabase
import json

# Create blueprint
evasion_api = Blueprint('evasion', __name__, url_prefix='/api/evasion')

# Get database and evasion manager instances
_db = None
_evasion_manager = None


def init_evasion_api(db: 'HoneypotDatabase') -> None:
    """Initialize evasion API with database"""
    global _db, _evasion_manager
    _db = db
    _evasion_manager = get_evasion_manager()


# ========================
# Evasion Detection Endpoints
# ========================

@evasion_api.route('/analyze/<source_ip>', methods=['GET'])
def analyze_ip_evasion(source_ip: str):
    """
    Analyze evasion techniques for a specific IP
    
    Returns:
        {
            "ip": "192.168.1.1",
            "analysis": {...evasion analysis...},
            "detections_count": 5,
            "stats": {...},
            "threat_level": "HIGH"
        }
    """
    if not _evasion_manager or not _db:
        return jsonify({"error": "Service not initialized"}), 503
    
    try:
        # Get evasion statistics
        stats = _db.get_evasion_statistics(source_ip)
        
        # Get latest detections
        detections = _db.get_evasion_detections(source_ip, limit=10)
        
        # Calculate threat level
        if stats.get('max_evasion_score', 0) >= 0.8:
            threat_level = "CRITICAL"
        elif stats.get('max_evasion_score', 0) >= 0.6:
            threat_level = "HIGH"
        elif stats.get('max_evasion_score', 0) >= 0.3:
            threat_level = "MEDIUM"
        else:
            threat_level = "LOW"
        
        return jsonify({
            "ip": source_ip,
            "stats": stats,
            "threat_level": threat_level,
            "detections": detections,
            "detection_count": len(detections)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@evasion_api.route('/top-evasion-ips', methods=['GET'])
def get_top_evasion_ips():
    """
    Get top IPs with highest evasion detection scores
    
    Query parameters:
        limit: Maximum number of IPs to return (default: 10)
    
    Returns:
        {
            "top_ips": [
                {"ip": "192.168.1.1", "detection_count": 5, "avg_score": 0.72, "max_score": 0.85},
                ...
            ]
        }
    """
    if not _db:
        return jsonify({"error": "Service not initialized"}), 503
    
    try:
        limit = request.args.get('limit', 10, type=int)
        top_ips = _db.get_top_evasion_ips(limit=limit)
        
        return jsonify({
            "total": len(top_ips),
            "top_ips": top_ips
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@evasion_api.route('/detections/<source_ip>', methods=['GET'])
def get_ip_detections(source_ip: str):
    """
    Get all evasion detections for an IP
    
    Query parameters:
        limit: Maximum number of detections (default: 100)
        type: Filter by detection type (slow_attack, protocol_confusion, etc)
    
    Returns:
        {
            "ip": "192.168.1.1",
            "detections": [...],
            "count": 5
        }
    """
    if not _db:
        return jsonify({"error": "Service not initialized"}), 503
    
    try:
        limit = request.args.get('limit', 100, type=int)
        detection_type = request.args.get('type', None)
        
        detections = _db.get_evasion_detections(source_ip, limit=limit)
        
        # Filter by type if specified
        if detection_type:
            detections = [d for d in detections if d.get('detection_type') == detection_type]
        
        return jsonify({
            "ip": source_ip,
            "count": len(detections),
            "detections": detections
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@evasion_api.route('/patterns/slow-attack', methods=['GET'])
def get_slow_attack_patterns():
    """
    Get information about detected slow attack patterns
    
    Returns:
        {
            "slow_attacks": [
                {"ip": "192.168.1.1", "consistency": 0.85, "duration": 300},
                ...
            ]
        }
    """
    if not _evasion_manager or not _db:
        return jsonify({"error": "Service not initialized"}), 503
    
    try:
        # Get all high-score detections of type slow_attack
        cursor = _db.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT source_ip, evasion_score
            FROM evasion_detections
            WHERE detection_type LIKE '%slow%'
            ORDER BY evasion_score DESC
            LIMIT 20
        """)
        
        results = [{"ip": row[0], "score": round(row[1], 3)} for row in cursor.fetchall()]
        
        return jsonify({
            "slow_attacks": results,
            "count": len(results)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@evasion_api.route('/patterns/protocol-confusion', methods=['GET'])
def get_protocol_confusion_patterns():
    """
    Get information about detected protocol confusion patterns
    
    Returns:
        {
            "protocol_confusion": [
                {"ip": "192.168.1.1", "protocols": ["http", "ssh", "ftp"], "switches": 5},
                ...
            ]
        }
    """
    if not _db:
        return jsonify({"error": "Service not initialized"}), 503
    
    try:
        # Get all detections of protocol confusion type
        cursor = _db.conn.cursor()
        cursor.execute("""
            SELECT DISTINCT source_ip, details
            FROM evasion_detections
            WHERE detection_type LIKE '%protocol%'
            ORDER BY evasion_score DESC
            LIMIT 20
        """)
        
        results = []
        for row in cursor.fetchall():
            try:
                details = json.loads(row[1]) if row[1] else {}
                results.append({
                    "ip": row[0],
                    "protocols": details.get('protocol_list', []),
                    "score": details.get('score', 0)
                })
            except:
                pass
        
        return jsonify({
            "protocol_confusion": results,
            "count": len(results)
        }), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@evasion_api.route('/statistics', methods=['GET'])
def get_evasion_statistics():
    """
    Get overall evasion detection statistics
    
    Returns:
        {
            "total_detections": 150,
            "unique_ips": 25,
            "detection_types": {"slow_attack": 45, "protocol_confusion": 50, ...},
            "threat_levels": {"CRITICAL": 5, "HIGH": 15, "MEDIUM": 30, "LOW": 100},
            "avg_score": 0.45,
            "max_score": 0.92
        }
    """
    if not _db:
        return jsonify({"error": "Service not initialized"}), 503
    
    try:
        cursor = _db.conn.cursor()
        
        # Get total counts and statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(DISTINCT source_ip) as unique_ips,
                AVG(evasion_score) as avg_score,
                MAX(evasion_score) as max_score
            FROM evasion_detections
        """)
        row = cursor.fetchone()
        
        stats = {
            "total_detections": row[0],
            "unique_ips": row[1],
            "avg_score": round(row[2], 3) if row[2] else 0,
            "max_score": round(row[3], 3) if row[3] else 0
        }
        
        # Get detection type breakdown
        cursor.execute("""
            SELECT detection_type, COUNT(*) as count
            FROM evasion_detections
            GROUP BY detection_type
        """)
        stats['detection_types'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Get threat level breakdown
        cursor.execute("""
            SELECT threat_level, COUNT(*) as count
            FROM evasion_detections
            GROUP BY threat_level
        """)
        stats['threat_levels'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        return jsonify(stats), 200
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@evasion_api.route('/health', methods=['GET'])
def health_check():
    """Health check for evasion detection service"""
    try:
        if not _evasion_manager or not _db:
            return jsonify({
                "status": "NOT_INITIALIZED",
                "message": "Evasion detection service not initialized"
            }), 503
        
        # Check if we can query database
        cursor = _db.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM evasion_detections")
        
        return jsonify({
            "status": "HEALTHY",
            "evasion_manager": "active",
            "database": "connected"
        }), 200
    
    except Exception as e:
        return jsonify({
            "status": "ERROR",
            "message": str(e)
        }), 500


# ========================
# API Documentation
# ========================

@evasion_api.route('/docs', methods=['GET'])
def api_docs():
    """API documentation"""
    return jsonify({
        "name": "Advanced Evasion Detection API",
        "version": "1.0",
        "endpoints": {
            "GET /api/evasion/analyze/<ip>": "Analyze evasion techniques for an IP",
            "GET /api/evasion/top-evasion-ips": "Get top IPs with highest evasion scores",
            "GET /api/evasion/detections/<ip>": "Get detections for an IP",
            "GET /api/evasion/patterns/slow-attack": "Get slow attack patterns",
            "GET /api/evasion/patterns/protocol-confusion": "Get protocol confusion patterns",
            "GET /api/evasion/statistics": "Get overall statistics",
            "GET /api/evasion/health": "Health check",
            "GET /api/evasion/docs": "API documentation"
        },
        "detection_types": [
            "slow_attack: Sustained low-rate attacks below threshold",
            "protocol_confusion: Mixing multiple protocols from single source",
            "polymorphic: Obfuscated attack variants",
            "behavioral_anomaly: Deviations from normal behavior"
        ],
        "threat_levels": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]
    }), 200
