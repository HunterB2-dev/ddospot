"""
Alert and notification system for DDoSPot honeypot.
Supports email, Discord webhooks, and custom integrations.
"""

import smtplib
import json
import time
import sqlite3
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from urllib.request import Request, urlopen
from urllib.error import URLError

from telemetry.logger import get_logger

logger = get_logger(__name__)


class AlertConfig:
    """Alert configuration manager"""
    
    def __init__(self, config_file: str = 'config/alert_config.json'):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            # Return default config
            return self._get_default_config()
        except Exception as e:
            logger.error(f'Failed to load alert config: {e}')
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict:
        """Get default alert configuration"""
        return {
            'enabled': True,
            'email': {
                'enabled': False,
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'sender': '',
                'password': '',
                'recipients': [],
                'use_tls': True
            },
            'discord': {
                'enabled': False,
                'webhook_url': ''
            },
            'telegram': {
                'enabled': False,
                'bot_token': '',
                'chat_id': ''
            },
            'alerts': {
                'critical_attack': True,
                'ip_blacklisted': True,
                'sustained_attack': True,
                'multi_protocol': True
            },
            'throttle': {
                'enabled': True,
                'min_interval_seconds': 300  # 5 minutes
            }
        }
    
    def save(self) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            logger.info(f'Alert config saved to {self.config_file}')
            return True
        except Exception as e:
            logger.error(f'Failed to save alert config: {e}')
            return False
    
    def get(self, key: str, default=None):
        """Get config value by key (supports nested with dots)"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
        return value if value is not None else default
    
    def set(self, key: str, value):
        """Set config value by key (supports nested with dots)"""
        keys = key.split('.')
        config = self.config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value
        self.save()


class EmailAlert:
    """Email alert sender"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
    
    def send(self, subject: str, message: str, html: Optional[str] = None) -> bool:
        """Send email alert"""
        if not self.config.get('email.enabled'):
            return False
        
        try:
            sender = str(self.config.get('email.sender', ''))
            password = str(self.config.get('email.password', ''))
            recipients_data = self.config.get('email.recipients', [])
            recipients = list(recipients_data) if recipients_data else []
            
            if not sender or not password or not recipients:
                logger.warning('Email alert not configured properly')
                return False
            
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = sender
            msg['To'] = ', '.join(recipients)
            
            # Add plain text version
            msg.attach(MIMEText(message, 'plain'))
            
            # Add HTML version if provided
            if html:
                msg.attach(MIMEText(html, 'html'))
            
            # Send email
            smtp_server = str(self.config.get('email.smtp_server', ''))
            smtp_port_val = self.config.get('email.smtp_port', 587)
            smtp_port = int(smtp_port_val) if isinstance(smtp_port_val, (int, str)) else 587
            use_tls_val = self.config.get('email.use_tls', True)
            use_tls = bool(use_tls_val) if use_tls_val is not None else True
            
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
            
            server.login(sender, password)
            server.sendmail(sender, recipients, msg.as_string())
            server.quit()
            
            logger.info(f'Email alert sent: {subject}')
            return True
        except Exception as e:
            logger.error(f'Failed to send email alert: {e}')
            return False


