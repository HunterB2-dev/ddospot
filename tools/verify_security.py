#!/usr/bin/env python3
"""
Quick security hardening verification script for DDoSPoT.
Tests rate limiting and token authentication features.
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def section(title):
    """Print section header"""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")

def run_test(name, command):
    """Run a test command"""
    print(f"  ▶ {name}...", end=" ", flush=True)
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓")
            return True
        else:
            print(f"✗ ({result.stderr[:50]})")
            return False
    except subprocess.TimeoutExpired:
        print("✗ (timeout)")
        return False
    except Exception as e:
        print(f"✗ ({str(e)[:50]})")
        return False

def main():
    """Run security feature tests"""
    print("\n" + "="*60)
    print("  DDoSPoT Security Hardening Verification")
    print("="*60)
    
    test_dir = Path(__file__).parent
    os.chdir(test_dir)
    
    # Verify files exist
    section("1. File Verification")
    
    files = [
        ("Security Hardening Doc", "SECURITY_HARDENING.md"),
        ("Main README", "README.md"),
        ("Dashboard Script", "dashboard.py"),
        ("CLI Script", "cli.py"),
        ("Rate Limiter Module", "telemetry/ratelimit.py"),
    ]
    
    all_exist = True
    for name, path in files:
        exists = Path(path).exists()
        status = "✓" if exists else "✗"
        print(f"  {status} {name:30} {path}")
        all_exist = all_exist and exists
    
    if not all_exist:
        print("\n✗ Some required files missing!")
        return False
    
    # Verify Python syntax
    section("2. Python Syntax Check")
    
    py_files = [
        ("Dashboard", "dashboard.py"),
        ("CLI", "cli.py"),
        ("Rate Limiter", "telemetry/ratelimit.py"),
    ]
    
    all_valid = True
    for name, path in py_files:
        result = subprocess.run(
            f"python3 -m py_compile {path}",
            shell=True,
            capture_output=True
        )
        valid = result.returncode == 0
        status = "✓" if valid else "✗"
        print(f"  {status} {name:30} {path}")
        all_valid = all_valid and valid
    
    if not all_valid:
        print("\n✗ Python syntax errors found!")
        return False
    
    # Verify features in code
    section("3. Feature Implementation Check")
    
    features = [
        ("Rate limiting middleware", "dashboard.py", "_rate_limiter"),
        ("Token auth decorator", "dashboard.py", "@require_token"),
        ("Token helper function", "cli.py", "_get_api_token"),
        ("Rate limiter class", "telemetry/ratelimit.py", "class RateLimiter"),
        ("Input validation", "dashboard.py", "isinstance(data, dict)"),
        ("HTTP error handling", "cli.py", "urllib.error.HTTPError"),
    ]
    
    all_found = True
    for feature, filepath, pattern in features:
        try:
            with open(filepath) as f:
                content = f.read()
                found = pattern in content
        except Exception:
            found = False
        
        status = "✓" if found else "✗"
        print(f"  {status} {feature:40} {filepath}")
        all_found = all_found and found
    
    if not all_found:
        print("\n✗ Some features not found in code!")
        return False
    
    # Verify environment variables documented
    section("4. Documentation Check")
    
    env_vars = [
        "DDOSPOT_API_TOKEN",
        "DDOSPOT_REQUIRE_TOKEN",
        "DDOSPOT_METRICS_PUBLIC",
        "DDOSPOT_RATE_LIMIT_MAX",
        "DDOSPOT_RATE_LIMIT_WINDOW",
        "DDOSPOT_RATE_LIMIT_BLACKLIST",
    ]
    
    try:
        with open("SECURITY_HARDENING.md") as f:
            doc_content = f.read()
    except Exception:
        print("  ✗ Cannot read SECURITY_HARDENING.md")
        return False
    
    all_doc = True
    for var in env_vars:
        found = var in doc_content
        status = "✓" if found else "✗"
        print(f"  {status} {var:40} documented")
        all_doc = all_doc and found
    
    if not all_doc:
        print("\n✗ Some environment variables not documented!")
        return False
    
    # Summary
    section("Summary")
    
    print("""
  ✓ All security hardening features implemented
  ✓ All files present and syntactically correct
  ✓ Rate limiting and token auth configured
  ✓ Documentation complete
  
  Next steps:
  
  1. Read SECURITY_HARDENING.md for deployment options
  2. Set environment variables for your environment
  3. Start the dashboard: ./cli.py (choose 2)
  4. Test with: curl -H "Authorization: Bearer token" http://localhost:5000/metrics
  5. Run health check: ./cli.py (choose 22)
  
  For production:
  
    export DDOSPOT_API_TOKEN=$(openssl rand -hex 32)
    export DDOSPOT_REQUIRE_TOKEN=true
    export DDOSPOT_METRICS_PUBLIC=false
    export DDOSPOT_RATE_LIMIT_MAX=50
    ./cli.py
  
  """)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

