import asyncio
import socket
from typing import List, Tuple, Optional, Any

from core.config import TCP_PORTS, UDP_PORTS, THRESHOLD_PER_MIN, BLACKLIST_SECONDS
from core.protocol_handlers import (
    create_http_response,
    create_ssh_banner,
    create_ssdp_response,
    create_dns_response,
    identify_protocol,
)
from core.state import HoneypotState
from core.detection import AttackDetector
from core.database import HoneypotDatabase
from telemetry.logger import get_logger
from telemetry.alerts import get_alert_manager
from ml.model import get_model
from ml.features import FeatureExtractor

logger = get_logger("ddospot.server")

# =========================
# INTERNAL STATE
# =========================

_tcp_servers: List[asyncio.AbstractServer] = []
_udp_sockets: List[socket.socket] = []
_running: bool = False

# Global honeypot state and detector
_state: Optional[HoneypotState] = None
_detector: Optional[AttackDetector] = None
_db: Optional[HoneypotDatabase] = None
_alert_manager: Optional[Any] = None
_ml_model: Optional[Any] = None
_feature_extractor: Optional[FeatureExtractor] = None


def initialize_state():
    """Initialize the honeypot state manager and database"""
    global _state, _detector, _db, _alert_manager, _ml_model, _feature_extractor
    _state = HoneypotState(window_size_seconds=60, rate_threshold=THRESHOLD_PER_MIN)
    _detector = AttackDetector(rate_threshold=THRESHOLD_PER_MIN, window_seconds=60)
    _db = HoneypotDatabase("logs/honeypot.db")
    _alert_manager = get_alert_manager("logs/honeypot.db", "config/alert_config.json")
    _ml_model = get_model()
    _feature_extractor = FeatureExtractor()
    logger.info("Database initialized: logs/honeypot.db")
    logger.info("Alert manager initialized")
    logger.info("ML model loaded for attack classification")


# =========================
# ATTACK PROCESSING
# =========================

def process_attack(source_ip: str, port: int, protocol: str, payload_size: int, event_type: str = "connection"):
    """Process an attack event and determine if blacklisting is needed"""
    if not _state or not _detector or not _db:
        return
    
    # Record event in database
    _db.add_event(source_ip, port, protocol, payload_size, event_type)
    
    # Record the event in state
    _state.record_event(source_ip, port, protocol, payload_size, event_type)
    
    # Analyze if blacklisting is warranted
    should_blacklist, reason, duration = _detector.analyze_attack(_state, source_ip)
    
    if should_blacklist:
        _state.blacklist_ip(source_ip, duration)
        
        # Also add to database blacklist
        severity = _detector.get_attack_severity(_state, source_ip)
        _db.add_blacklist(source_ip, reason, duration, severity)
        
        profile = _state.attack_profiles[source_ip]
        
        # Get ML prediction for attack type
        ml_attack_type = 'unknown'
        ml_confidence = 0.0
        if _ml_model and _feature_extractor and profile.total_events > 0:
            try:
                # Get events for this IP from database
                events = _db.get_events_by_ip(source_ip, limit=1000)
                if events:
                    # Extract features
                    features_dict = _feature_extractor.extract_from_events(events)
                    feature_names = _feature_extractor.get_feature_names()
                    feature_vector = [features_dict.get(name, 0) for name in feature_names]
                    
                    # Predict
                    ml_attack_type, ml_confidence = _ml_model.predict(feature_vector)
            except Exception as e:
                logger.debug(f"ML prediction error: {e}")
        
        logger.warning(
            f"BLACKLIST: {source_ip} ({reason}) - "
            f"{profile.total_events} events, "
            f"severity={severity}, duration={duration}s, "
            f"ML={ml_attack_type} ({ml_confidence:.1%})"
        )
        
        # Send alerts
        if _alert_manager:
            try:
                if severity.lower() == 'critical':
                    _alert_manager.alert_critical_attack(
                        ip=source_ip,
                        severity=severity,
                        event_count=profile.total_events,
                        protocols=profile.protocols_used
                    )
                
                _alert_manager.alert_ip_blacklisted(
                    ip=source_ip,
                    reason=reason,
                    severity=severity
                )
            except Exception as e:
                logger.error(f"Failed to send alert: {e}")
    
    # Periodically update IP profiles in database
    if _state.total_events % 100 == 0:  # Update every 100 events
        _update_database_profiles()


def _update_database_profiles():
    """Sync IP profiles from state to database"""
    if not _state or not _db:
        return
    
    try:
        for ip, profile in _state.attack_profiles.items():
            _db.add_or_update_profile(
                ip=ip,
                first_seen=profile.first_seen,
                last_seen=profile.last_seen,
                total_events=profile.total_events,
                events_per_minute=profile.events_per_minute,
                attack_type=profile.attack_type,
                protocols_used=list(profile.protocols_used),
                avg_payload_size=profile.avg_payload_size,
                severity=_detector.get_attack_severity(_state, ip) if _detector else "unknown"
            )
    except Exception as e:
        logger.warning(f"Error updating database profiles: {e}")


# =========================
# TCP HANDLER
# =========================

