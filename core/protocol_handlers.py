"""
Protocol-specific response handlers for honeypot services.
Makes the honeypot appear as real vulnerable services.
"""

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

# =========================
# FTP RESPONSES
# =========================

def create_ftp_banner() -> bytes:
    """Create a realistic FTP server banner."""
    return b"220 FTP Server Ready\r\n"

def create_ftp_response(request: bytes) -> bytes:
    """Create FTP response based on command."""
    try:
        cmd = request.decode('utf-8', errors='ignore').strip().upper()
        
        if cmd.startswith('USER'):
            return b"331 User OK, password required\r\n"
        elif cmd.startswith('PASS'):
            return b"230 User logged in\r\n"
        elif cmd.startswith('LIST'):
            return b"150 Opening ASCII mode data connection for file list\r\n"
        elif cmd.startswith('QUIT'):
            return b"221 Goodbye\r\n"
        elif cmd.startswith('PWD'):
            return b"257 \"/\" is current directory\r\n"
        elif cmd.startswith('TYPE'):
            return b"200 Type set to ASCII\r\n"
        else:
            return b"500 Command not recognized\r\n"
    except:
        return b"500 Command error\r\n"


# =========================
# TELNET RESPONSES
# =========================

def create_telnet_banner() -> bytes:
    """Create a realistic Telnet server banner."""
    banner = b"\r\nWelcome to Telnet Server\r\n"
    banner += b"login: "
    return banner

def create_telnet_response(request: bytes) -> bytes:
    """Create Telnet response based on input."""
    try:
        data = request.decode('utf-8', errors='ignore').strip()
        
        if 'password' in data.lower() or 'pass' in data.lower():
            return b"Password: "
        else:
            return b"login: "
    except:
        return b"login: "


# =========================
# MYSQL RESPONSES
# =========================

def create_mysql_handshake() -> bytes:
    """Create a MySQL handshake/greeting packet."""
    packet = b"\x0a"  # Protocol version 10
    packet += b"5.7.31-0-log"  # Server version
    packet += b"\x00"  # Null terminator
    packet += b"\x01\x00\x00\x00"  # Connection ID
    packet += b"mysql_native_password".ljust(8, b'\x00')  # Auth plugin data (8 bytes)
    packet += b"\x00"  # Filler
    packet += b"\xff\xff"  # Server capabilities
    packet += b"\x21"  # Charset
    packet += b"\x02\x00"  # Status
    packet += b"\x00\x00"  # Server capabilities (cont)
    packet += b"\x00" * 13  # Reserved
    return packet

def create_mysql_response(request: bytes) -> bytes:
    """Create MySQL response to authentication attempts."""
    if len(request) < 4:
        return create_mysql_handshake()
    
    # Simple response indicating auth needed
    error = b"\xff"  # Error marker
    error += b"\x15\x04"  # Error code (1045 = Access Denied)
    error += b"#28000"  # SQL State
    error += b"Access denied for user"
    return error


# =========================
# POSTGRESQL RESPONSES
# =========================

def create_postgresql_startup() -> bytes:
    """Create PostgreSQL startup response."""
    # PostgreSQL authentication required
    response = b"R"  # Authentication request
    response += b"\x00\x00\x00\x08"  # Message length
    response += b"\x00\x00\x00\x03"  # Authentication type: MD5
    return response

def create_postgresql_response(request: bytes) -> bytes:
    """Create PostgreSQL response to connection attempts."""
    # Error response
    response = b"E"  # Error response
    response += b"\x00\x00\x00\x5a"  # Length
    response += b"SFATAL"  # Severity (localized)
    response += b"\x00C"  # Error code
    response += b"28P01"  # PostgreSQL error code
    response += b"\x00M"  # Message
    response += b"FATAL:  password authentication failed for user"
    response += b"\x00"
    return response


# =========================
# REDIS RESPONSES
# =========================

def create_redis_response(request: bytes) -> bytes:
    """Create Redis response based on command."""
    try:
        data = request.decode('utf-8', errors='ignore').strip()
        
        if data.startswith('*'):
            # RESP (Redis Serialization Protocol)
            if 'PING' in data.upper():
                return b"+PONG\r\n"
            elif 'COMMAND' in data.upper():
                return b"*0\r\n"
            elif 'INFO' in data.upper():
                info = b"# Server\r\nredis_version:5.0.0\r\nredis_mode:standalone\r\n"
                return b"$" + str(len(info)).encode() + b"\r\n" + info + b"\r\n"
            else:
                # Generic OK response
                return b"+OK\r\n"
        else:
            # Simple string protocol
            return b"+OK\r\n"
    except:
        return b"+OK\r\n"


# =========================
# MONGODB RESPONSES
# =========================

def create_mongodb_response(request: bytes) -> bytes:
    """Create MongoDB wire protocol response."""
    try:
        # MongoDB wire protocol - basic handshake
        # OpMsg response to client connection
        if len(request) > 4:
            return b"\x01\x00\x00\x00"  # Response to connection attempt
        else:
            # Error response
            error_msg = b"unauthorized"
            response = b"\x00\x00\x00\x00"  # Flags
            response += error_msg
            return response
    except:
        return b""


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
    elif port == 21:
        return 'ftp'
    elif port == 23:
        return 'telnet'
    elif port == 3306:
        return 'mysql'
    elif port == 5432:
        return 'postgresql'
    elif port == 6379:
        return 'redis'
    elif port == 27017:
        return 'mongodb'
    elif port == 53:
        return 'dns'
    elif port == 1900:
        if b'M-SEARCH' in data:
            return 'ssdp'
    
    # Default heuristic: check if it looks like text protocol
    if data[:4].startswith(b'GET ') or data[:4].startswith(b'POST'):
        return 'http'
    
    return 'unknown'
