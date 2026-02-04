"""
Response Management API
REST API endpoints for managing automated response rules and actions
"""

import logging
from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import uuid

logger = logging.getLogger(__name__)

# ============================================================================
# API BLUEPRINT
# ============================================================================

response_api = Blueprint('response', __name__, url_prefix='/api/response')

# ============================================================================
# RESPONSE RULES ENDPOINTS
# ============================================================================

@response_api.route('/rules', methods=['GET'])
def get_rules():
    """Get all response rules"""
    try:
        from core.response_rules import get_response_engine
        
        engine = get_response_engine()
        rules = engine.get_all_rules()
        
        return jsonify({
            'success': True,
            'data': [r.to_dict() for r in rules],
            'count': len(rules)
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting rules: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """Get specific rule"""
    try:
        from core.response_rules import get_response_engine
        
        engine = get_response_engine()
        rule = engine.get_rule(rule_id)
        
        if not rule:
            return jsonify({'success': False, 'error': 'Rule not found'}), 404
        
        return jsonify({
            'success': True,
            'data': rule.to_dict()
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting rule: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/rules', methods=['POST'])
def create_rule():
    """Create new response rule"""
    try:
        from core.response_rules import (
            get_response_engine, ResponseRule, RuleCondition,
            ActionType, SeverityLevel, RuleOperator
        )
        
        data = request.get_json()
        
        # Validate input
        required_fields = ['name', 'description', 'conditions', 'actions', 'severity']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        # Parse conditions
        conditions = []
        for cond_data in data.get('conditions', []):
            condition = RuleCondition(
                field=cond_data['field'],
                operator=RuleOperator(cond_data['operator']),
                value=cond_data['value']
            )
            conditions.append(condition)
        
        # Parse actions
        actions = [ActionType(a) for a in data.get('actions', [])]
        
        # Create rule
        rule = ResponseRule(
            id=data.get('id', f'RULE_{uuid.uuid4().hex[:8].upper()}'),
            name=data['name'],
            description=data['description'],
            enabled=data.get('enabled', True),
            conditions=conditions,
            actions=actions,
            severity=SeverityLevel[data['severity']],
            priority=data.get('priority', 10),
            execution_delay=data.get('execution_delay', 0),
            max_triggers_per_hour=data.get('max_triggers_per_hour'),
            active_hours=data.get('active_hours', '24/7'),
            notes=data.get('notes', '')
        )
        
        # Add to engine
        engine = get_response_engine()
        if engine.add_rule(rule):
            return jsonify({
                'success': True,
                'data': rule.to_dict(),
                'message': f'Rule created: {rule.id}'
            }), 201
        else:
            return jsonify({'success': False, 'error': 'Failed to add rule'}), 500
    
    except Exception as e:
        logger.error(f'[API] Error creating rule: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """Update response rule"""
    try:
        from core.response_rules import get_response_engine
        
        engine = get_response_engine()
        rule = engine.get_rule(rule_id)
        
        if not rule:
            return jsonify({'success': False, 'error': 'Rule not found'}), 404
        
        data = request.get_json()
        
        # Update fields
        if 'enabled' in data:
            if data['enabled']:
                engine.enable_rule(rule_id)
            else:
                engine.disable_rule(rule_id)
        
        if 'priority' in data:
            rule.priority = data['priority']
        
        if 'max_triggers_per_hour' in data:
            rule.max_triggers_per_hour = data['max_triggers_per_hour']
        
        rule.updated_at = datetime.now()
        engine._update_rule_in_db(rule)
        
        return jsonify({
            'success': True,
            'data': rule.to_dict(),
            'message': f'Rule updated: {rule_id}'
        })
    
    except Exception as e:
        logger.error(f'[API] Error updating rule: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """Delete response rule"""
    try:
        from core.response_rules import get_response_engine
        
        engine = get_response_engine()
        
        if engine.remove_rule(rule_id):
            return jsonify({
                'success': True,
                'message': f'Rule deleted: {rule_id}'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to delete rule'}), 500
    
    except Exception as e:
        logger.error(f'[API] Error deleting rule: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# BLOCKED IPS ENDPOINTS
# ============================================================================

@response_api.route('/blocked-ips', methods=['GET'])
def get_blocked_ips():
    """Get all blocked IPs"""
    try:
        from core.response_actions import get_response_actions
        
        engine = get_response_actions()
        blocked_ips = engine.get_blocked_ips()
        
        return jsonify({
            'success': True,
            'data': blocked_ips,
            'count': len(blocked_ips)
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting blocked IPs: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/block-ip', methods=['POST'])
def block_ip():
    """Block an IP address"""
    try:
        from core.response_actions import get_response_actions, BlockAction
        
        data = request.get_json()
        
        if 'ip' not in data:
            return jsonify({'success': False, 'error': 'Missing IP address'}), 400
        
        engine = get_response_actions()
        
        action = BlockAction(
            ip_address=data['ip'],
            reason=data.get('reason', 'DDoSSpot auto-block'),
            duration=data.get('duration', 0),
            priority=data.get('priority', 1)
        )
        
        success, message = engine.block_ip(action)
        
        return jsonify({
            'success': success,
            'message': message,
            'data': {
                'ip': data['ip'],
                'reason': action.reason,
                'duration': action.duration
            }
        }), (200 if success else 400)
    
    except Exception as e:
        logger.error(f'[API] Error blocking IP: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/unblock-ip', methods=['POST'])
def unblock_ip():
    """Unblock an IP address"""
    try:
        from core.response_actions import get_response_actions
        
        data = request.get_json()
        
        if 'ip' not in data:
            return jsonify({'success': False, 'error': 'Missing IP address'}), 400
        
        engine = get_response_actions()
        success, message = engine.unblock_ip(data['ip'])
        
        return jsonify({
            'success': success,
            'message': message,
            'data': {'ip': data['ip']}
        }), (200 if success else 400)
    
    except Exception as e:
        logger.error(f'[API] Error unblocking IP: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# RATE LIMITING ENDPOINTS
# ============================================================================

@response_api.route('/rate-limited-ips', methods=['GET'])
def get_rate_limited_ips():
    """Get all rate-limited IPs"""
    try:
        from core.response_actions import get_response_actions
        
        engine = get_response_actions()
        limited_ips = engine.get_rate_limited_ips()
        
        return jsonify({
            'success': True,
            'data': limited_ips,
            'count': len(limited_ips)
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting rate-limited IPs: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/rate-limit', methods=['POST'])
def rate_limit():
    """Apply rate limiting to an IP"""
    try:
        from core.response_actions import get_response_actions, RateLimitAction
        
        data = request.get_json()
        
        required_fields = ['ip', 'requests_per_second', 'duration']
        for field in required_fields:
            if field not in data:
                return jsonify({'success': False, 'error': f'Missing field: {field}'}), 400
        
        engine = get_response_actions()
        
        action = RateLimitAction(
            ip_address=data['ip'],
            requests_per_second=data['requests_per_second'],
            duration=data['duration']
        )
        
        success, message = engine.rate_limit_ip(action)
        
        return jsonify({
            'success': success,
            'message': message,
            'data': {
                'ip': data['ip'],
                'requests_per_second': data['requests_per_second'],
                'duration': data['duration']
            }
        }), (200 if success else 400)
    
    except Exception as e:
        logger.error(f'[API] Error rate limiting: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/remove-rate-limit', methods=['POST'])
def remove_rate_limit():
    """Remove rate limiting from an IP"""
    try:
        from core.response_actions import get_response_actions
        
        data = request.get_json()
        
        if 'ip' not in data:
            return jsonify({'success': False, 'error': 'Missing IP address'}), 400
        
        engine = get_response_actions()
        success, message = engine.remove_rate_limit(data['ip'])
        
        return jsonify({
            'success': success,
            'message': message,
            'data': {'ip': data['ip']}
        }), (200 if success else 400)
    
    except Exception as e:
        logger.error(f'[API] Error removing rate limit: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ALERTS ENDPOINTS
# ============================================================================

@response_api.route('/alerts', methods=['GET'])
def get_alerts():
    """Get recent alerts"""
    try:
        from core.response_alerts import get_notification_manager
        
        limit = request.args.get('limit', 50, type=int)
        
        manager = get_notification_manager()
        alerts = manager.get_dashboard_alerts(limit)
        
        return jsonify({
            'success': True,
            'data': alerts,
            'count': len(alerts)
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting alerts: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/alert-history', methods=['GET'])
def get_alert_history():
    """Get alert history"""
    try:
        from core.response_alerts import get_notification_manager
        
        limit = request.args.get('limit', 100, type=int)
        
        manager = get_notification_manager()
        history = manager.get_alert_history(limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting alert history: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# STATISTICS & STATUS ENDPOINTS
# ============================================================================

@response_api.route('/statistics', methods=['GET'])
def get_statistics():
    """Get response system statistics"""
    try:
        from core.response_rules import get_response_engine
        from core.response_actions import get_response_actions
        from core.response_alerts import get_notification_manager
        
        rules_engine = get_response_engine()
        actions_engine = get_response_actions()
        alerts_manager = get_notification_manager()
        
        return jsonify({
            'success': True,
            'data': {
                'rules': rules_engine.get_statistics(),
                'blocked_ips': len(actions_engine.get_blocked_ips()),
                'rate_limited_ips': len(actions_engine.get_rate_limited_ips()),
                'alerts': alerts_manager.get_stats()
            }
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting statistics: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/status', methods=['GET'])
def get_status():
    """Get response system status"""
    try:
        from core.response_rules import get_response_engine
        from core.response_actions import get_response_actions
        from core.response_alerts import get_notification_manager
        from core.response_soar import get_soar_integration
        
        rules_engine = get_response_engine()
        actions_engine = get_response_actions()
        alerts_manager = get_notification_manager()
        soar_engine = get_soar_integration()
        
        return jsonify({
            'success': True,
            'data': {
                'timestamp': datetime.now().isoformat(),
                'rules': {
                    'total': len(rules_engine.rules),
                    'enabled': sum(1 for r in rules_engine.rules.values() if r.enabled)
                },
                'firewall_handlers': list(actions_engine.firewall_handlers.keys()),
                'notification_channels': list(alerts_manager.handlers.keys()),
                'soar_platforms': list(soar_engine.handlers.keys()),
                'system_status': 'operational'
            }
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting status: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

@response_api.route('/execution-history', methods=['GET'])
def get_execution_history():
    """Get rule execution history"""
    try:
        from core.response_rules import get_response_engine
        
        rule_id = request.args.get('rule_id')
        limit = request.args.get('limit', 100, type=int)
        
        engine = get_response_engine()
        history = engine.get_execution_history(rule_id, limit)
        
        return jsonify({
            'success': True,
            'data': history,
            'count': len(history)
        })
    
    except Exception as e:
        logger.error(f'[API] Error getting execution history: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@response_api.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'success': False, 'error': 'Endpoint not found'}), 404

@response_api.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f'[API] Internal error: {error}')
    return jsonify({'success': False, 'error': 'Internal server error'}), 500
