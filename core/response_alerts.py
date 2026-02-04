"""
Alert Notification System for Response Alerts
Handles email, webhooks, dashboard alerts, SMS, and Slack notifications
"""

import json
import logging
import smtplib
import asyncio
try:
    import aiohttp  # type: ignore
except ImportError:
    aiohttp = None
from typing import Dict, List, Optional, Callable
from datetime import datetime
from enum import Enum
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & TYPES
# ============================================================================

class NotificationChannel(Enum):
    """Notification delivery channels"""
    EMAIL = "email"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    SMS = "sms"
    SLACK = "slack"

class AlertLevel(Enum):
    """Alert severity levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class NotificationConfig:
    """Configuration for a notification channel"""
    channel: NotificationChannel
    enabled: bool
    config: Dict
    retry_count: int = 3
    retry_delay: int = 5  # seconds

@dataclass
class Alert:
    """Alert notification object"""
    id: str
    level: AlertLevel
    title: str
    message: str
    threat_data: Dict
    rule_id: str
    timestamp: Optional[datetime] = None
    delivered_to: Optional[List[NotificationChannel]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.delivered_to is None:
            self.delivered_to = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'level': self.level.name,
            'title': self.title,
            'message': self.message,
            'threat_data': self.threat_data,
            'rule_id': self.rule_id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'delivered_to': [c.value for c in self.delivered_to] if self.delivered_to else []
        }

# ============================================================================
# NOTIFICATION HANDLERS
# ============================================================================

class EmailHandler:
    """Handle email notifications"""
    
    def __init__(self, config: Dict):
        """Initialize email handler"""
        self.smtp_server = config.get('smtp_server', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.sender_email = config.get('sender_email', 'alerts@honeypot.local')
        self.sender_password = config.get('sender_password', '')
        self.recipients = config.get('recipients', [])
        self.use_tls = config.get('use_tls', True)
    
    def send(self, alert: Alert) -> bool:
        """Send email alert"""
        if not self.recipients:
            logger.warning('[Alerts] No email recipients configured')
            return False
        
        try:
            message = MIMEMultipart('alternative')
            message['Subject'] = f"[{alert.level.name}] {alert.title}"
            message['From'] = self.sender_email
            message['To'] = ', '.join(self.recipients)
            
            # Create email body
            text = f"""
Threat Alert: {alert.level.name}

Title: {alert.title}
Message: {alert.message}
Rule: {alert.rule_id}
Timestamp: {alert.timestamp.isoformat() if alert.timestamp else 'Unknown'}

Threat Data:
{json.dumps(alert.threat_data, indent=2)}
"""
            
            html = f"""
<html>
  <body style="font-family: Arial, sans-serif;">
    <h2 style="color: #d32f2f;">Threat Alert: {alert.level.name}</h2>
    <p><strong>Title:</strong> {alert.title}</p>
    <p><strong>Message:</strong> {alert.message}</p>
    <p><strong>Rule:</strong> {alert.rule_id}</p>
    <p><strong>Time:</strong> {alert.timestamp.isoformat() if alert.timestamp else 'Unknown'}</p>
    <h3>Threat Details:</h3>
    <pre style="background-color: #f5f5f5; padding: 10px;">
{json.dumps(alert.threat_data, indent=2)}
    </pre>
  </body>
