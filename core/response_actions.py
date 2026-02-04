"""
Automated Response Actions for Threat Mitigation
Handles IP blocking, rate limiting, WAF updates, and firewall integration
"""

import json
import logging
import subprocess
import asyncio
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass
import sqlite3

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & TYPES
# ============================================================================

class FirewallType(Enum):
    """Supported firewall types"""
    IPTABLES = "iptables"
    UFW = "ufw"
    AWS_SECURITY_GROUP = "aws_sg"
    CLOUDFLARE_WAF = "cloudflare_waf"
    AZURE_NSG = "azure_nsg"

class ActionStatus(Enum):
    """Action execution status"""
    PENDING = "pending"
    EXECUTING = "executing"
    SUCCESS = "success"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class BlockAction:
    """IP block action"""
    ip_address: str
    reason: str
    duration: int  # seconds, 0 = permanent
    priority: int = 1
    timestamp: Optional[datetime] = None
    expiry: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if self.duration > 0:
            self.expiry = self.timestamp + timedelta(seconds=self.duration)

@dataclass
class RateLimitAction:
    """Rate limit action"""
    ip_address: str
    requests_per_second: int
    duration: int  # seconds
    timestamp: Optional[datetime] = None
    expiry: Optional[datetime] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        
        if self.duration > 0:
            self.expiry = self.timestamp + timedelta(seconds=self.duration)

# ============================================================================
# FIREWALL HANDLERS
# ============================================================================

