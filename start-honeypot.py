#!/usr/bin/env python3
"""
DDoSPot Honeypot Entry Point

Run: python start-honeypot.py
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Change to project root directory so relative paths work correctly
os.chdir(project_root)

if __name__ == "__main__":
    from app.main import asyncio, main, signal, logger
    
    try:
        logger.info("Starting DDoSPot honeypot...")
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Honeypot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Honeypot error: {e}")
        sys.exit(1)
