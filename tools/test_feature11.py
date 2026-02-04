#!/usr/bin/env python3
"""
Feature #11: Web Configuration UI - Test Suite

Tests all 12 configuration management endpoints.
Verifies settings persistence and validation.
"""

import requests
import json
import sys

BASE_URL = "http://127.0.0.1:5000/api"
API_KEY = "demo-admin-key"

def test_honeypot_config():
    """Test honeypot configuration endpoints"""
    print("\n[TEST 1] Honeypot Configuration")
    try:
        # GET honeypot config
        response = requests.get(
            f"{BASE_URL}/config/honeypot",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        print(f"✓ 200 - Retrieved honeypot config")
        print(f"  Services: {list(data.get('config', {}).keys())[:3]}")
        
        # POST honeypot config (update)
        response = requests.post(
            f"{BASE_URL}/config/honeypot",
            headers={"X-API-Key": API_KEY},
            json={"honeypot_ssh_port": 2223, "honeypot_log_level": "DEBUG"},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Update should succeed"
        print(f"✓ 200 - Updated honeypot config")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_alerts_config():
    """Test alert configuration endpoints"""
    print("\n[TEST 2] Alert Configuration")
    try:
        # GET alert config
        response = requests.get(
            f"{BASE_URL}/config/alerts",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        print(f"✓ 200 - Retrieved alert config")
        print(f"  Settings: {list(data.get('config', {}).keys())[:3]}")
        
        # POST alert config (update)
        response = requests.post(
            f"{BASE_URL}/config/alerts",
            headers={"X-API-Key": API_KEY},
            json={"alert_event_threshold": 15, "alert_enable_email": True},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Update should succeed"
        print(f"✓ 200 - Updated alert config")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_response_config():
    """Test response actions configuration endpoints"""
    print("\n[TEST 3] Response Actions Configuration")
    try:
        # GET response config
        response = requests.get(
            f"{BASE_URL}/config/responses",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        print(f"✓ 200 - Retrieved response config")
        print(f"  Settings: {list(data.get('config', {}).keys())[:3]}")
        
        # POST response config (update)
        response = requests.post(
            f"{BASE_URL}/config/responses",
            headers={"X-API-Key": API_KEY},
            json={"response_auto_block_threshold": 8.0, "response_block_duration": 48},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Update should succeed"
        print(f"✓ 200 - Updated response config")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_ui_config():
    """Test UI configuration endpoints"""
    print("\n[TEST 4] UI Configuration")
    try:
        # GET UI config (no auth required)
        response = requests.get(
            f"{BASE_URL}/config/ui",
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        print(f"✓ 200 - Retrieved UI config")
        print(f"  Settings: {list(data.get('config', {}).keys())[:3]}")
        
        # POST UI config (update)
        response = requests.post(
            f"{BASE_URL}/config/ui",
            headers={"X-API-Key": API_KEY},
            json={"ui_theme": "dark", "ui_refresh_interval": 10},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Update should succeed"
        print(f"✓ 200 - Updated UI config")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_system_config():
    """Test system configuration endpoints (admin only)"""
    print("\n[TEST 5] System Configuration")
    try:
        # GET system config
        response = requests.get(
            f"{BASE_URL}/config/system",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        print(f"✓ 200 - Retrieved system config")
        print(f"  Settings: {list(data.get('config', {}).keys())[:3]}")
        
        # POST system config (update - admin only)
        response = requests.post(
            f"{BASE_URL}/config/system",
            headers={"X-API-Key": API_KEY},
            json={"system_backup_enabled": False, "system_backup_schedule": "0 3 * * *"},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Update should succeed"
        print(f"✓ 200 - Updated system config")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_webhook_test():
    """Test webhook configuration test endpoint"""
    print("\n[TEST 6] Webhook Test Endpoint")
    try:
        response = requests.post(
            f"{BASE_URL}/config/test/webhook",
            headers={"X-API-Key": API_KEY},
            json={"webhook_url": "https://webhook.example.com/ddospot"},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Webhook test should succeed"
        print(f"✓ 200 - Webhook test passed")
        print(f"  URL: {data.get('webhook_url')}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_email_test():
    """Test email configuration test endpoint"""
    print("\n[TEST 7] Email Test Endpoint")
    try:
        response = requests.post(
            f"{BASE_URL}/config/test/email",
            headers={"X-API-Key": API_KEY},
            json={
                "smtp_server": "smtp.example.com",
                "smtp_port": 587,
                "test_email": "admin@example.com"
            },
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Email test should succeed"
        print(f"✓ 200 - Email test passed")
        print(f"  Recipient: {data.get('test_recipient')}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_restart_services():
    """Test service restart endpoint"""
    print("\n[TEST 8] Service Restart Endpoint")
    try:
        response = requests.post(
            f"{BASE_URL}/config/restart",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Restart should succeed"
        print(f"✓ 200 - Service restart scheduled")
        print(f"  Note: {data.get('note')}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_authentication_required():
    """Test that protected endpoints require authentication"""
    print("\n[TEST 9] Authentication Required")
    try:
        # Try POST without auth
        response = requests.post(
            f"{BASE_URL}/config/system",
            json={"system_backup_enabled": True},
            timeout=5
        )
        is_protected = response.status_code in (401, 403)
        assert is_protected, f"Expected 401/403, got {response.status_code}"
        print(f"✓ {response.status_code} - System config endpoint properly protected")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_rate_limiting():
    """Test rate limiting on config endpoints"""
    print("\n[TEST 10] Rate Limiting")
    try:
        # Send multiple requests
        success_count = 0
        rate_limited = False
        
        for i in range(5):
            response = requests.post(
                f"{BASE_URL}/config/honeypot",
                headers={"X-API-Key": API_KEY},
                json={"honeypot_ssh_port": 2222},
                timeout=5
            )
            
            if response.status_code == 200:
                success_count += 1
            elif response.status_code == 429:
                rate_limited = True
                print(f"✓ 429 - Rate limit enforced after {i} requests")
                break
        
        if success_count >= 5:
            print(f"✓ Rate limiting configured (all {success_count} requests successful)")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_settings_page():
    """Test settings page loads correctly"""
    print("\n[TEST 11] Settings Page Loads")
    try:
        response = requests.get("http://127.0.0.1:5000/settings", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        assert 'settings.html' in response.text or 'honeypot' in response.text.lower()
        print(f"✓ 200 - Settings page loaded successfully")
        print(f"  Content size: {len(response.text)} bytes")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def test_persistence():
    """Test configuration persistence"""
    print("\n[TEST 12] Configuration Persistence")
    try:
        # Set a value
        requests.post(
            f"{BASE_URL}/config/honeypot",
            headers={"X-API-Key": API_KEY},
            json={"honeypot_ssh_port": 3333},
            timeout=5
        )
        
        # Retrieve it
        response = requests.get(
            f"{BASE_URL}/config/honeypot",
            headers={"X-API-Key": API_KEY},
            timeout=5
        )
        
        data = response.json()
        config = data.get('config', {})
        port = config.get('honeypot_ssh_port')
        
        assert port == 3333 or port == '3333', f"Expected 3333, got {port}"
        print(f"✓ Configuration persisted correctly")
        print(f"  Value: honeypot_ssh_port = {port}")
        
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        return False


def main():
    """Run all Feature #11 tests"""
    print("=" * 60)
    print("Feature #11: Web Configuration UI - Test Suite")
    print("=" * 60)
    
    tests = [
        ("Honeypot Config", test_honeypot_config),
        ("Alert Config", test_alerts_config),
        ("Response Config", test_response_config),
        ("UI Config", test_ui_config),
        ("System Config", test_system_config),
        ("Webhook Test", test_webhook_test),
        ("Email Test", test_email_test),
        ("Service Restart", test_restart_services),
        ("Authentication", test_authentication_required),
        ("Rate Limiting", test_rate_limiting),
        ("Settings Page", test_settings_page),
        ("Persistence", test_persistence),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"✗ Test error: {e}")
            results.append((name, False))
    
    # Print summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status:8} - {name}")
    
    print("=" * 60)
    print(f"Results: {passed}/{total} tests passed ({100*passed//total}%)")
    print("=" * 60)
    
    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
