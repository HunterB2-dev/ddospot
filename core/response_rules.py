"""
Response Rules Engine for Automated Attack Response
Manages threat response rules, rule matching, and action determination
"""

import json
import logging
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, asdict
import sqlite3

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & TYPES
# ============================================================================

class ActionType(Enum):
    """Automated response action types"""
    BLOCK_IP = "block_ip"
    RATE_LIMIT = "rate_limit"
    ALERT = "alert"
    INCIDENT = "incident"
    QUARANTINE = "quarantine"
    LOG = "log"
    PLAYBOOK = "playbook"

class SeverityLevel(Enum):
    """Response severity levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1

class RuleOperator(Enum):
    """Comparison operators for rule conditions"""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    LESS_THAN = "<"
    GREATER_EQUAL = ">="
    LESS_EQUAL = "<="
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class RuleCondition:
    """Single condition in a rule"""
    field: str
    operator: RuleOperator
    value: Any
    
    def matches(self, threat_data: Dict) -> bool:
        """Check if threat data matches this condition"""
        threat_value = threat_data.get(self.field)
        if threat_value is None:
            return False
        
        op = self.operator.value
        
        if op == "==":
            return threat_value == self.value
        elif op == "!=":
            return threat_value != self.value
        elif op == ">":
            return threat_value > self.value
        elif op == "<":
            return threat_value < self.value
        elif op == ">=":
            return threat_value >= self.value
        elif op == "<=":
            return threat_value <= self.value
        elif op == "contains":
            return str(self.value) in str(threat_value)
        elif op == "not_contains":
            return str(self.value) not in str(threat_value)
        elif op == "in":
            return threat_value in self.value
        elif op == "not_in":
            return threat_value not in self.value
        
        return False

@dataclass
class ResponseRule:
    """Automated response rule definition"""
    id: str
    name: str
    description: str
    enabled: bool
    conditions: List[RuleCondition]
    actions: List[ActionType]
    severity: SeverityLevel
    priority: int
    execution_delay: int  # seconds
    max_triggers_per_hour: Optional[int] = None
    active_hours: str = "24/7"
    notes: str = ""
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    def matches(self, threat_data: Dict) -> bool:
        """Check if threat data matches all conditions"""
        if not self.enabled:
            return False
        
        # All conditions must match (AND logic)
        for condition in self.conditions:
            if not condition.matches(threat_data):
                return False
        
        return True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['conditions'] = [
            {
                'field': c.field,
                'operator': c.operator.value,
                'value': c.value
            }
            for c in self.conditions
        ]
        data['actions'] = [a.value for a in self.actions]
        data['severity'] = self.severity.name
        data['created_at'] = self.created_at.isoformat() if self.created_at else None
        data['updated_at'] = self.updated_at.isoformat() if self.updated_at else None
        return data

# ============================================================================
# RESPONSE RULE ENGINE
# ============================================================================

class ResponseRulesEngine:
    """
    Manages and executes response rules for automated attack mitigation
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize response rules engine"""
        self.db_path = db_path or '/home/hunter/Projekty/ddospot/ddospot.db'
        self.rules: Dict[str, ResponseRule] = {}
        self.rule_execution_count: Dict[str, int] = {}
        self.rule_last_execution: Dict[str, datetime] = {}
        
        logger.info('[Response] Initializing Response Rules Engine')
        self._init_database()
        self._load_rules()
    
    def _init_database(self):
        """Initialize database tables for rules and executions"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Response rules table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS response_rules (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        enabled BOOLEAN DEFAULT 1,
                        conditions JSON NOT NULL,
                        actions JSON NOT NULL,
                        severity TEXT NOT NULL,
                        priority INTEGER,
                        execution_delay INTEGER DEFAULT 0,
                        max_triggers_per_hour INTEGER,
                        active_hours TEXT DEFAULT '24/7',
                        notes TEXT,
                        created_at TIMESTAMP,
                        updated_at TIMESTAMP
                    )
                ''')
                
                # Response execution log
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS response_executions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_id TEXT NOT NULL,
                        threat_ip TEXT,
                        threat_score REAL,
                        triggered_at TIMESTAMP,
                        actions_executed JSON,
                        status TEXT,
                        result TEXT,
                        FOREIGN KEY (rule_id) REFERENCES response_rules(id)
                    )
                ''')
                
                # Response statistics
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS response_statistics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        rule_id TEXT NOT NULL,
                        date TEXT,
                        trigger_count INTEGER DEFAULT 0,
                        action_count INTEGER DEFAULT 0,
                        success_rate REAL DEFAULT 100.0,
                        avg_execution_time REAL DEFAULT 0.0,
                        UNIQUE(rule_id, date),
                        FOREIGN KEY (rule_id) REFERENCES response_rules(id)
                    )
                ''')
                
                conn.commit()
                logger.info('[Response] Database tables initialized')
        
        except sqlite3.Error as e:
            logger.error(f'[Response] Database initialization error: {e}')
    
    def add_rule(self, rule: ResponseRule) -> bool:
        """Add a new response rule"""
        try:
            self.rules[rule.id] = rule
            
            # Persist to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Serialize conditions with operator values
                conditions_json = []
                for c in rule.conditions:
                    conditions_json.append({
                        'field': c.field,
                        'operator': c.operator.value,
                        'value': c.value
                    })
                
                cursor.execute('''
                    INSERT OR REPLACE INTO response_rules
                    (id, name, description, enabled, conditions, actions, 
                     severity, priority, execution_delay, max_triggers_per_hour,
                     active_hours, notes, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule.id,
                    rule.name,
                    rule.description,
                    rule.enabled,
                    json.dumps(conditions_json),
                    json.dumps([a.value for a in rule.actions]),
                    rule.severity.name,
                    rule.priority,
                    rule.execution_delay,
                    rule.max_triggers_per_hour,
                    rule.active_hours,
                    rule.notes,
                    rule.created_at.isoformat() if rule.created_at else None,
                    rule.updated_at.isoformat() if rule.updated_at else None
                ))
                conn.commit()
            
            logger.info(f'[Response] Rule added: {rule.id} - {rule.name}')
            return True
        
        except Exception as e:
            logger.error(f'[Response] Error adding rule: {e}')
            return False
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a response rule"""
        try:
            if rule_id in self.rules:
                del self.rules[rule_id]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM response_rules WHERE id = ?', (rule_id,))
                conn.commit()
            
            logger.info(f'[Response] Rule removed: {rule_id}')
            return True
        
        except Exception as e:
            logger.error(f'[Response] Error removing rule: {e}')
            return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a response rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = True
            self._update_rule_in_db(self.rules[rule_id])
            logger.info(f'[Response] Rule enabled: {rule_id}')
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a response rule"""
        if rule_id in self.rules:
            self.rules[rule_id].enabled = False
            self._update_rule_in_db(self.rules[rule_id])
            logger.info(f'[Response] Rule disabled: {rule_id}')
            return True
        return False
    
    def get_rule(self, rule_id: str) -> Optional[ResponseRule]:
        """Get a specific rule"""
        return self.rules.get(rule_id)
    
    def get_all_rules(self) -> List[ResponseRule]:
        """Get all rules sorted by priority"""
        return sorted(self.rules.values(), key=lambda r: r.priority)
    
    def find_matching_rules(self, threat_data: Dict) -> List[Tuple[ResponseRule, List[ActionType]]]:
        """Find all rules that match threat data"""
        matching = []
        
        for rule in self.get_all_rules():
            if rule.matches(threat_data):
                # Check rate limit
                if self._can_execute_rule(rule):
                    matching.append((rule, rule.actions))
        
        return sorted(matching, key=lambda x: x[0].priority)
    
    def _can_execute_rule(self, rule: ResponseRule) -> bool:
        """Check if rule can be executed (rate limiting)"""
        if rule.max_triggers_per_hour is None:
            return True
        
        # Check execution count in last hour
        count_key = f"{rule.id}_hour"
        executions_this_hour = self.rule_execution_count.get(count_key, 0)
        
        if executions_this_hour >= rule.max_triggers_per_hour:
            logger.warning(f'[Response] Rule {rule.id} rate limit reached')
            return False
        
        return True
    
    def log_execution(self, rule_id: str, threat_ip: str, threat_score: float,
                      actions: List[str], status: str, result: str = "") -> bool:
        """Log rule execution"""
        try:
            # Update execution counters
            count_key = f"{rule_id}_hour"
            self.rule_execution_count[count_key] = self.rule_execution_count.get(count_key, 0) + 1
            self.rule_last_execution[rule_id] = datetime.now()
            
            # Reset hourly counter every hour
            if rule_id in self.rule_last_execution:
                last = self.rule_last_execution[rule_id]
                if (datetime.now() - last).seconds > 3600:
                    self.rule_execution_count[count_key] = 1
            
            # Log to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO response_executions
                    (rule_id, threat_ip, threat_score, triggered_at, 
                     actions_executed, status, result)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    rule_id,
                    threat_ip,
                    threat_score,
                    datetime.now().isoformat(),
                    json.dumps(actions),
                    status,
                    result
                ))
                conn.commit()
            
            logger.info(f'[Response] Execution logged: {rule_id} for {threat_ip} - {status}')
            return True
        
        except Exception as e:
            logger.error(f'[Response] Error logging execution: {e}')
            return False
    
    def get_execution_history(self, rule_id: Optional[str] = None, 
                              limit: int = 100) -> List[Dict]:
        """Get execution history"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if rule_id:
                    cursor.execute('''
                        SELECT * FROM response_executions 
                        WHERE rule_id = ? 
                        ORDER BY triggered_at DESC 
                        LIMIT ?
                    ''', (rule_id, limit))
                else:
                    cursor.execute('''
                        SELECT * FROM response_executions 
                        ORDER BY triggered_at DESC 
                        LIMIT ?
                    ''', (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f'[Response] Error retrieving execution history: {e}')
            return []
    
    def get_statistics(self, rule_id: Optional[str] = None,
                       days: int = 7) -> Dict:
        """Get response statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                stats = {
                    'total_rules': len(self.rules),
                    'enabled_rules': sum(1 for r in self.rules.values() if r.enabled),
                    'period_days': days,
                    'executions': 0,
                    'actions_taken': 0,
                    'average_response_time': 0.0
                }
                
                # Query execution stats
                date_limit = (datetime.now() - timedelta(days=days)).isoformat()
                
                cursor.execute('''
                    SELECT COUNT(*) as count FROM response_executions
                    WHERE triggered_at > ?
                ''', (date_limit,))
                
                result = cursor.fetchone()
                if result:
                    stats['executions'] = result['count']
                
                return stats
        
        except Exception as e:
            logger.error(f'[Response] Error retrieving statistics: {e}')
            return {}
    
    def _load_rules(self):
        """Load rules from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM response_rules')
                rows = cursor.fetchall()
                
                for row in rows:
                    try:
                        conditions_data = json.loads(row['conditions'])
                        conditions = [
                            RuleCondition(
                                field=c['field'],
                                operator=RuleOperator(c['operator']),
                                value=c['value']
                            )
                            for c in conditions_data
                        ]
                        
                        actions = [
                            ActionType(a) for a in json.loads(row['actions'])
                        ]
                        
                        rule = ResponseRule(
                            id=row['id'],
                            name=row['name'],
                            description=row['description'],
                            enabled=row['enabled'],
                            conditions=conditions,
                            actions=actions,
                            severity=SeverityLevel[row['severity']],
                            priority=row['priority'],
                            execution_delay=row['execution_delay'],
                            max_triggers_per_hour=row['max_triggers_per_hour'],
                            active_hours=row['active_hours'],
                            notes=row['notes'],
                            created_at=datetime.fromisoformat(row['created_at']),
                            updated_at=datetime.fromisoformat(row['updated_at'])
                        )
                        
                        self.rules[rule.id] = rule
                    
                    except Exception as e:
                        logger.error(f'[Response] Error loading rule: {e}')
                
                logger.info(f'[Response] Loaded {len(self.rules)} rules from database')
        
        except Exception as e:
            logger.error(f'[Response] Error loading rules: {e}')
    
    def _update_rule_in_db(self, rule: ResponseRule):
        """Update rule in database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE response_rules 
                    SET enabled = ?, updated_at = ?
                    WHERE id = ?
                ''', (rule.enabled, datetime.now().isoformat(), rule.id))
                conn.commit()
        except Exception as e:
            logger.error(f'[Response] Error updating rule: {e}')

# ============================================================================
# DEFAULT RULES
# ============================================================================

def get_default_rules() -> List[ResponseRule]:
    """Create default response rules"""
    
    rules = []
    
    # Rule 1: Block Critical Threats
    rules.append(ResponseRule(
        id='RULE_001',
        name='Block Critical Threats',
        description='Automatically block IPs with critical threat score',
        enabled=True,
        conditions=[
            RuleCondition(
                field='threat_score',
                operator=RuleOperator.GREATER_EQUAL,
                value=80
            ),
            RuleCondition(
                field='confidence',
                operator=RuleOperator.GREATER_EQUAL,
                value=85
            )
        ],
        actions=[ActionType.BLOCK_IP, ActionType.ALERT, ActionType.INCIDENT],
        severity=SeverityLevel.CRITICAL,
        priority=1,
        execution_delay=0,
        max_triggers_per_hour=100,
        notes='Immediate blocking for confirmed threats'
    ))
    
    # Rule 2: Alert on High Threats
    rules.append(ResponseRule(
        id='RULE_002',
        name='Alert on High Threats',
        description='Send alert for high-threat IPs',
        enabled=True,
        conditions=[
            RuleCondition(
                field='threat_score',
                operator=RuleOperator.GREATER_EQUAL,
                value=60
            ),
            RuleCondition(
                field='threat_score',
                operator=RuleOperator.LESS_THAN,
                value=80
            )
        ],
        actions=[ActionType.ALERT, ActionType.LOG],
        severity=SeverityLevel.HIGH,
        priority=2,
        execution_delay=0,
        max_triggers_per_hour=500,
        notes='Alert for review, no automatic blocking'
    ))
    
    # Rule 3: Rate Limit Medium Threats
    rules.append(ResponseRule(
        id='RULE_003',
        name='Rate Limit Medium Threats',
        description='Apply rate limiting to medium-threat IPs',
        enabled=True,
        conditions=[
            RuleCondition(
                field='threat_score',
                operator=RuleOperator.GREATER_EQUAL,
                value=40
            ),
            RuleCondition(
                field='threat_score',
                operator=RuleOperator.LESS_THAN,
                value=60
            )
        ],
        actions=[ActionType.RATE_LIMIT, ActionType.LOG],
        severity=SeverityLevel.MEDIUM,
        priority=3,
        execution_delay=0,
        max_triggers_per_hour=1000,
        notes='Rate limiting without full blocking'
    ))
    
    # Rule 4: Block Botnet IPs
    rules.append(ResponseRule(
        id='RULE_004',
        name='Block Botnet IPs',
        description='Automatically block confirmed botnet IPs',
        enabled=True,
        conditions=[
            RuleCondition(
                field='threat_type',
                operator=RuleOperator.CONTAINS,
                value='botnet'
            )
        ],
        actions=[ActionType.BLOCK_IP, ActionType.ALERT, ActionType.INCIDENT],
        severity=SeverityLevel.CRITICAL,
        priority=1,
        execution_delay=0,
        max_triggers_per_hour=200,
        notes='Botnet detection - immediate blocking'
    ))
    
    # Rule 5: Log All Threats
    rules.append(ResponseRule(
        id='RULE_005',
        name='Log All Threats',
        description='Log all detected threats for analysis',
        enabled=True,
        conditions=[
            RuleCondition(
                field='threat_score',
                operator=RuleOperator.GREATER_THAN,
                value=0
            )
        ],
        actions=[ActionType.LOG],
        severity=SeverityLevel.INFO,
        priority=10,
        execution_delay=0,
        max_triggers_per_hour=None,
        notes='Comprehensive logging of all threats'
    ))
    
    return rules

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_response_engine = None

def get_response_engine() -> ResponseRulesEngine:
    """Get singleton response rules engine instance"""
    global _response_engine
    
    if _response_engine is None:
        _response_engine = ResponseRulesEngine()
    
    return _response_engine