class DiscordAlert:
    """Discord webhook alert sender"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
    
    def send(self, title: str, message: str, color: int = 0xff3333, fields: Optional[List[Dict]] = None) -> bool:
        """Send Discord alert via webhook"""
        if not self.config.get('discord.enabled'):
            return False
        
        try:
            webhook_url = str(self.config.get('discord.webhook_url', ''))
            if not webhook_url:
                logger.warning('Discord webhook not configured')
                return False
            
            # Build embed
            embed = {
                'title': title,
                'description': message,
                'color': color,
                'timestamp': datetime.utcnow().isoformat(),
            }
            
            if fields:
                embed['fields'] = fields
            
            payload = {
                'embeds': [embed]
            }
            
            # Send to Discord
            req = Request(
                webhook_url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            response = urlopen(req)
            response.read()
            response.close()
            
            logger.info(f'Discord alert sent: {title}')
            return True
        except URLError as e:
            logger.error(f'Failed to send Discord alert: {e}')
            return False
        except Exception as e:
            logger.error(f'Discord alert error: {e}')
            return False


class TelegramAlert:
    """Telegram bot alert sender"""
    
    def __init__(self, config: AlertConfig):
        self.config = config
    
    def send(self, title: str, message: str, fields: Optional[List[Dict]] = None) -> bool:
        """Send Telegram alert via bot"""
        if not self.config.get('telegram.enabled'):
            return False
        
        try:
            bot_token = str(self.config.get('telegram.bot_token', ''))
            chat_id = str(self.config.get('telegram.chat_id', ''))
            
            if not bot_token or not chat_id:
                logger.warning('Telegram bot token or chat ID not configured')
                return False
            
            # Build message
            text = f"🚨 *{title}*\n\n{message}"
            
            if fields:
                for field in fields:
                    name = field.get('name', 'Field')
                    value = field.get('value', 'N/A')
                    text += f"\n\n📊 *{name}:* `{value}`"
            
            text += f"\n\n⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            
            # Send via Telegram API
            url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
            payload = {
                'chat_id': chat_id,
                'text': text,
                'parse_mode': 'Markdown'
            }
            
            req = Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            response = urlopen(req, timeout=10)
            response.read()
            response.close()
            
            logger.info(f'Telegram alert sent: {title}')
            return True
        except URLError as e:
            logger.error(f'Failed to send Telegram alert: {e}')
            return False
        except Exception as e:
            logger.error(f'Telegram alert error: {e}')
            return False


class AlertThrottler:
    """Smart alert throttling to prevent spam"""
    
    def __init__(self, db_path: str = 'honeypot.db'):
        self.db_path = db_path
        self.memory_cache = {}  # Fast in-memory cache
        self._init_db()
    
    def _init_db(self):
        """Initialize alert history table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS alert_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    alert_type TEXT NOT NULL,
                    ip TEXT,
                    severity TEXT,
                    message TEXT,
                    sent BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_alert_type 
                ON alert_history(alert_type, created_at)
            ''')
            
            conn.commit()
            conn.close()
            logger.info('Alert history table initialized')
        except Exception as e:
            logger.error(f'Failed to initialize alert history: {e}')
    
    def should_alert(self, alert_type: str, ip: Optional[str] = None, min_interval_seconds: int = 300) -> bool:
        """Check if alert should be sent (throttling)"""
        cache_key = f'{alert_type}:{ip}'
        now = time.time()
        
        # Check memory cache first (fastest)
        if cache_key in self.memory_cache:
            last_alert_time = self.memory_cache[cache_key]
            if now - last_alert_time < min_interval_seconds:
                return False
        
        # Update memory cache
        self.memory_cache[cache_key] = now
        
        # Store in database for persistence
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT created_at FROM alert_history 
                WHERE alert_type = ? AND (ip = ? OR ip IS NULL)
                ORDER BY created_at DESC LIMIT 1
            ''', (alert_type, ip))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                last_time = datetime.fromisoformat(result[0])
                if datetime.now() - last_time < timedelta(seconds=min_interval_seconds):
                    return False
        except Exception as e:
            logger.error(f'Throttle check error: {e}')
        
        return True
    
    def log_alert(self, alert_type: str, severity: str, message: str, ip: Optional[str] = None, sent: bool = True):
        """Log alert to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO alert_history (alert_type, severity, message, ip, sent)
                VALUES (?, ?, ?, ?, ?)
            ''', (alert_type, severity, message, ip, sent))
            
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f'Failed to log alert: {e}')
    
    def get_recent_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts from history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT id, alert_type, ip, severity, message, sent, created_at
                FROM alert_history
                ORDER BY created_at DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'id': row[0],
                    'type': row[1],
                    'ip': row[2],
                    'severity': row[3],
                    'message': row[4],
                    'sent': bool(row[5]),
                    'timestamp': row[6]
                }
                for row in rows
            ]
        except Exception as e:
            logger.error(f'Failed to get alerts: {e}')
            return []


class AlertManager:
    """Main alert manager coordinating all alert channels"""
    
    def __init__(self, db_path: str = 'logs/honeypot.db', config_file: str = 'config/alert_config.json'):
        self.config = AlertConfig(config_file)
        self.throttler = AlertThrottler(db_path)
        self.email = EmailAlert(self.config)
        self.discord = DiscordAlert(self.config)
        self.telegram = TelegramAlert(self.config)
    
    def send_alert(self, alert_type: str, severity: str, title: str, message: str, 
                   ip: Optional[str] = None, fields: Optional[List[Dict]] = None) -> bool:
        """Send alert through all configured channels"""
        if not self.config.get('enabled'):
            return False
        
        # Check if alert type is enabled
        if not self.config.get(f'alerts.{alert_type}', True):
            logger.debug(f'Alert type {alert_type} is disabled')
            return False
        
        # Check throttling
        min_interval_val = self.config.get('throttle.min_interval_seconds', 300)
        min_interval = int(min_interval_val) if isinstance(min_interval_val, (int, str)) else 300
        if not self.throttler.should_alert(alert_type, ip, min_interval):
            logger.debug(f'Alert throttled: {alert_type} for {ip}')
            self.throttler.log_alert(alert_type, severity, message, ip, sent=False)
            return False
        
        # Send through all enabled channels
        sent = False
        
        # Email alert
        if self.config.get('email.enabled'):
            html_message = self._build_html_message(title, message, fields)
            if self.email.send(title, message, html_message):
                sent = True
        
        # Discord alert
        if self.config.get('discord.enabled'):
            color = self._get_color_for_severity(severity)
            if self.discord.send(title, message, color, fields):
                sent = True
        
        # Telegram alert
        if self.config.get('telegram.enabled'):
            if self.telegram.send(title, message, fields):
                sent = True
        
        # Log to database
        self.throttler.log_alert(alert_type, severity, message, ip, sent=sent)
        
        return sent
    
    def _build_html_message(self, title: str, message: str, fields: Optional[List[Dict]] = None) -> str:
        """Build HTML email message"""
        html = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <h2 style="color: #ff3333;">🚨 {title}</h2>
                <p>{message}</p>
        """
        
        if fields:
            html += '<table style="border-collapse: collapse;">'
            for field in fields:
                html += f"""
                <tr>
                    <td style="padding: 8px; border: 1px solid #ddd;"><strong>{field.get('name', 'N/A')}</strong></td>
                    <td style="padding: 8px; border: 1px solid #ddd;">{field.get('value', 'N/A')}</td>
                </tr>
                """
            html += '</table>'
        
        html += """
                <hr>
                <p style="color: #666; font-size: 12px;">DDoSPot Honeypot Alert System</p>
            </body>
        </html>
        """
        return html
    
    def _get_color_for_severity(self, severity: str) -> int:
        """Get Discord embed color for severity"""
        colors = {
            'low': 0x3498db,      # Blue
            'medium': 0xf39c12,   # Orange
            'high': 0xe74c3c,     # Red
            'critical': 0xc0392b  # Dark Red
        }
        return colors.get(severity.lower(), 0xff3333)
    
    def alert_critical_attack(self, ip: str, severity: str, event_count: int, protocols: List[str]):
        """Send critical attack alert"""
        title = f'🚨 Critical Attack Detected: {ip}'
        message = f'A critical DDoS attack has been detected from {ip} with {event_count} events using {", ".join(protocols)} protocol(s).'
        
        fields = [
            {'name': 'Attacker IP', 'value': ip},
            {'name': 'Event Count', 'value': str(event_count)},
            {'name': 'Protocols', 'value': ', '.join(protocols)},
            {'name': 'Severity', 'value': severity.upper()},
            {'name': 'Timestamp', 'value': datetime.now().isoformat()}
        ]
        
        return self.send_alert('critical_attack', severity, title, message, ip, fields)
    
    def alert_ip_blacklisted(self, ip: str, reason: str, severity: str):
        """Send IP blacklist alert"""
        title = f'🚫 IP Blacklisted: {ip}'
        message = f'IP address {ip} has been automatically blacklisted due to {reason} attack.'
        
        fields = [
            {'name': 'IP Address', 'value': ip},
            {'name': 'Reason', 'value': reason},
            {'name': 'Severity', 'value': severity.upper()},
            {'name': 'Timestamp', 'value': datetime.now().isoformat()}
        ]
        
        return self.send_alert('ip_blacklisted', severity, title, message, ip, fields)
    
    def alert_sustained_attack(self, duration_minutes: int, event_count: int):
        """Send sustained attack alert"""
        title = f'⚠️ Sustained Attack Ongoing ({duration_minutes}m)'
        message = f'A sustained attack has been ongoing for {duration_minutes} minutes with {event_count} total events detected.'
        
        fields = [
            {'name': 'Duration', 'value': f'{duration_minutes} minutes'},
            {'name': 'Event Count', 'value': str(event_count)},
            {'name': 'Timestamp', 'value': datetime.now().isoformat()}
        ]
        
        return self.send_alert('sustained_attack', 'high', title, message, fields=fields)
    
    def get_alert_history(self, limit: int = 50) -> List[Dict]:
        """Get alert history"""
        return self.throttler.get_recent_alerts(limit)


# Global instance
_alert_manager = None

def get_alert_manager(db_path: str = 'logs/honeypot.db', config_file: str = 'config/alert_config.json') -> AlertManager:
    """Get or create alert manager instance"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager(db_path, config_file)
    return _alert_manager
