"""
Protocol-specific response handlers for honeypot services.
Makes the honeypot appear as real vulnerable services.
"""

import struct
from typing import Tuple

# =========================
# HTTP RESPONSES
# =========================

def create_http_response(request: bytes) -> bytes:
    """Create a realistic HTTP response for HTTP requests."""
    try:
        request_str = request.decode('utf-8', errors='ignore').split('\r\n')[0]
    except:
        request_str = "UNKNOWN"
    
    html_body = b"""<!DOCTYPE html>
<html>
<head>
    <title>Welcome</title>
</head>
<body>
    <h1>Welcome to Web Server</h1>
    <p>This is a default web server page.</p>
</body>
</html>"""
    
    response = b"HTTP/1.1 200 OK\r\n"
    response += b"Content-Type: text/html\r\n"
    response += b"Content-Length: " + str(len(html_body)).encode() + b"\r\n"
    response += b"Connection: close\r\n"
    response += b"Server: Apache/2.4.41 (Ubuntu)\r\n"
    response += b"\r\n"
    response += html_body
    
    return response


# =========================
# SSH RESPONSES
# =========================

def create_ssh_banner() -> bytes:
    """Create a realistic SSH server banner."""
    # SSH protocol: SSH-2.0-OpenSSH_7.4
    banner = b"SSH-2.0-OpenSSH_7.4\r\n"
    return banner


def create_ssh_key_exchange() -> bytes:
    """Create minimal SSH key exchange response (fake, but looks real)."""
    # Minimal SSH packet structure (not a full handshake, but discourages brute force)
    response = b"\x00\x00\x00\x00"  # Packet length
    response += b"\x00"  # Padding length
    return response


# =========================
# DNS RESPONSES
# =========================

def create_dns_response(request: bytes, src_addr: Tuple[str, int]) -> bytes:
    """
    Create a minimal DNS response.
    DNS packets need proper structure to be recognized.
    """
    if len(request) < 12:
        return b""
    
    try:
        # Parse DNS header
        transaction_id = request[0:2]
        flags = request[2:4]
        
        # Build response header
        response = transaction_id  # Transaction ID (echo)
        response += b"\x84\x00"    # Flags: response, no error
        response += b"\x00\x01"    # Questions: 1
        response += b"\x00\x01"    # Answer RRs: 1
        response += b"\x00\x00"    # Authority RRs: 0
        response += b"\x00\x00"    # Additional RRs: 0
        
        # Try to extract question from request
        if len(request) > 12:
            response += request[12:]  # Echo the question
            # Add a simple A record response (fake IP)
            response += b"\xc0\x0c"    # Pointer to name
            response += b"\x00\x01"    # Type: A
            response += b"\x00\x01"    # Class: IN
            response += b"\x00\x00\x00\x3c"  # TTL: 60
            response += b"\x00\x04"    # Data length: 4
            response += b"\x7f\x00\x00\x01"  # IP: 127.0.0.1
        
        return response
    except:
        return b""


# =========================
# SSDP RESPONSES (UPnP Discovery)
# =========================

def create_ssdp_response(src_addr: Tuple[str, int], local_addr: str = "127.0.0.1") -> bytes:
    """
    Create a realistic SSDP (Simple Service Discovery Protocol) response.
    Used by UPnP devices. Attackers use it for DDoS amplification.
    """
    response = b"HTTP/1.1 200 OK\r\n"
    response += b"CACHE-CONTROL: max-age=1800\r\n"
    response += b"EXT:\r\n"
    response += b"LOCATION: http://" + local_addr.encode() + b":5000/description.xml\r\n"
    response += b"SERVER: Linux/3.14.0 UPnP/1.0 IpBridge/1.26.0\r\n"
    response += b"ST: upnp:rootdevice\r\n"
    response += b"USN: uuid:UPnP-SpotDevice:device:MediaRenderer:1::upnp:rootdevice\r\n"
    response += b"\r\n"
    
    return response


# =========================
# HELPER FUNCTIONS
# =========================

def identify_protocol(data: bytes, port: int) -> str:
    """
    Try to identify which protocol the client is speaking based on data and port.
    """
    if port == 8080 or port == 80:
        if data.startswith(b'GET ') or data.startswith(b'POST ') or data.startswith(b'HEAD '):
            return 'http'
    elif port == 2222 or port == 22:
        if data.startswith(b'SSH-'):
            return 'ssh'
    elif port == 53:
        return 'dns'
    elif port == 1900:
        if b'M-SEARCH' in data:
            return 'ssdp'
    
    # Default heuristic: check if it looks like text protocol
    if data[:4].startswith(b'GET ') or data[:4].startswith(b'POST'):
        return 'http'
    
    return 'unknown'
