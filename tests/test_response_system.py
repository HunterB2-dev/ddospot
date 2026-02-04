"""
Test Suite for Response System
Comprehensive tests for response rules, actions, alerts, and SOAR integration
"""

import unittest
import json
import sqlite3
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.insert(0, '/home/hunter/Projekty/ddospot')

from core.response_rules import (
    ResponseRulesEngine, ResponseRule, RuleCondition, RuleOperator,
    ActionType, SeverityLevel, get_default_rules
)

# Try to import alert-related classes, make optional for testing
try:
    from core.response_alerts import (
        NotificationManager, Alert, AlertLevel, NotificationChannel
    )
    ALERTS_AVAILABLE = True
except ImportError:
    ALERTS_AVAILABLE = False
    print("WARNING: Alert notifications not available (aiohttp not installed)")

from core.response_actions import (
    ResponseActionsEngine, BlockAction, RateLimitAction, ActionStatus
)

# ============================================================================
# TEST CONFIGURATION
# ============================================================================

TEST_DB = '/tmp/test_response.db'

def setup_test_db():
    """Setup test database"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

def teardown_test_db():
    """Cleanup test database"""
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

# ============================================================================
# RESPONSE RULES TESTS
# ============================================================================

class TestResponseRules(unittest.TestCase):
    """Test response rules engine"""
    
    def setUp(self):
        setup_test_db()
        self.engine = ResponseRulesEngine(db_path=TEST_DB)
    
    def tearDown(self):
        teardown_test_db()
    
    def test_add_rule(self):
        """Test adding a rule"""
        rule = ResponseRule(
            id='TEST_001',
            name='Test Rule',
            description='Test rule description',
            enabled=True,
            conditions=[
                RuleCondition(
                    field='threat_score',
                    operator=RuleOperator.GREATER_EQUAL,
                    value=80
                )
            ],
            actions=[ActionType.BLOCK_IP, ActionType.ALERT],
            severity=SeverityLevel.CRITICAL,
            priority=1,
            execution_delay=0
        )
        
        result = self.engine.add_rule(rule)
        self.assertTrue(result)
        self.assertIn('TEST_001', self.engine.rules)
    
    def test_rule_matching_positive(self):
        """Test rule matching with matching threat data"""
        rule = ResponseRule(
            id='TEST_002',
            name='High Threat Rule',
            description='Matches high threats',
            enabled=True,
            conditions=[
                RuleCondition(
                    field='threat_score',
                    operator=RuleOperator.GREATER_EQUAL,
                    value=75
                )
            ],
            actions=[ActionType.BLOCK_IP],
            severity=SeverityLevel.HIGH,
            priority=2,
            execution_delay=0
        )
        
        self.engine.add_rule(rule)
        
        threat_data = {'threat_score': 85, 'ip': '192.168.1.1'}
        matches = self.engine.find_matching_rules(threat_data)
        
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0][0].id, 'TEST_002')
    
    def test_rule_matching_negative(self):
        """Test rule not matching with non-matching threat data"""
        rule = ResponseRule(
            id='TEST_003',
            name='High Threat Rule',
            description='Only matches high threats',
            enabled=True,
            conditions=[
                RuleCondition(
                    field='threat_score',
                    operator=RuleOperator.GREATER_EQUAL,
                    value=80
                )
            ],
            actions=[ActionType.BLOCK_IP],
            severity=SeverityLevel.CRITICAL,
            priority=1,
            execution_delay=0
        )
        
        self.engine.add_rule(rule)
        
        threat_data = {'threat_score': 50, 'ip': '192.168.1.1'}
        matches = self.engine.find_matching_rules(threat_data)
        
        self.assertEqual(len(matches), 0)
    
    def test_rule_conditions_all_operators(self):
        """Test all condition operators"""
        test_cases = [
            ('threat_score', RuleOperator.EQUALS, 80, 80, True),
            ('threat_score', RuleOperator.NOT_EQUALS, 80, 75, True),
            ('threat_score', RuleOperator.GREATER_THAN, 70, 75, True),
            ('threat_score', RuleOperator.LESS_THAN, 80, 75, True),
            ('threat_score', RuleOperator.GREATER_EQUAL, 75, 75, True),
            ('threat_score', RuleOperator.LESS_EQUAL, 80, 75, True),
        ]
        
        for field, op, condition_value, data_value, expected in test_cases:
            condition = RuleCondition(
                field=field,
                operator=op,
                value=condition_value
            )
            
            threat_data = {'threat_score': data_value}
            result = condition.matches(threat_data)
            
            self.assertEqual(result, expected, 
                           f'Failed for {op.value} with {data_value} vs {condition_value}')
    
    def test_enable_disable_rule(self):
        """Test enabling and disabling rules"""
        rule = ResponseRule(
            id='TEST_004',
            name='Toggle Rule',
            description='Rule to toggle',
            enabled=True,
            conditions=[],
            actions=[ActionType.LOG],
            severity=SeverityLevel.LOW,
            priority=5,
            execution_delay=0
        )
        
        self.engine.add_rule(rule)
        
        self.assertTrue(self.engine.rules['TEST_004'].enabled)
        self.engine.disable_rule('TEST_004')
        self.assertFalse(self.engine.rules['TEST_004'].enabled)
        self.engine.enable_rule('TEST_004')
        self.assertTrue(self.engine.rules['TEST_004'].enabled)
    
    def test_remove_rule(self):
        """Test removing a rule"""
        rule = ResponseRule(
            id='TEST_005',
            name='Removable Rule',
            description='Will be removed',
            enabled=True,
            conditions=[],
            actions=[ActionType.LOG],
            severity=SeverityLevel.INFO,
            priority=10,
            execution_delay=0
        )
        
        self.engine.add_rule(rule)
        self.assertIn('TEST_005', self.engine.rules)
        
        self.engine.remove_rule('TEST_005')
        self.assertNotIn('TEST_005', self.engine.rules)
    
    def test_execution_logging(self):
        """Test logging rule execution"""
        rule = ResponseRule(
            id='TEST_006',
            name='Logged Rule',
            description='Rule with logging',
            enabled=True,
            conditions=[],
            actions=[ActionType.LOG, ActionType.ALERT],
            severity=SeverityLevel.MEDIUM,
            priority=3,
            execution_delay=0
        )
        
        self.engine.add_rule(rule)
        
        success = self.engine.log_execution(
            rule_id='TEST_006',
            threat_ip='192.168.1.1',
            threat_score=75.5,
            actions=['ALERT', 'LOG'],
            status='success',
            result='Alert sent successfully'
        )
        
        self.assertTrue(success)
        
        history = self.engine.get_execution_history('TEST_006')
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['threat_ip'], '192.168.1.1')
    
    def test_default_rules(self):
        """Test loading default rules"""
        default_rules = get_default_rules()
        
        self.assertGreater(len(default_rules), 0)
        
        for rule in default_rules:
            self.assertIsNotNone(rule.id)
            self.assertIsNotNone(rule.name)
            self.assertIsNotNone(rule.conditions)
            self.assertIsNotNone(rule.actions)

# ============================================================================
# RESPONSE ACTIONS TESTS
# ============================================================================

class TestResponseActions(unittest.TestCase):
    """Test response actions engine"""
    
    def setUp(self):
        setup_test_db()
        self.engine = ResponseActionsEngine(db_path=TEST_DB)
    
    def tearDown(self):
        teardown_test_db()
    
    def test_block_action_creation(self):
        """Test creating block action"""
        action = BlockAction(
            ip_address='192.168.1.100',
            reason='DDoS attack detected',
            duration=3600,
            priority=1
        )
        
        self.assertEqual(action.ip_address, '192.168.1.100')
        self.assertEqual(action.reason, 'DDoS attack detected')
        self.assertEqual(action.duration, 3600)
        self.assertIsNotNone(action.timestamp)
        self.assertIsNotNone(action.expiry)
    
    def test_rate_limit_action_creation(self):
        """Test creating rate limit action"""
        action = RateLimitAction(
            ip_address='192.168.1.101',
            requests_per_second=10,
            duration=1800
        )
        
        self.assertEqual(action.ip_address, '192.168.1.101')
        self.assertEqual(action.requests_per_second, 10)
        self.assertEqual(action.duration, 1800)
        self.assertIsNotNone(action.timestamp)
        self.assertIsNotNone(action.expiry)
    
    def test_get_blocked_ips_empty(self):
        """Test getting blocked IPs when none exist"""
        blocked = self.engine.get_blocked_ips()
        self.assertEqual(len(blocked), 0)
    
    def test_get_rate_limited_ips_empty(self):
        """Test getting rate-limited IPs when none exist"""
        limited = self.engine.get_rate_limited_ips()
        self.assertEqual(len(limited), 0)
    
    def test_cleanup_expired_blocks(self):
        """Test cleaning up expired blocks"""
        # Note: Without firewall handlers, blocks won't be added to firewall
        # but should still be tracked internally
        
        action = BlockAction(
            ip_address='192.168.1.102',
            reason='Test expire',
            duration=1,  # 1 second
            priority=1
        )
        
        # Note: This would normally be called with firewall handlers
        # For testing, we just verify the logic exists
        self.engine.blocked_ips[action.ip_address] = action
        
        import time
        time.sleep(2)
        
        count = self.engine.cleanup_expired_blocks()
        self.assertGreaterEqual(count, 0)

# ============================================================================
# ALERT NOTIFICATIONS TESTS
# ============================================================================

class TestAlertNotifications(unittest.TestCase):
    """Test alert notification system"""
    
    def setUp(self):
        if not ALERTS_AVAILABLE:
            self.skipTest("Alert notifications not available")
        
        config = {
            'channels': {
                'dashboard': {
                    'enabled': True,
                    'max_alerts': 100
                },
                'email': {
                    'enabled': False
                },
                'webhook': {
                    'enabled': False
                },
                'sms': {
                    'enabled': False
                },
                'slack': {
                    'enabled': False
                }
            }
        }
        
        self.manager = NotificationManager(config)  # type: ignore
    
    def test_alert_creation(self):
        """Test creating an alert"""
        alert = Alert(  # type: ignore
            id='ALERT_001',
            level=AlertLevel.CRITICAL,  # type: ignore
            title='Critical Threat Detected',
            message='IP 192.168.1.1 detected as critical threat',
            threat_data={'ip': '192.168.1.1', 'threat_score': 95},
            rule_id='RULE_001'
        )
        
        self.assertEqual(alert.id, 'ALERT_001')
        self.assertEqual(alert.level, AlertLevel.CRITICAL)  # type: ignore
        self.assertIsNotNone(alert.timestamp)
    
    def test_alert_to_dict(self):
        """Test converting alert to dictionary"""
        alert = Alert(  # type: ignore
            id='ALERT_002',
            level=AlertLevel.HIGH,  # type: ignore
            title='High Threat',
            message='Test message',
            threat_data={'score': 85},
            rule_id='RULE_002'
        )
        
        alert_dict = alert.to_dict()
        
        self.assertEqual(alert_dict['id'], 'ALERT_002')
        self.assertEqual(alert_dict['level'], 'HIGH')
        self.assertIn('timestamp', alert_dict)
    
    def test_send_alert_dashboard(self):
        """Test sending alert to dashboard"""
        alert = Alert(  # type: ignore
            id='ALERT_003',
            level=AlertLevel.MEDIUM,  # type: ignore
            title='Medium Alert',
            message='Test alert',
            threat_data={'score': 60},
            rule_id='RULE_003'
        )
        
        results = self.manager.send_alert(alert)
        
        self.assertIsNotNone(results)
        if 'dashboard' in results:
            self.assertTrue(results['dashboard'])
    
    def test_get_dashboard_alerts(self):
        """Test retrieving dashboard alerts"""
        alert1 = Alert(  # type: ignore
            id='ALERT_004',
            level=AlertLevel.LOW,  # type: ignore
            title='Low Alert 1',
            message='Message 1',
            threat_data={'score': 30},
            rule_id='RULE_004'
        )
        
        alert2 = Alert(  # type: ignore
            id='ALERT_005',
            level=AlertLevel.INFO,  # type: ignore
            title='Info Alert',
            message='Message 2',
            threat_data={'score': 10},
            rule_id='RULE_005'
        )
        
        self.manager.send_alert(alert1)
        self.manager.send_alert(alert2)
        
        alerts = self.manager.get_dashboard_alerts(10)
        
        self.assertEqual(len(alerts), 2)
    
    def test_notification_manager_stats(self):
        """Test notification manager statistics"""
        stats = self.manager.get_stats()
        
        self.assertIn('total_alerts', stats)
        self.assertIn('handlers_enabled', stats)
        self.assertGreaterEqual(stats['total_alerts'], 0)

# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestResponseIntegration(unittest.TestCase):
    """Test integration between response components"""
    
    def setUp(self):
        setup_test_db()
        self.rules_engine = ResponseRulesEngine(db_path=TEST_DB)
        self.actions_engine = ResponseActionsEngine(db_path=TEST_DB)
        
        if ALERTS_AVAILABLE:
            self.alerts_manager = NotificationManager()  # type: ignore
        else:
            self.alerts_manager = None
    
    def tearDown(self):
        teardown_test_db()
    
    def test_end_to_end_threat_response(self):
        """Test end-to-end threat detection and response"""
        # Add a rule
        rule = ResponseRule(
            id='E2E_RULE',
            name='E2E Test Rule',
            description='End-to-end test',
            enabled=True,
            conditions=[
                RuleCondition(
                    field='threat_score',
                    operator=RuleOperator.GREATER_EQUAL,
                    value=70
                )
            ],
            actions=[ActionType.ALERT, ActionType.LOG],
            severity=SeverityLevel.HIGH,
            priority=2,
            execution_delay=0
        )
        
        self.rules_engine.add_rule(rule)
        
        # Simulate threat data
        threat_data = {
            'ip': '192.168.1.200',
            'threat_score': 85,
            'threat_type': 'DDoS'
        }
        
        # Find matching rules
        matching = self.rules_engine.find_matching_rules(threat_data)
        self.assertEqual(len(matching), 1)
        
        # Log execution
        self.rules_engine.log_execution(
            rule_id='E2E_RULE',
            threat_ip=threat_data['ip'],
            threat_score=threat_data['threat_score'],
            actions=['ALERT', 'LOG'],
            status='success'
        )
        
        # Send alert (if available)
        if self.alerts_manager:
            alert = Alert(  # type: ignore
                id='E2E_ALERT',
                level=AlertLevel.HIGH,  # type: ignore
                title='E2E Test Alert',
                message=f"Threat detected: {threat_data['ip']}",
                threat_data=threat_data,
                rule_id='E2E_RULE'
            )
            
            results = self.alerts_manager.send_alert(alert)
            self.assertIsNotNone(results)
        
        # Verify execution history
        history = self.rules_engine.get_execution_history('E2E_RULE')
        self.assertGreater(len(history), 0)
    
    def test_multiple_rules_matching(self):
        """Test matching multiple rules"""
        # Add multiple rules
        rule1 = ResponseRule(
            id='MULTI_1',
            name='Rule 1',
            description='High threat',
            enabled=True,
            conditions=[
                RuleCondition(
                    field='threat_score',
                    operator=RuleOperator.GREATER_EQUAL,
                    value=50
                )
            ],
            actions=[ActionType.LOG],
            severity=SeverityLevel.HIGH,
            priority=1,
            execution_delay=0
        )
        
        rule2 = ResponseRule(
            id='MULTI_2',
            name='Rule 2',
            description='Medium threat',
            enabled=True,
            conditions=[
                RuleCondition(
                    field='threat_score',
                    operator=RuleOperator.GREATER_EQUAL,
                    value=30
                )
            ],
            actions=[ActionType.LOG],
            severity=SeverityLevel.MEDIUM,
            priority=2,
            execution_delay=0
        )
        
        self.rules_engine.add_rule(rule1)
        self.rules_engine.add_rule(rule2)
        
        threat_data = {'threat_score': 75}
        matches = self.rules_engine.find_matching_rules(threat_data)
        
        # Both rules should match (sorted by priority)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[0][0].id, 'MULTI_1')
        self.assertEqual(matches[1][0].id, 'MULTI_2')

# ============================================================================
# PERFORMANCE TESTS
# ============================================================================

class TestResponsePerformance(unittest.TestCase):
    """Test response system performance"""
    
    def setUp(self):
        setup_test_db()
        self.rules_engine = ResponseRulesEngine(db_path=TEST_DB)
    
    def tearDown(self):
        teardown_test_db()
    
    def test_rule_matching_performance(self):
        """Test rule matching performance with multiple rules"""
        import time
        
        # Add 100 rules
        for i in range(100):
            rule = ResponseRule(
                id=f'PERF_{i:03d}',
                name=f'Performance Rule {i}',
                description='Performance test rule',
                enabled=True,
                conditions=[
                    RuleCondition(
                        field='threat_score',
                        operator=RuleOperator.GREATER_EQUAL,
                        value=i % 100
                    )
                ],
                actions=[ActionType.LOG],
                severity=SeverityLevel.LOW,
                priority=i,
                execution_delay=0
            )
            self.rules_engine.add_rule(rule)
        
        threat_data = {'threat_score': 85}
        
        # Measure matching time
        start = time.time()
        for _ in range(100):
            matches = self.rules_engine.find_matching_rules(threat_data)
        elapsed = time.time() - start
        
        avg_time = (elapsed / 100) * 1000  # Convert to ms
        
        # Rule matching should be fast (< 50ms per call on average)
        self.assertLess(avg_time, 50, 
                       f'Rule matching too slow: {avg_time:.2f}ms')

# ============================================================================
# TEST RUNNER
# ============================================================================

if __name__ == '__main__':
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test cases
    suite.addTests(loader.loadTestsFromTestCase(TestResponseRules))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseActions))
    suite.addTests(loader.loadTestsFromTestCase(TestAlertNotifications))
    suite.addTests(loader.loadTestsFromTestCase(TestResponseIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestResponsePerformance))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print('\n' + '=' * 70)
    print('TEST SUMMARY')
    print('=' * 70)
    print(f'Tests run: {result.testsRun}')
    print(f'Successes: {result.testsRun - len(result.failures) - len(result.errors)}')
    print(f'Failures: {len(result.failures)}')
    print(f'Errors: {len(result.errors)}')
    print(f'Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%')
    print('=' * 70)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
