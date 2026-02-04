"""
SOAR Integration for Automated Incident Management
Integrates with popular SOAR platforms for playbook execution
"""

import json
import logging
import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

try:
    import aiohttp  # type: ignore
except ImportError:
    aiohttp = None

logger = logging.getLogger(__name__)

# ============================================================================
# ENUMS & TYPES
# ============================================================================

class SOARPlatform(Enum):
    """Supported SOAR platforms"""
    SPLUNK_PHANTOM = "splunk_phantom"
    PALO_ALTO_CORTEX = "palo_alto_cortex"
    DEMISTO = "demisto"
    MICROSOFT_SENTINEL = "microsoft_sentinel"
    IBM_SOAR = "ibm_soar"
    GENERIC_WEBHOOK = "generic_webhook"

class IncidentSeverity(Enum):
    """Incident severity levels"""
    CRITICAL = 5
    HIGH = 4
    MEDIUM = 3
    LOW = 2
    INFO = 1

class IncidentStatus(Enum):
    """Incident status"""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"

# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class Incident:
    """Security incident for SOAR integration"""
    id: str
    title: str
    description: str
    severity: IncidentSeverity
    threat_data: Dict
    source_ip: str
    threat_type: str
    rule_id: str
    timestamp: Optional[datetime] = None
    source_system: str = "ddospot"
    tags: Optional[List[str]] = None
    status: IncidentStatus = IncidentStatus.OPEN
    playbooks: Optional[List[str]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.tags is None:
            self.tags = []
        if self.playbooks is None:
            self.playbooks = []
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        data = asdict(self)
        data['severity'] = self.severity.name
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat() if self.timestamp else None
        return data

@dataclass
class PlaybookExecution:
    """Playbook execution request"""
    incident_id: str
    playbook_name: str
    parameters: Optional[Dict] = None
    triggered_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: str = "pending"
    result: Optional[Dict] = None
    
    def __post_init__(self):
        if self.triggered_at is None:
            self.triggered_at = datetime.now()
        if self.parameters is None:
            self.parameters = {}

# ============================================================================
# SOAR HANDLERS
# ============================================================================

class SplunkPhantomHandler:
    """Splunk Phantom/SOAR integration handler"""
    
    def __init__(self, config: Dict):
        """Initialize Phantom handler"""
        self.base_url = config.get('base_url', '')
        self.api_token = config.get('api_token', '')
        self.playbook_mapping = config.get('playbook_mapping', {})
    
    async def create_incident(self, incident: Incident) -> Tuple[bool, str, Optional[str]]:
        """Create incident in Phantom"""
        if not self.base_url or not self.api_token:
            logger.warning('[SOAR] Phantom credentials not configured')
            return False, 'Phantom not configured', None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'name': incident.title,
                'description': incident.description,
                'severity': incident.severity.name,
                'source_data_identifier': incident.id,
                'type': incident.threat_type,
                'labels': incident.tags,
                'cef': {
                    'sourceIPv4': incident.source_ip,
                    'ddospot_threat_score': incident.threat_data.get('threat_score', 0),
                    'ddospot_rule_id': incident.rule_id
                }
            }
            
            url = f'{self.base_url}/rest/container/'
            
            if aiohttp is None:
                logger.error('[SOAR] aiohttp not available')
                return False, 'aiohttp not installed', None
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 201:
                        data = await response.json()
                        incident_id = data.get('id', '')
                        logger.info(f'[SOAR] Phantom incident created: {incident_id}')
                        return True, 'Incident created', incident_id
                    else:
                        error = await response.text()
                        logger.error(f'[SOAR] Phantom error: {error}')
                        return False, f'HTTP {response.status}', None
        
        except Exception as e:
            logger.error(f'[SOAR] Phantom error: {e}')
            return False, str(e), None
    
    async def execute_playbook(self, incident_id: str, playbook: str,
                               parameters: Dict) -> Tuple[bool, str, Dict]:
        """Execute playbook in Phantom"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            # Map generic playbook name to Phantom playbook
            phantom_playbook = self.playbook_mapping.get(playbook, playbook)
            
            payload = {
                'playbook_name': phantom_playbook,
                'scope': 'all',
                'container_id': incident_id,
                'parameters': parameters
            }
            
            url = f'{self.base_url}/rest/playbook_run/'
            
            if aiohttp is None:
                logger.error('[SOAR] aiohttp not available')
                return False, 'aiohttp not installed', {}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 201:
                        data = await response.json()
                        result = {
                            'playbook_run_id': data.get('id'),
                            'status': 'started'
                        }
                        logger.info(f'[SOAR] Playbook executed: {phantom_playbook}')
                        return True, 'Playbook started', result
                    else:
                        error = await response.text()
                        logger.error(f'[SOAR] Playbook error: {error}')
                        return False, f'HTTP {response.status}', {}
        
        except Exception as e:
            logger.error(f'[SOAR] Playbook execution error: {e}')
            return False, str(e), {}

class PaloAltoCortexHandler:
    """Palo Alto Cortex XSOAR integration handler"""
    
    def __init__(self, config: Dict):
        """Initialize Cortex XSOAR handler"""
        self.base_url = config.get('base_url', '')
        self.api_token = config.get('api_token', '')
        self.playbook_mapping = config.get('playbook_mapping', {})
    
    async def create_incident(self, incident: Incident) -> Tuple[bool, str, Optional[str]]:
        """Create incident in Cortex XSOAR"""
        if not self.base_url or not self.api_token:
            logger.warning('[SOAR] Cortex credentials not configured')
            return False, 'Cortex not configured', None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'name': incident.title,
                'description': incident.description,
                'severity': incident.severity.value,
                'type': incident.threat_type,
                'labels': incident.tags,
                'customFields': {
                    'ddospotthreatscore': incident.threat_data.get('threat_score', 0),
                    'ddospotip': incident.source_ip,
                    'ddospot_rule': incident.rule_id
                }
            }
            
            url = f'{self.base_url}/xsoar/incidents'
            
            if aiohttp is None:
                logger.error('[SOAR] aiohttp not available')
                return False, 'aiohttp not installed', None
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        incident_id = str(data.get('id', ''))
                        logger.info(f'[SOAR] Cortex incident created: {incident_id}')
                        return True, 'Incident created', incident_id
                    else:
                        error = await response.text()
                        logger.error(f'[SOAR] Cortex error: {error}')
                        return False, f'HTTP {response.status}', None
        
        except Exception as e:
            logger.error(f'[SOAR] Cortex error: {e}')
            return False, str(e), None
    
    async def execute_playbook(self, incident_id: str, playbook: str,
                               parameters: Dict) -> Tuple[bool, str, Dict]:
        """Execute playbook in Cortex XSOAR"""
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            # Map generic playbook name to Cortex playbook
            cortex_playbook = self.playbook_mapping.get(playbook, playbook)
            
            payload = {
                'playbookID': cortex_playbook,
                'incidentID': incident_id,
                'isRun': True
            }
            
            url = f'{self.base_url}/xsoar/playbooks/run'
            
            if aiohttp is None:
                logger.error('[SOAR] aiohttp not available')
                return False, 'aiohttp not installed', {}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        result = {
                            'run_id': data.get('runID'),
                            'status': 'started'
                        }
                        logger.info(f'[SOAR] Cortex playbook executed: {cortex_playbook}')
                        return True, 'Playbook started', result
                    else:
                        error = await response.text()
                        logger.error(f'[SOAR] Cortex playbook error: {error}')
                        return False, f'HTTP {response.status}', {}
        
        except Exception as e:
            logger.error(f'[SOAR] Cortex playbook error: {e}')
            return False, str(e), {}

class MicrosoftSentinelHandler:
    """Microsoft Sentinel integration handler"""
    
    def __init__(self, config: Dict):
        """Initialize Sentinel handler"""
        self.base_url = config.get('base_url', '')
        self.api_token = config.get('api_token', '')
        self.resource_group = config.get('resource_group', '')
        self.workspace = config.get('workspace', '')
    
    async def create_incident(self, incident: Incident) -> Tuple[bool, str, Optional[str]]:
        """Create incident in Microsoft Sentinel"""
        if not self.base_url or not self.api_token:
            logger.warning('[SOAR] Sentinel credentials not configured')
            return False, 'Sentinel not configured', None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'properties': {
                    'title': incident.title,
                    'description': incident.description,
                    'severity': incident.severity.name,
                    'status': incident.status.value,
                    'labels': incident.tags,
                    'owner': {
                        'assignedTo': None,
                        'email': None,
                        'name': None,
                        'objectId': None,
                        'userPrincipalName': None
                    }
                }
            }
            
            url = (f'{self.base_url}/subscriptions/{self.resource_group}/'
                   f'resourceGroups/{self.resource_group}/'
                   f'providers/Microsoft.OperationalInsights/workspaces/{self.workspace}/'
                   f'incidents')
            
            if aiohttp is None:
                logger.error('[SOAR] aiohttp not available')
                return False, 'aiohttp not installed', None
            
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status in [200, 201]:
                        data = await response.json()
                        incident_id = data.get('name', '')
                        logger.info(f'[SOAR] Sentinel incident created: {incident_id}')
                        return True, 'Incident created', incident_id
                    else:
                        error = await response.text()
                        logger.error(f'[SOAR] Sentinel error: {error}')
                        return False, f'HTTP {response.status}', None
        
        except Exception as e:
            logger.error(f'[SOAR] Sentinel error: {e}')
            return False, str(e), None

# ============================================================================
# SOAR INTEGRATION ENGINE
# ============================================================================

class SOARIntegrationEngine:
    """
    Manages SOAR platform integration and incident management
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize SOAR integration engine"""
        self.config = config or {}
        self.handlers: Dict[str, Any] = {}
        self.incident_mapping: Dict[str, str] = {}
        
        logger.info('[SOAR] Initializing SOAR Integration Engine')
        self._init_handlers()
    
    def _init_handlers(self):
        """Initialize SOAR handlers"""
        soar_config = self.config.get('soar', {})
        
        # Phantom handler
        if soar_config.get('phantom', {}).get('enabled'):
            self.handlers['phantom'] = SplunkPhantomHandler(soar_config['phantom'])
            logger.info('[SOAR] Phantom handler initialized')
        
        # Cortex XSOAR handler
        if soar_config.get('cortex', {}).get('enabled'):
            self.handlers['cortex'] = PaloAltoCortexHandler(soar_config['cortex'])
            logger.info('[SOAR] Cortex XSOAR handler initialized')
        
        # Sentinel handler
        if soar_config.get('sentinel', {}).get('enabled'):
            self.handlers['sentinel'] = MicrosoftSentinelHandler(soar_config['sentinel'])
            logger.info('[SOAR] Microsoft Sentinel handler initialized')
    
    async def create_incident(self, incident: Incident) -> Dict[str, Any]:
        """Create incident in all configured SOAR platforms"""
        results = {
            'incident_id': incident.id,
            'created_at': datetime.now().isoformat(),
            'platforms': {}
        }
        
        tasks = []
        platform_names = []
        
        # Create tasks for all handlers
        for platform_name, handler in self.handlers.items():
            task = handler.create_incident(incident)
            tasks.append(task)
            platform_names.append(platform_name)
        
        # Execute all tasks concurrently
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for platform_name, response in zip(platform_names, responses):
                if isinstance(response, Exception):
                    results['platforms'][platform_name] = {
                        'success': False,
                        'message': str(response),
                        'incident_id': None
                    }
                else:
                    success, message, remote_id = response  # type: ignore
                    results['platforms'][platform_name] = {
                        'success': success,
                        'message': message,
                        'incident_id': remote_id
                    }
                    
                    # Store mapping for playbook execution
                    if success and remote_id:
                        self.incident_mapping[f'{platform_name}_{incident.id}'] = remote_id
        
        logger.info(f'[SOAR] Incident created: {incident.id} - {results}')
        return results
    
    async def execute_playbook(self, incident_id: str, playbook: str,
                               parameters: Optional[Dict] = None) -> Dict[str, Any]:
        """Execute playbook in SOAR platforms"""
        results = {
            'incident_id': incident_id,
            'playbook': playbook,
            'executed_at': datetime.now().isoformat(),
            'platforms': {}
        }
        
        if parameters is None:
            parameters = {}
        
        tasks = []
        platform_names = []
        
        # Create tasks for all handlers
        for platform_name, handler in self.handlers.items():
            # Get remote incident ID
            remote_id = self.incident_mapping.get(f'{platform_name}_{incident_id}')
            
            if remote_id:
                task = handler.execute_playbook(remote_id, playbook, parameters)
                tasks.append(task)
                platform_names.append(platform_name)
        
        # Execute all tasks concurrently
        if tasks:
            responses = await asyncio.gather(*tasks, return_exceptions=True)
            
            for platform_name, response in zip(platform_names, responses):
                if isinstance(response, Exception):
                    results['platforms'][platform_name] = {
                        'success': False,
                        'message': str(response),
                        'result': {}
                    }
                else:
                    success, message, result = response  # type: ignore
                    results['platforms'][platform_name] = {
                        'success': success,
                        'message': message,
                        'result': result
                    }
        
        logger.info(f'[SOAR] Playbook executed: {playbook} - {results}')
        return results
    
    async def get_incident_status(self, incident_id: str, platform: Optional[str] = None) -> Dict:
        """Get incident status from SOAR platform"""
        if platform and platform in self.handlers:
            # Get from specific platform
            remote_id = self.incident_mapping.get(f'{platform}_{incident_id}')
            
            if remote_id:
                return {
                    'platform': platform,
                    'incident_id': incident_id,
                    'remote_id': remote_id,
                    'status': 'found'
                }
        
        # Check all platforms
        statuses = {}
        for platform_name in self.handlers.keys():
            remote_id = self.incident_mapping.get(f'{platform_name}_{incident_id}')
            if remote_id:
                statuses[platform_name] = {
                    'remote_id': remote_id,
                    'status': 'found'
                }
        
        return {
            'incident_id': incident_id,
            'platforms': statuses
        }
    
    def get_integration_status(self) -> Dict:
        """Get overall SOAR integration status"""
        return {
            'timestamp': datetime.now().isoformat(),
            'platforms_enabled': list(self.handlers.keys()),
            'total_incidents_mapped': len(self.incident_mapping),
            'handlers': {
                name: {
                    'status': 'enabled',
                    'type': handler.__class__.__name__
                }
                for name, handler in self.handlers.items()
            }
        }

# ============================================================================
# SINGLETON ACCESS
# ============================================================================

_soar_engine = None

def get_soar_integration(config: Optional[Dict] = None) -> SOARIntegrationEngine:
    """Get singleton SOAR integration engine instance"""
    global _soar_engine
    
    if _soar_engine is None:
        _soar_engine = SOARIntegrationEngine(config)
    
    return _soar_engine
