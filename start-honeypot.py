#!/usr/bin/env python3
"""
DDoSPot Honeypot Entry Point

Run: python start-honeypot.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

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