class IptablesHandler:
    """Handle iptables firewall rules"""
    
    @staticmethod
    def block_ip(ip: str) -> Tuple[bool, str]:
        """Block IP using iptables"""
        try:
            # Add to INPUT chain
            cmd = ['sudo', 'iptables', '-I', 'INPUT', '1', 
                   '-s', ip, '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode != 0:
                error = result.stderr.decode()
                logger.error(f'[Response] Iptables block error: {error}')
                return False, error
            
            logger.info(f'[Response] IP blocked with iptables: {ip}')
            return True, 'IP blocked'
        
        except Exception as e:
            logger.error(f'[Response] Iptables error: {e}')
            return False, str(e)
    
    @staticmethod
    def unblock_ip(ip: str) -> Tuple[bool, str]:
        """Unblock IP using iptables"""
        try:
            cmd = ['sudo', 'iptables', '-D', 'INPUT', 
                   '-s', ip, '-j', 'DROP']
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode != 0:
                logger.warning(f'[Response] Iptables unblock warning: {result.stderr.decode()}')
                return False, 'IP not found in rules'
            
            logger.info(f'[Response] IP unblocked with iptables: {ip}')
            return True, 'IP unblocked'
        
        except Exception as e:
            logger.error(f'[Response] Iptables unblock error: {e}')
            return False, str(e)
    
    @staticmethod
    def save_rules() -> bool:
        """Save iptables rules to persist across reboot"""
        try:
            # Try iptables-save (Debian/Ubuntu)
            cmd = ['sudo', 'iptables-save', '|', 'sudo', 'tee', 
                   '/etc/iptables/rules.v4']
            subprocess.run(cmd, capture_output=True, timeout=10, shell=True)
            
            logger.info('[Response] Iptables rules saved')
            return True
        
        except Exception as e:
            logger.warning(f'[Response] Iptables save warning: {e}')
            return False

class UFWHandler:
    """Handle UFW (Uncomplicated Firewall) rules"""
    
    @staticmethod
    def block_ip(ip: str) -> Tuple[bool, str]:
        """Block IP using UFW"""
        try:
            cmd = ['sudo', 'ufw', 'insert', '1', 'deny', 'from', ip]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode != 0:
                error = result.stderr.decode()
                logger.error(f'[Response] UFW block error: {error}')
                return False, error
            
            logger.info(f'[Response] IP blocked with UFW: {ip}')
            return True, 'IP blocked'
        
        except Exception as e:
            logger.error(f'[Response] UFW error: {e}')
            return False, str(e)
    
    @staticmethod
    def unblock_ip(ip: str) -> Tuple[bool, str]:
        """Unblock IP using UFW"""
        try:
            cmd = ['sudo', 'ufw', 'delete', 'deny', 'from', ip]
            result = subprocess.run(cmd, capture_output=True, timeout=10)
            
            if result.returncode != 0:
                logger.warning(f'[Response] UFW unblock warning: {result.stderr.decode()}')
                return False, 'IP not found in rules'
            
            logger.info(f'[Response] IP unblocked with UFW: {ip}')
            return True, 'IP unblocked'
        
        except Exception as e:
            logger.error(f'[Response] UFW unblock error: {e}')
            return False, str(e)

class CloudflareWAFHandler:
    """Handle Cloudflare WAF rules"""
    
    def __init__(self, config: Dict):
        """Initialize Cloudflare handler"""
        self.api_token = config.get('api_token', '')
        self.zone_id = config.get('zone_id', '')
        self.list_id = config.get('list_id', '')
    
    async def block_ip(self, ip: str) -> Tuple[bool, str]:
        """Block IP using Cloudflare WAF"""
        if not self.api_token or not self.zone_id:
            logger.warning('[Response] Cloudflare credentials not configured')
            return False, 'Cloudflare not configured'
        
        try:
            import aiohttp  # type: ignore
        except ImportError:
            logger.error('[Response] aiohttp not installed. Cannot use Cloudflare integration.')
            return False, 'aiohttp not installed'
        
        try:
            
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            # Add to WAF rule
            url = f'https://api.cloudflare.com/client/v4/zones/{self.zone_id}/firewall/access_rules/rules'
            
            payload = {
                'mode': 'block',
                'configuration': {
                    'target': 'ip',
                    'value': ip
                },
                'priority': 1,
                'notes': 'DDoSSpot auto-block'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f'[Response] IP blocked with Cloudflare: {ip}')
                        return True, 'IP blocked'
                    else:
                        error = await response.text()
                        logger.error(f'[Response] Cloudflare error: {error}')
                        return False, error
        
        except Exception as e:
            logger.error(f'[Response] Cloudflare error: {e}')
            return False, str(e)

class AWSSecurityGroupHandler:
    """Handle AWS Security Group rules"""
    
    def __init__(self, config: Dict):
        """Initialize AWS handler"""
        self.sg_id = config.get('security_group_id', '')
        self.region = config.get('region', 'us-east-1')
    
    def block_ip(self, ip: str) -> Tuple[bool, str]:
        """Block IP using AWS Security Group"""
        if not self.sg_id:
            logger.warning('[Response] AWS Security Group ID not configured')
            return False, 'AWS not configured'
        
        try:
            import boto3  # type: ignore
        except ImportError:
            logger.error('[Response] boto3 not installed. Cannot use AWS integration.')
            return False, 'boto3 not installed'
        
        try:
            
            ec2 = boto3.client('ec2', region_name=self.region)
            
            ec2.authorize_security_group_ingress(
                GroupId=self.sg_id,
                IpPermissions=[
                    {
                        'IpProtocol': '-1',
                        'FromPort': -1,
                        'ToPort': -1,
                        'IpRanges': [{'CidrIp': f'{ip}/32', 'Description': 'DDoSSpot block'}]
                    }
                ]
            )
            
            logger.info(f'[Response] IP blocked with AWS SG: {ip}')
            return True, 'IP blocked'
        
        except Exception as e:
            logger.error(f'[Response] AWS error: {e}')
            return False, str(e)

# ============================================================================
# RESPONSE ACTIONS ENGINE
# ============================================================================

class ResponseActionsEngine:
    """
    Executes automated response actions
    """
    
    def __init__(self, db_path: Optional[str] = None, config: Optional[Dict] = None):
        """Initialize response actions engine"""
        self.db_path = db_path or '/home/hunter/Projekty/ddospot/ddospot.db'
        self.config = config or {}
        self.blocked_ips: Dict[str, BlockAction] = {}
        self.rate_limited_ips: Dict[str, RateLimitAction] = {}
        self.firewall_handlers = {}
        
        logger.info('[Response] Initializing Response Actions Engine')
        self._init_database()
        self._init_handlers()
        self._load_blocked_ips()
    
    def _init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Blocked IPs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS blocked_ips (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ip_address TEXT UNIQUE,
                        reason TEXT,
                        duration INTEGER,
                        priority INTEGER DEFAULT 1,
                        blocked_at TIMESTAMP,
                        expires_at TIMESTAMP,
                        firewall_type TEXT,
                        status TEXT
                    )
                ''')
                
                # Rate limited IPs table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS rate_limited_ips (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        ip_address TEXT UNIQUE,
                        requests_per_second INTEGER,
                        duration INTEGER,
                        limited_at TIMESTAMP,
                        expires_at TIMESTAMP,
                        status TEXT
                    )
                ''')
                
                # Action execution log
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS action_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        action_type TEXT,
                        target_ip TEXT,
                        status TEXT,
                        result TEXT,
                        executed_at TIMESTAMP
                    )
                ''')
                
                conn.commit()
                logger.info('[Response] Database tables initialized')
        
        except sqlite3.Error as e:
            logger.error(f'[Response] Database error: {e}')
    
    def _init_handlers(self):
        """Initialize firewall handlers"""
        fw_config = self.config.get('firewall', {})
        
        if fw_config.get('iptables', {}).get('enabled'):
            self.firewall_handlers['iptables'] = IptablesHandler()
            logger.info('[Response] Iptables handler initialized')
        
        if fw_config.get('ufw', {}).get('enabled'):
            self.firewall_handlers['ufw'] = UFWHandler()
            logger.info('[Response] UFW handler initialized')
        
        if fw_config.get('cloudflare', {}).get('enabled'):
            self.firewall_handlers['cloudflare'] = CloudflareWAFHandler(fw_config['cloudflare'])
            logger.info('[Response] Cloudflare handler initialized')
        
        if fw_config.get('aws', {}).get('enabled'):
            self.firewall_handlers['aws'] = AWSSecurityGroupHandler(fw_config['aws'])
            logger.info('[Response] AWS handler initialized')
    
    def block_ip(self, action: BlockAction) -> Tuple[bool, str]:
        """Block an IP address"""
        try:
            # Check if already blocked
            if action.ip_address in self.blocked_ips:
                logger.warning(f'[Response] IP already blocked: {action.ip_address}')
                return True, 'IP already blocked'
            
            success_count = 0
            results = []
            
            # Execute on all configured firewalls
            for fw_name, handler in self.firewall_handlers.items():
                try:
                    if fw_name == 'cloudflare':
                        # Async handler
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            asyncio.create_task(handler.block_ip(action.ip_address))
                            success_count += 1
                        else:
                            success, msg = loop.run_until_complete(handler.block_ip(action.ip_address))
                            if success:
                                success_count += 1
                            results.append(f'{fw_name}: {msg}')
                    else:
                        success, msg = handler.block_ip(action.ip_address)
                        if success:
                            success_count += 1
                        results.append(f'{fw_name}: {msg}')
                
                except Exception as e:
                    results.append(f'{fw_name}: {str(e)}')
            
            if success_count > 0:
                # Store in memory and database
                self.blocked_ips[action.ip_address] = action
                self._save_blocked_ip(action)
                
                msg = f'IP blocked on {success_count} firewall(s): {", ".join(results)}'
                logger.info(f'[Response] {msg}')
                return True, msg
            else:
                msg = f'Failed to block on any firewall: {", ".join(results)}'
                logger.warning(f'[Response] {msg}')
                return False, msg
        
        except Exception as e:
            logger.error(f'[Response] Block IP error: {e}')
            return False, str(e)
    
    def unblock_ip(self, ip_address: str) -> Tuple[bool, str]:
        """Unblock an IP address"""
        try:
            if ip_address not in self.blocked_ips:
                logger.warning(f'[Response] IP not blocked: {ip_address}')
                return False, 'IP not found in blocked list'
            
            success_count = 0
            results = []
            
            # Execute on all configured firewalls
            for fw_name, handler in self.firewall_handlers.items():
                try:
                    success, msg = handler.unblock_ip(ip_address)
                    if success:
                        success_count += 1
                    results.append(f'{fw_name}: {msg}')
                
                except Exception as e:
                    results.append(f'{fw_name}: {str(e)}')
            
            # Remove from memory and database
            del self.blocked_ips[ip_address]
            self._remove_blocked_ip(ip_address)
            
            msg = f'IP unblocked on {success_count} firewall(s): {", ".join(results)}'
            logger.info(f'[Response] {msg}')
            return True, msg
        
        except Exception as e:
            logger.error(f'[Response] Unblock IP error: {e}')
            return False, str(e)
    
    def rate_limit_ip(self, action: RateLimitAction) -> Tuple[bool, str]:
        """Apply rate limiting to an IP"""
        try:
            if action.ip_address in self.rate_limited_ips:
                logger.warning(f'[Response] IP already rate limited: {action.ip_address}')
                return True, 'IP already rate limited'
            
            # Store rate limit
            self.rate_limited_ips[action.ip_address] = action
            
            # Save to database
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO rate_limited_ips
                    (ip_address, requests_per_second, duration, limited_at, 
                     expires_at, status)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    action.ip_address,
                    action.requests_per_second,
                    action.duration,
                    action.timestamp.isoformat() if action.timestamp else None,
                    action.expiry.isoformat() if action.expiry else None,
                    'active'
                ))
                conn.commit()
            
            logger.info(f'[Response] Rate limit applied: {action.ip_address} - {action.requests_per_second} req/s')
            return True, 'Rate limit applied'
        
        except Exception as e:
            logger.error(f'[Response] Rate limit error: {e}')
            return False, str(e)
    
    def remove_rate_limit(self, ip_address: str) -> Tuple[bool, str]:
        """Remove rate limiting from an IP"""
        try:
            if ip_address not in self.rate_limited_ips:
                return False, 'IP not found in rate limit list'
            
            del self.rate_limited_ips[ip_address]
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM rate_limited_ips WHERE ip_address = ?',
                    (ip_address,)
                )
                conn.commit()
            
            logger.info(f'[Response] Rate limit removed: {ip_address}')
            return True, 'Rate limit removed'
        
        except Exception as e:
            logger.error(f'[Response] Remove rate limit error: {e}')
            return False, str(e)
    
    def get_blocked_ips(self) -> List[Dict]:
        """Get list of blocked IPs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM blocked_ips 
                    WHERE expires_at IS NULL OR expires_at > ?
                    ORDER BY blocked_at DESC
                ''', (datetime.now().isoformat(),))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f'[Response] Error getting blocked IPs: {e}')
            return []
    
    def get_rate_limited_ips(self) -> List[Dict]:
        """Get list of rate-limited IPs"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM rate_limited_ips 
                    WHERE expires_at IS NULL OR expires_at > ?
                    ORDER BY limited_at DESC
                ''', (datetime.now().isoformat(),))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        
        except Exception as e:
            logger.error(f'[Response] Error getting rate limited IPs: {e}')
            return []
    
    def cleanup_expired_blocks(self) -> int:
        """Remove expired IP blocks"""
        try:
            count = 0
            expired = [
                ip for ip, action in self.blocked_ips.items()
                if action.expiry and action.expiry < datetime.now()
            ]
            
            for ip in expired:
                self.unblock_ip(ip)
                count += 1
            
            logger.info(f'[Response] Cleaned up {count} expired blocks')
            return count
        
        except Exception as e:
            logger.error(f'[Response] Cleanup error: {e}')
            return 0
    
    def _save_blocked_ip(self, action: BlockAction):
        """Save blocked IP to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO blocked_ips
                    (ip_address, reason, duration, priority, blocked_at, 
                     expires_at, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (
                    action.ip_address,
                    action.reason,
                    action.duration,
                    action.priority,
                    action.timestamp.isoformat() if action.timestamp else None,
                    action.expiry.isoformat() if action.expiry else None,
                    'active'
                ))
                conn.commit()
        
        except Exception as e:
            logger.error(f'[Response] Error saving blocked IP: {e}')
    
    def _remove_blocked_ip(self, ip_address: str):
        """Remove blocked IP from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    'DELETE FROM blocked_ips WHERE ip_address = ?',
                    (ip_address,)
                )
                conn.commit()
        
        except Exception as e:
            logger.error(f'[Response] Error removing blocked IP: {e}')
    
    def _load_blocked_ips(self):
        """Load blocked IPs from database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT * FROM blocked_ips
                    WHERE status = 'active' AND 
                    (expires_at IS NULL OR expires_at > ?)
                ''', (datetime.now().isoformat(),))
                
                rows = cursor.fetchall()
                for row in rows:
                    action = BlockAction(
                        ip_address=row['ip_address'],
                        reason=row['reason'],
                        duration=row['duration'],
                        priority=row['priority'],
                        timestamp=datetime.fromisoformat(row['blocked_at'])
                    )
                    
                    if row['expires_at']:
                        action.expiry = datetime.fromisoformat(row['expires_at'])
                    
                    self.blocked_ips[action.ip_address] = action
                
                logger.info(f'[Response] Loaded {len(self.blocked_ips)} blocked IPs')
        
        except Exception as e:
            logger.error(f'[Response] Error loading blocked IPs: {e}')

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_response_actions = None

def get_response_actions(config: Optional[Dict] = None) -> ResponseActionsEngine:
    """Get singleton response actions engine instance"""
    global _response_actions
    
    if _response_actions is None:
        _response_actions = ResponseActionsEngine(config=config)
    
    return _response_actions