async def _handle_tcp_client(
    reader: asyncio.StreamReader,
    writer: asyncio.StreamWriter
) -> None:
    peer: Tuple[str, int] = writer.get_extra_info("peername")
    port: int = writer.get_extra_info("sockname")[1]
    source_ip = peer[0]
    
    logger.info(f"TCP connection from {peer} on port {port}")

    try:
        # Check if IP is already blacklisted
        if _state and _state.is_blacklisted(source_ip):
            logger.info(f"Blacklisted IP {source_ip} attempted connection, dropping")
            writer.close()
            await writer.wait_closed()
            return
        
        # For SSH, send banner immediately
        if port == 2222 or port == 22:
            banner = create_ssh_banner()
            writer.write(banner)
            await writer.drain()
            logger.info(f"SSH banner sent to {peer}")
        
        # Read client data
        data = await asyncio.wait_for(reader.read(1024), timeout=5.0)
        if data:
            logger.info(f"TCP received {len(data)} bytes from {peer}")
            
            # Record attack event
            protocol = identify_protocol(data, port)
            process_attack(source_ip, port, protocol, len(data), "tcp_data")
            
            # Send appropriate response
            response = None
            
            if protocol == 'http':
                response = create_http_response(data)
                logger.info(f"HTTP attack detected from {peer}")
            
            # Send response if we created one
            if response:
                try:
                    writer.write(response)
                    await writer.drain()
                except Exception as e:
                    logger.warning(f"Failed to send response to {peer}: {e}")
    except asyncio.TimeoutError:
        logger.info(f"Connection from {peer} timed out (possible slow attack)")
        process_attack(source_ip, port, "tcp", 0, "timeout")
    except Exception as e:
        logger.warning(f"TCP error with {peer}: {e}")
    finally:
        try:
            writer.close()
            await writer.wait_closed()
        except:
            pass
        logger.info(f"TCP connection closed {peer}")


# =========================
# UDP HANDLER
# =========================

async def _udp_listener(sock: socket.socket) -> None:
    loop = asyncio.get_running_loop()
    port = sock.getsockname()[1]
    logger.info(f"UDP listening on {sock.getsockname()}")

    while _running:
        try:
            data, addr = await loop.sock_recvfrom(sock, 4096)
            source_ip = addr[0]
            
            logger.info(f"UDP received {len(data)} bytes from {addr}")
            
            # Check if IP is blacklisted
            if _state and _state.is_blacklisted(source_ip):
                logger.info(f"Blacklisted IP {source_ip} sent UDP, ignoring")
                continue
            
            # Record attack event
            protocol = identify_protocol(data, port)
            process_attack(source_ip, port, protocol, len(data), "udp_data")
            
            # Send appropriate response
            response = None
            
            if protocol == 'dns':
                response = create_dns_response(data, addr)
                logger.info(f"DNS query from {addr}")
            elif protocol == 'ssdp':
                response = create_ssdp_response(addr)
                logger.info(f"SSDP discovery from {addr}")
            
            # Send response if we created one
            if response:
                try:
                    await loop.sock_sendto(sock, response, addr)
                except Exception as e:
                    logger.warning(f"Failed to send UDP response to {addr}: {e}")
        except Exception as e:
            if _running:
                logger.warning(f"UDP error: {e}")

# =========================
# BACKGROUND TASKS
# =========================

async def _cleanup_blacklist_task():
    """Periodically clean up expired blacklist entries"""
    while _running:
        try:
            if _state:
                _state.cleanup_expired_blacklist()
            await asyncio.sleep(300)  # Clean every 5 minutes
        except Exception as e:
            logger.warning(f"Error in blacklist cleanup: {e}")


# =========================
# SERVER CONTROL
# =========================

async def start_servers(host: str = "0.0.0.0") -> None:
    global _running
    if _running:
        return

    # Initialize state and detector
    initialize_state()
    
    logger.info("Starting servers with advanced detection")
    _running = True

    # ---- TCP ----
    for port in TCP_PORTS:
        server = await asyncio.start_server(
            _handle_tcp_client,
            host,
            port
        )
        _tcp_servers.append(server)
        logger.info(f"TCP server started on {host}:{port}")

    # ---- UDP ----
    loop = asyncio.get_running_loop()

    for port in UDP_PORTS:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setblocking(False)
        sock.bind((host, port))

        _udp_sockets.append(sock)
        asyncio.create_task(_udp_listener(sock))
        logger.info(f"UDP socket bound on {host}:{port}")
    
    # Start cleanup task for expired blacklist entries
    asyncio.create_task(_cleanup_blacklist_task())


async def stop_servers() -> None:
    global _running, _db
    if not _running:
        return

    logger.info("Stopping servers")
    _running = False

    # Final database sync
    _update_database_profiles()

    # ---- TCP ----
    for server in _tcp_servers:
        server.close()
        await server.wait_closed()

    _tcp_servers.clear()

    # ---- UDP ----
    for sock in _udp_sockets:
        try:
            sock.close()
        except Exception:
            pass

    _udp_sockets.clear()

    # Close database connection
    if _db:
        _db.close()
        logger.info("Database connection closed")

    logger.info("All servers stopped")
