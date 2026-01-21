"""
Honeypot protocol response handlers.
Generates appropriate responses for different attack protocols.
"""

import asyncio
import socket
from typing import Optional, Tuple
from telemetry.logger import get_logger

logger = get_logger(__name__)


class ProtocolResponseHandler:
    """Handles responses to different protocols"""
    
    @staticmethod
    def get_http_response(request: bytes) -> bytes:
        """Generate HTTP response"""
        response = (
            "HTTP/1.1 200 OK\r\n"
            "Content-Type: text/html\r\n"
            "Content-Length: 100\r\n"
            "Connection: close\r\n"
            "\r\n"
            "<html><body><h1>Welcome</h1><p>This is a honeypot server.</p></body></html>"
        ).encode()
        return response
    
    @staticmethod
    def get_ssh_banner() -> bytes:
        """Generate SSH protocol banner"""
        banner = "SSH-2.0-OpenSSH_7.4\r\n".encode()
        return banner
    
    @staticmethod
    def get_ssdp_response() -> bytes:
        """Generate SSDP M-SEARCH response"""
        response = (
            "HTTP/1.1 200 OK\r\n"
            "CACHE-CONTROL: max-age=1900\r\n"
            "EXT:\r\n"
            "LOCATION: http://127.0.0.1:1900/upnp/device.xml\r\n"
            "SERVER: Linux/3.14.0 UPnP/1.0 miniupnpd/1.9\r\n"
            "ST: upnp:rootdevice\r\n"
            "USN: uuid:12345678-1234-1234-1234-123456789012::upnp:rootdevice\r\n"
            "\r\n"
        ).encode()
        return response
    
    @staticmethod
    def get_dns_response(request: bytes) -> bytes:
        """Generate DNS response"""
        # Simple DNS response for any query
        if len(request) < 12:
            return b""
        
        # Copy transaction ID from request
        transaction_id = request[:2]
        
        # DNS response flags: QR=1, OPCODE=0, AA=0, TC=0, RD=1, RA=1, Z=0, RCODE=0
        flags = b'\x84\x00'
        
        # Question count, answer count, authority count, additional count
        counts = b'\x00\x01\x00\x01\x00\x00\x00\x00'
        
        # Original question section (echoed)
        response = transaction_id + flags + counts + request[12:]
        
        # Add a simple A record response (point to 127.0.0.1)
        response += b'\x00\x05\x00\x01\x00\x00\x00\x60\x00\x04\x7f\x00\x00\x01'
        
        return response
    
    @staticmethod
    def get_ntp_response(request: bytes) -> bytes:
        """Generate NTP response"""
        if len(request) < 48:
            return b""
        
        import time
        import struct
        
        # NTP response packet
        response = bytearray(48)
        
        # First byte: LI (2), VN (3), Mode (3)
        # LI=0 (no warning), VN=4 (NTPv4), Mode=4 (server)
        response[0] = 0x24
        
        # Stratum
        response[1] = 2  # Primary reference source
        
        # Poll interval
        response[2] = 4
        
        # Precision
        response[3] = 0xEC  # about -20 (microseconds)
        
        # Root delay
        struct.pack_into("!I", response, 4, 0x00010000)
        
        # Root dispersion
        struct.pack_into("!I", response, 8, 0x00010000)
        
        # Reference ID (us.pool.ntp.org)
        response[12:16] = b'POOL'
        
        # Reference timestamp
        ntp_time = int((time.time() + 2208988800) * (2 ** 32))
        struct.pack_into("!Q", response, 16, ntp_time)
        
        # Originate timestamp (from request)
        response[24:32] = request[40:48] if len(request) >= 48 else b'\x00' * 8
        
        # Receive timestamp
        struct.pack_into("!Q", response, 32, ntp_time)
        
        # Transmit timestamp
        struct.pack_into("!Q", response, 40, ntp_time)
        
        return bytes(response)


class HTTPServerResponse:
    """HTTP server response generator"""
    
    @staticmethod
    async def handle_client(reader, writer, addr):
        """Handle HTTP client connection"""
        try:
            request = await asyncio.wait_for(
                reader.read(4096),
                timeout=5
            )
            
            if not request:
                writer.close()
                return
            
            response = ProtocolResponseHandler.get_http_response(request)
            writer.write(response)
            await writer.drain()
            writer.close()
            await writer.wait_closed()
            
            logger.debug(f"Handled HTTP request from {addr}")
        except asyncio.TimeoutError:
            writer.close()
        except Exception as e:
            logger.error(f"HTTP handler error from {addr}: {e}")
            try:
                writer.close()
            except:
                pass


class SSHServerResponse:
    """SSH server response generator"""
    
    @staticmethod
    async def handle_client(reader, writer, addr):
        """Handle SSH client connection"""
        try:
            # Send SSH banner immediately
            banner = ProtocolResponseHandler.get_ssh_banner()
            writer.write(banner)
            await writer.drain()
            
            # Keep connection open briefly to receive any data
            try:
                data = await asyncio.wait_for(
                    reader.read(1024),
                    timeout=2
                )
                logger.debug(f"SSH data received from {addr}: {len(data)} bytes")
            except asyncio.TimeoutError:
                pass
            
            writer.close()
            await writer.wait_closed()
            
            logger.debug(f"Handled SSH connection from {addr}")
        except Exception as e:
            logger.error(f"SSH handler error from {addr}: {e}")
            try:
                writer.close()
            except:
                pass


class SSDPServerResponse:
    """SSDP server response generator"""
    
    @staticmethod
    async def handle_discovery(addr, data):
        """Handle SSDP M-SEARCH discovery"""
        try:
            if b"M-SEARCH" in data and b"ssdp:discover" in data:
                response = ProtocolResponseHandler.get_ssdp_response()
                logger.debug(f"Sent SSDP response to {addr}")
                return response
        except Exception as e:
            logger.error(f"SSDP handler error from {addr}: {e}")
        
        return None


class DNSServerResponse:
    """DNS server response generator"""
    
    @staticmethod
    async def handle_query(addr, data):
        """Handle DNS query"""
        try:
            response = ProtocolResponseHandler.get_dns_response(data)
            logger.debug(f"Sent DNS response to {addr}")
            return response
        except Exception as e:
            logger.error(f"DNS handler error from {addr}: {e}")
        
        return None


class NTPServerResponse:
    """NTP server response generator"""
    
    @staticmethod
    async def handle_query(addr, data):
        """Handle NTP query"""
        try:
            response = ProtocolResponseHandler.get_ntp_response(data)
            logger.debug(f"Sent NTP response to {addr}")
            return response
        except Exception as e:
            logger.error(f"NTP handler error from {addr}: {e}")
        
        return None


# Export handlers
def get_protocol_handler(protocol: str):
    """Get handler for a specific protocol"""
    handlers = {
        'HTTP': HTTPServerResponse,
        'SSH': SSHServerResponse,
        'SSDP': SSDPServerResponse,
        'DNS': DNSServerResponse,
        'NTP': NTPServerResponse,
    }
    return handlers.get(protocol.upper())
