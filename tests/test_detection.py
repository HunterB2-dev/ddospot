#!/usr/bin/env python3
"""
Test script for DDoS detection logic.
Simulates attacks and verifies detection and blacklisting.
"""

import asyncio
import socket
import time
from concurrent.futures import ThreadPoolExecutor


def simulate_http_flood(target_ip: str = "127.0.0.1", target_port: int = 8080, count: int = 150):
    """Simulate an HTTP flood attack"""
    print(f"\n[*] Simulating HTTP flood: {count} requests to {target_ip}:{target_port}")
    
    successful = 0
    for i in range(count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((target_ip, target_port))
            
            request = b"GET / HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n"
            sock.send(request)
            
            try:
                response = sock.recv(4096)
                if b"HTTP/1.1 200" in response:
                    successful += 1
            except:
                pass
            
            sock.close()
        except Exception as e:
            pass
        
        if (i + 1) % 50 == 0:
            print(f"    Sent {i + 1}/{count} requests...")
    
    print(f"    ✓ HTTP flood complete: {successful} successful responses")
    return successful


def simulate_ssdp_flood(target_ip: str = "127.0.0.1", target_port: int = 1900, count: int = 150):
    """Simulate an SSDP amplification attack"""
    print(f"\n[*] Simulating SSDP flood: {count} requests to {target_ip}:{target_port}")
    
    successful = 0
    request = b"M-SEARCH * HTTP/1.1\r\nHOST: 239.255.255.250:1900\r\nMAN: \"ssdp:discover\"\r\nST: ssdp:all\r\n\r\n"
    
    for i in range(count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.settimeout(1)
            sock.sendto(request, (target_ip, target_port))
            
            try:
                response, _ = sock.recvfrom(4096)
                if b"HTTP/1.1 200" in response:
                    successful += 1
            except:
                pass
            
            sock.close()
        except Exception as e:
            pass
        
        if (i + 1) % 50 == 0:
            print(f"    Sent {i + 1}/{count} requests...")
    
    print(f"    ✓ SSDP flood complete: {successful} successful responses")
    return successful


def simulate_ssh_connection_flood(target_ip: str = "127.0.0.1", target_port: int = 2222, count: int = 100):
    """Simulate an SSH connection flood"""
    print(f"\n[*] Simulating SSH connection flood: {count} connections to {target_ip}:{target_port}")
    
    successful = 0
    for i in range(count):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            sock.connect((target_ip, target_port))
            
            try:
                banner = sock.recv(1024)
                if b"SSH-2.0" in banner:
                    successful += 1
            except:
                pass
            
            sock.close()
        except Exception as e:
            pass
        
        if (i + 1) % 25 == 0:
            print(f"    Made {i + 1}/{count} connections...")
    
    print(f"    ✓ SSH connection flood complete: {successful} successful banners")
    return successful


async def main():
    print("=" * 60)
    print("DDoSPot Detection Logic Test")
    print("=" * 60)
    
    print("\n[!] Make sure the honeypot is running: python3 main.py")
    print("[!] Testing will simulate multiple types of attacks\n")
    
    input("Press ENTER to start attacks (honeypot must be running)...")
    
    try:
        # Test 1: HTTP Flood (should trigger at ~100+ requests)
        print("\n" + "=" * 60)
        print("TEST 1: HTTP FLOOD ATTACK")
        print("=" * 60)
        await asyncio.sleep(0.5)
        http_result = await asyncio.to_thread(simulate_http_flood, "127.0.0.1", 8080, 150)
        
        # Small delay
        await asyncio.sleep(2)
        
        # Test 2: SSDP Amplification (UDP)
        print("\n" + "=" * 60)
        print("TEST 2: SSDP AMPLIFICATION ATTACK")
        print("=" * 60)
        await asyncio.sleep(0.5)
        ssdp_result = await asyncio.to_thread(simulate_ssdp_flood, "127.0.0.1", 1900, 150)
        
        # Small delay
        await asyncio.sleep(2)
        
        # Test 3: SSH Connection Flood
        print("\n" + "=" * 60)
        print("TEST 3: SSH CONNECTION FLOOD")
        print("=" * 60)
        await asyncio.sleep(0.5)
        ssh_result = await asyncio.to_thread(simulate_ssh_connection_flood, "127.0.0.1", 2222, 100)
        
        print("\n" + "=" * 60)
        print("ATTACK SIMULATION COMPLETE")
        print("=" * 60)
        print(f"\nResults:")
        print(f"  HTTP Flood:    {http_result} responses")
        print(f"  SSDP Flood:    {ssdp_result} responses")
        print(f"  SSH Flood:     {ssh_result} responses")
        
        print(f"\n[!] Check the honeypot logs to verify:")
        print(f"    - Attacks were detected")
        print(f"    - IPs were blacklisted")
        print(f"    - Attack severity was calculated")
        
        print(f"\nRun: tail -f honeypot.log")
        
    except KeyboardInterrupt:
        print("\n[!] Test interrupted")
    except Exception as e:
        print(f"\n[!] Error during testing: {e}")


if __name__ == "__main__":
    asyncio.run(main())