</html>
"""
            
            part1 = MIMEText(text, 'plain')
            part2 = MIMEText(html, 'html')
            message.attach(part1)
            message.attach(part2)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                
                if self.sender_password:
                    server.login(self.sender_email, self.sender_password)
                
                server.sendmail(self.sender_email, self.recipients, message.as_string())
            
            logger.info(f'[Alerts] Email sent for alert {alert.id}')
            return True
        
        except Exception as e:
            logger.error(f'[Alerts] Email sending error: {e}')
            return False

class WebhookHandler:
    """Handle webhook notifications"""
    
    def __init__(self, config: Dict):
        """Initialize webhook handler"""
        self.webhooks = config.get('webhooks', [])
        self.timeout = config.get('timeout', 10)
    
    async def send_async(self, alert: Alert) -> bool:
        """Send webhook alert asynchronously"""
        if not self.webhooks:
            logger.warning('[Alerts] No webhooks configured')
            return False
        
        payload = alert.to_dict()
        
        try:
            if aiohttp is None:
                logger.warning('[Alerts] aiohttp not installed. Skipping webhook delivery.')
                return False
                
            async with aiohttp.ClientSession() as session:
                tasks = []
                for webhook_url in self.webhooks:
                    task = self._send_webhook(session, webhook_url, payload)
                    tasks.append(task)
                
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                success_count = sum(1 for r in results if r is True)
                logger.info(f'[Alerts] Webhooks sent: {success_count}/{len(self.webhooks)}')
                return success_count > 0
        
        except Exception as e:
            logger.error(f'[Alerts] Webhook error: {e}')
            return False
    
    async def _send_webhook(self, session, webhook_url: str, payload: Dict) -> bool:
        """Send single webhook"""
        try:
            if aiohttp is None:
                return False
                
            async with session.post(
                webhook_url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                success = response.status >= 200 and response.status < 300
                logger.debug(f'[Alerts] Webhook response: {response.status}')
                return success
        
        except Exception as e:
            logger.error(f'[Alerts] Webhook send error: {e}')
            return False

class DashboardHandler:
    """Handle dashboard notifications"""
    
    def __init__(self, config: Dict):
        """Initialize dashboard handler"""
        self.max_alerts = config.get('max_alerts', 100)
        self.alerts: List[Alert] = []
    
    def send(self, alert: Alert) -> bool:
        """Store alert for dashboard display"""
        try:
            self.alerts.insert(0, alert)
            
            # Keep only recent alerts
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[:self.max_alerts]
            
            logger.debug(f'[Alerts] Dashboard alert added: {alert.id}')
            return True
        
        except Exception as e:
            logger.error(f'[Alerts] Dashboard alert error: {e}')
            return False
    
    def get_alerts(self, limit: int = 50) -> List[Dict]:
        """Get recent alerts"""
        return [a.to_dict() for a in self.alerts[:limit]]

class SMSHandler:
    """Handle SMS notifications"""
    
    def __init__(self, config: Dict):
        """Initialize SMS handler"""
        self.provider = config.get('provider', 'twilio')
        self.api_key = config.get('api_key', '')
        self.phone_numbers = config.get('phone_numbers', [])
        self.account_sid = config.get('account_sid', '')
    
    def send(self, alert: Alert) -> bool:
        """Send SMS alert"""
        if not self.phone_numbers:
            logger.warning('[Alerts] No phone numbers configured')
            return False
        
        try:
            if self.provider == 'twilio':
                return self._send_twilio(alert)
            else:
                logger.warning(f'[Alerts] Unknown SMS provider: {self.provider}')
                return False
        
        except Exception as e:
            logger.error(f'[Alerts] SMS error: {e}')
            return False
    
    def _send_twilio(self, alert: Alert) -> bool:
        """Send via Twilio API"""
        try:
            try:
                from twilio.rest import Client  # type: ignore
            except ImportError:
                logger.warning('[Alerts] Twilio not installed. SMS alerts disabled.')
                return False
            
            client = Client(self.account_sid, self.api_key)
            
            message_body = (
                f"{alert.level.name}: {alert.title}\n"
                f"Score: {alert.threat_data.get('threat_score', 0)}\n"
                f"IP: {alert.threat_data.get('ip', 'unknown')}"
            )
            
            success_count = 0
            for phone in self.phone_numbers:
                message = client.messages.create(
                    body=message_body,
                    from_=self.account_sid,
                    to=phone
                )
                
                if message.sid:
                    success_count += 1
            
            logger.info(f'[Alerts] SMS sent to {success_count} numbers')
            return success_count > 0
        
        except ImportError:
            logger.warning('[Alerts] Twilio library not installed')
            return False

class SlackHandler:
    """Handle Slack notifications"""
    
    def __init__(self, config: Dict):
        """Initialize Slack handler"""
        self.webhook_url = config.get('webhook_url', '')
        self.channel = config.get('channel', '#alerts')
    
    async def send_async(self, alert: Alert) -> bool:
        """Send Slack message asynchronously"""
        if not self.webhook_url:
            logger.warning('[Alerts] Slack webhook URL not configured')
            return False
        
        try:
            color_map = {
                AlertLevel.CRITICAL: '#d32f2f',
                AlertLevel.HIGH: '#f57c00',
                AlertLevel.MEDIUM: '#fbc02d',
                AlertLevel.LOW: '#1976d2',
                AlertLevel.INFO: '#388e3c'
            }
            
            payload = {
                'channel': self.channel,
                'attachments': [
                    {
                        'color': color_map.get(alert.level, '#999999'),
                        'title': alert.title,
                        'text': alert.message,
                        'fields': [
                            {
                                'title': 'Level',
                                'value': alert.level.name,
                                'short': True
                            },
                            {
                                'title': 'IP Address',
                                'value': alert.threat_data.get('ip', 'unknown'),
                                'short': True
                            },
                            {
                                'title': 'Threat Score',
                                'value': str(alert.threat_data.get('threat_score', 0)),
                                'short': True
                            },
                            {
                                'title': 'Rule',
                                'value': alert.rule_id,
                                'short': True
                            }
                        ],
                        'ts': int(alert.timestamp.timestamp()) if alert.timestamp else 0
                    }
                ]
            }
            
            if aiohttp is None:
                logger.warning('[Alerts] aiohttp not available for async webhook')
                return False
            
            async with aiohttp.ClientSession() as session:
                async with session.post(self.webhook_url, json=payload) as response:
                    success = response.status == 200
                    logger.info(f'[Alerts] Slack notification sent: {success}')
                    return success
        
        except Exception as e:
            logger.error(f'[Alerts] Slack error: {e}')
            return False

# ============================================================================
# NOTIFICATION MANAGER
# ============================================================================

class NotificationManager:
    """
    Manages alert notifications across multiple channels
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize notification manager"""
        self.config = config or {}
        self.handlers = {}
        self.alert_history = []
        self.max_history = 1000
        
        logger.info('[Alerts] Initializing Notification Manager')
        self._init_handlers()
    
    def _init_handlers(self):
        """Initialize notification handlers"""
        channel_configs = self.config.get('channels', {})
        
        # Email handler
        if channel_configs.get('email', {}).get('enabled'):
            self.handlers['email'] = EmailHandler(channel_configs['email'])
            logger.info('[Alerts] Email handler initialized')
        
        # Webhook handler
        if channel_configs.get('webhook', {}).get('enabled'):
            self.handlers['webhook'] = WebhookHandler(channel_configs['webhook'])
            logger.info('[Alerts] Webhook handler initialized')
        
        # Dashboard handler
        if channel_configs.get('dashboard', {}).get('enabled', True):
            self.handlers['dashboard'] = DashboardHandler(channel_configs.get('dashboard', {}))
            logger.info('[Alerts] Dashboard handler initialized')
        
        # SMS handler
        if channel_configs.get('sms', {}).get('enabled'):
            self.handlers['sms'] = SMSHandler(channel_configs['sms'])
            logger.info('[Alerts] SMS handler initialized')
        
        # Slack handler
        if channel_configs.get('slack', {}).get('enabled'):
            self.handlers['slack'] = SlackHandler(channel_configs['slack'])
            logger.info('[Alerts] Slack handler initialized')
    
    def send_alert(self, alert: Alert) -> Dict[str, bool]:
        """Send alert to all configured channels"""
        results = {}
        
        # Ensure delivered_to is initialized
        if alert.delivered_to is None:
            alert.delivered_to = []
        
        # Email
        if 'email' in self.handlers:
            try:
                results['email'] = self.handlers['email'].send(alert)
                if results['email']:
                    alert.delivered_to.append(NotificationChannel.EMAIL)
            except Exception as e:
                logger.error(f'[Alerts] Email send error: {e}')
                results['email'] = False
        
        # Webhook (async)
        if 'webhook' in self.handlers:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Schedule as task if loop is running
                    asyncio.create_task(self.handlers['webhook'].send_async(alert))
                    results['webhook'] = True
                else:
                    results['webhook'] = loop.run_until_complete(
                        self.handlers['webhook'].send_async(alert)
                    )
                
                if results.get('webhook'):
                    alert.delivered_to.append(NotificationChannel.WEBHOOK)
            except Exception as e:
                logger.error(f'[Alerts] Webhook error: {e}')
                results['webhook'] = False
        
        # Dashboard
        if 'dashboard' in self.handlers:
            try:
                results['dashboard'] = self.handlers['dashboard'].send(alert)
                if results['dashboard']:
                    alert.delivered_to.append(NotificationChannel.DASHBOARD)
            except Exception as e:
                logger.error(f'[Alerts] Dashboard error: {e}')
                results['dashboard'] = False
        
        # SMS
        if 'sms' in self.handlers:
            try:
                results['sms'] = self.handlers['sms'].send(alert)
                if results['sms']:
                    alert.delivered_to.append(NotificationChannel.SMS)
            except Exception as e:
                logger.error(f'[Alerts] SMS error: {e}')
                results['sms'] = False
        
        # Slack (async)
        if 'slack' in self.handlers:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.create_task(self.handlers['slack'].send_async(alert))
                    results['slack'] = True
                else:
                    results['slack'] = loop.run_until_complete(
                        self.handlers['slack'].send_async(alert)
                    )
                
                if results.get('slack'):
                    alert.delivered_to.append(NotificationChannel.SLACK)
            except Exception as e:
                logger.error(f'[Alerts] Slack error: {e}')
                results['slack'] = False
        
        # Store in history
        self.alert_history.insert(0, alert)
        if len(self.alert_history) > self.max_history:
            self.alert_history = self.alert_history[:self.max_history]
        
        logger.info(f'[Alerts] Alert delivered: {alert.id} - {results}')
        return results
    
    def get_dashboard_alerts(self, limit: int = 50) -> List[Dict]:
        """Get alerts for dashboard"""
        if 'dashboard' in self.handlers:
            return self.handlers['dashboard'].get_alerts(limit)
        return []
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """Get alert history"""
        return [a.to_dict() for a in self.alert_history[:limit]]
    
    def get_stats(self) -> Dict:
        """Get notification statistics"""
        return {
            'total_alerts': len(self.alert_history),
            'handlers_enabled': list(self.handlers.keys()),
            'recent_alerts': len([a for a in self.alert_history if 
                                 (datetime.now() - a.timestamp).total_seconds() < 3600])
        }

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_notification_manager = None

def get_notification_manager(config: Optional[Dict] = None) -> NotificationManager:
    """Get singleton notification manager instance"""
    global _notification_manager
    
    if _notification_manager is None:
        _notification_manager = NotificationManager(config)
    
    return _notification_manager
