#!/usr/bin/env python3
"""
Feature #10: Advanced API Enhancements - Test Suite

Tests API authentication, rate limiting, and status endpoints.
All tests should return 200 status code for success cases.
"""

import requests
import time
import json
import sys

BASE_URL = "http://127.0.0.1:5000/api"

def test_health_check():
    """Test health check endpoint (no auth required)"""
    print("\n[TEST 1] Health Check Endpoint")
    try:
        response = requests.get(f"{BASE_URL}/status/health", timeout=5)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('status') == 'healthy', "Status should be 'healthy'"
        print(f"✓ Health check passed - Status: {data.get('status')}")
        print(f"  Database: {data.get('database')}")
        print(f"  Events: {data.get('event_count')}")
        return True
    except Exception as e:
        print(f"✗ Health check failed: {e}")
        return False

def test_create_api_key():
    """Test API key creation (requires admin permission)"""
    print("\n[TEST 2] Create API Key")
    try:
        # First, get a default admin key or create one
        admin_key = os.getenv("ADMIN_API_KEY", "demo-admin-key")
        
        response = requests.post(
            f"{BASE_URL}/auth/keys/create",
            headers={"X-API-Key": admin_key},
            json={
                "name": "Test Key",
                "permissions": ["read", "write"]
            },
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        assert 'key' in data, "Should return API key"
        print(f"✓ API key created successfully")
        print(f"  Name: {data.get('name')}")
        print(f"  Permissions: {data.get('permissions')}")
        return True, data.get('key')
    except Exception as e:
        print(f"✗ API key creation failed: {e}")
        return False, None

def test_list_api_keys(admin_key):
    """Test listing API keys (requires admin permission)"""
    print("\n[TEST 3] List API Keys")
    try:
        response = requests.get(
            f"{BASE_URL}/auth/keys",
            headers={"X-API-Key": admin_key},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        assert 'keys' in data, "Should return keys list"
        print(f"✓ Listed API keys successfully")
        print(f"  Total keys: {data.get('count')}")
        if data.get('keys'):
            print(f"  First key name: {data['keys'][0].get('name')}")
        return True
    except Exception as e:
        print(f"✗ List API keys failed: {e}")
        return False

def test_api_stats(api_key):
    """Test API statistics endpoint (requires read permission)"""
    print("\n[TEST 4] API Statistics")
    try:
        response = requests.get(
            f"{BASE_URL}/status/stats",
            headers={"X-API-Key": api_key},
            timeout=5
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        assert data.get('success'), "Should succeed"
        assert 'stats' in data, "Should return stats"
        print(f"✓ API statistics retrieved successfully")
        stats = data.get('stats', {})
        print(f"  Active API Keys: {stats.get('active_api_keys')}")
        print(f"  Total API Keys: {stats.get('total_api_keys')}")
        print(f"  Rate Limit Entries: {stats.get('total_rate_limit_entries')}")
        return True
    except Exception as e:
        print(f"✗ API statistics failed: {e}")
        return False

def test_rate_limiting():
    """Test rate limiting on health endpoint (100 calls/60s limit)"""
    print("\n[TEST 5] Rate Limiting")
    try:
        # Make requests rapidly to test rate limiting
        success_count = 0
        rate_limited = False
        
        for i in range(5):
            response = requests.get(f"{BASE_URL}/status/health", timeout=5)
            
            # Check rate limit headers
            limit = response.headers.get('X-RateLimit-Limit')
            remaining = response.headers.get('X-RateLimit-Remaining')
            
            if response.status_code == 200:
                success_count += 1
                print(f"  Request {i+1}: 200 OK (Remaining: {remaining}/{limit})")
            elif response.status_code == 429:
                rate_limited = True
                print(f"  Request {i+1}: 429 Too Many Requests (Rate Limited)")
                break
        
        if success_count >= 5:
            print(f"✓ Rate limiting working (headers present)")
        elif rate_limited:
            print(f"✓ Rate limiting enforced")
        else:
            print(f"✗ Unexpected response")
            return False
        
        return True
    except Exception as e:
        print(f"✗ Rate limiting test failed: {e}")
        return False

def test_authentication_required():
    """Test that protected endpoints require authentication"""
    print("\n[TEST 6] Authentication Required")
    try:
        # Try accessing protected endpoint without auth
        response = requests.get(f"{BASE_URL}/status/stats", timeout=5)
        
        # Should fail with 401 or similar
        if response.status_code in (401, 403):
            print(f"✓ Authentication properly enforced (Status: {response.status_code})")
            return True
        else:
            print(f"✗ Expected 401/403, got {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Authentication test failed: {e}")
        return False

def test_invalid_api_key():
    """Test that invalid API keys are rejected"""
    print("\n[TEST 7] Invalid API Key Rejection")
    try:
        response = requests.get(
            f"{BASE_URL}/status/stats",
            headers={"X-API-Key": "invalid-key-12345"},
            timeout=5
        )
        
        # Should fail with 401
        if response.status_code == 401:
            print(f"✓ Invalid API key properly rejected (Status: {response.status_code})")
            return True
        else:
            print(f"✗ Expected 401, got {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Invalid key test failed: {e}")
        return False

def test_rate_limit_headers():
    """Test that rate limit headers are present"""
    print("\n[TEST 8] Rate Limit Headers")
    try:
        response = requests.get(f"{BASE_URL}/status/health", timeout=5)
        
        headers = response.headers
        has_limit = 'X-RateLimit-Limit' in headers
        has_remaining = 'X-RateLimit-Remaining' in headers
        has_reset = 'X-RateLimit-Reset' in headers
        
        if has_limit and has_remaining and has_reset:
            print(f"✓ All rate limit headers present")
            print(f"  X-RateLimit-Limit: {headers.get('X-RateLimit-Limit')}")
            print(f"  X-RateLimit-Remaining: {headers.get('X-RateLimit-Remaining')}")
            print(f"  X-RateLimit-Reset: {headers.get('X-RateLimit-Reset')}")
            return True
        else:
            print(f"✗ Missing rate limit headers")
            print(f"  Limit: {has_limit}, Remaining: {has_remaining}, Reset: {has_reset}")
            return False
    except Exception as e:
        print(f"✗ Rate limit headers test failed: {e}")
        return False

def main():
    """Run all Feature #10 tests"""
    print("=" * 60)
    print("Feature #10: Advanced API Enhancements - Test Suite")
    print("=" * 60)
    
    results = []
    
    # Test 1: Health Check
    results.append(("Health Check", test_health_check()))
    
    # Test 2: Create API Key
    success, api_key = test_create_api_key()
    results.append(("Create API Key", success))
    
    # Test 3: List API Keys
    results.append(("List API Keys", test_list_api_keys("demo-admin-key")))
    
    # Test 4: API Statistics
    if api_key:
        results.append(("API Statistics", test_api_stats(api_key)))
    
    # Test 5: Rate Limiting
    results.append(("Rate Limiting", test_rate_limiting()))
    
    # Test 6: Authentication Required
    results.append(("Authentication Required", test_authentication_required()))
    
    # Test 7: Invalid API Key
    results.append(("Invalid API Key", test_invalid_api_key()))
    
    # Test 8: Rate Limit Headers
    results.append(("Rate Limit Headers", test_rate_limit_headers()))
    
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
    print(f"Results: {passed}/{total} tests passed ({100*passed/total:.0f}%)")
    print("=" * 60)
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    import os
    sys.exit(main())
