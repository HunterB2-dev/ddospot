#!/usr/bin/env python3
"""
Test script to verify honeypot protocol responses.
Run this to test if the honeypot servers respond correctly to attacks.
"""

import asyncio
import socket
import sys

async def test_http():
    """Test HTTP response on port 8080"""
    print("\n[*] Testing HTTP (port 8080)...")
    writer = None
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection('127.0.0.1', 8080),
            timeout=2
        )
        
        # Send HTTP request
        request = b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
        writer.write(request)
        await writer.drain()
        
        # Read response
        response = await reader.read(4096)
        if b"HTTP/1.1 200" in response and b"Welcome" in response:
            print("    ✓ HTTP response OK")
            return True
        else:
            print(f"    ✗ Unexpected response: {response[:100]}")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    finally:
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass


async def test_ssh():
    """Test SSH banner on port 2222"""
    print("[*] Testing SSH (port 2222)...")
    writer = None
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection('127.0.0.1', 2222),
            timeout=2
        )
        
        # SSH should send banner immediately
        response = await asyncio.wait_for(reader.read(1024), timeout=1)
        
        if b"SSH-2.0" in response:
            print(f"    ✓ SSH banner received: {response.decode().strip()}")
            return True
        else:
            print(f"    ✗ Unexpected response: {response}")
            return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    finally:
        if writer:
            try:
                writer.close()
                await writer.wait_closed()
            except:
                pass


async def test_ssdp():
    """Test SSDP response on port 1900"""
    print("[*] Testing SSDP (port 1900)...")
    sock = None
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(2)
        
        # Send SSDP M-SEARCH discovery
        request = b"M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nST: ssdp:all\r\n\r\n"
        sock.sendto(request, ('127.0.0.1', 1900))
        
        # Receive response
        response, _ = sock.recvfrom(4096)
        
        if b"HTTP/1.1 200" in response and b"upnp" in response.lower():
            print("    ✓ SSDP response OK")
            return True
        else:
            print(f"    ✗ Unexpected response: {response[:100]}")
            return False
    except socket.timeout:
        print("    ✗ No response (timeout)")
        return False
    except Exception as e:
        print(f"    ✗ Error: {e}")
        return False
    finally:
        if sock:
            sock.close()


async def main():
    print("=" * 50)
    print("DDoSPot Honeypot Protocol Response Tests")
    print("=" * 50)
    
    results = []
    results.append(("HTTP", await test_http()))
    results.append(("SSH", await test_ssh()))
    results.append(("SSDP", await test_ssdp()))
    
    print("\n" + "=" * 50)
    print("Test Summary:")
    print("=" * 50)
    for protocol, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{protocol:10} {status}")
    
    total_passed = sum(1 for _, p in results if p)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")


if __name__ == "__main__":
    asyncio.run(main())
