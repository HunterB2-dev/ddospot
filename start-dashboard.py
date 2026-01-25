#!/usr/bin/env python3
"""
DDoSPot Dashboard Entry Point

Run: python start-dashboard.py
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

if __name__ == "__main__":
    from app.dashboard import create_app, logger
    
    try:
        logger.info("Starting DDoSPot dashboard...")
        app = create_app()
        app.run(debug=False, host='127.0.0.1', port=5000, threaded=True)
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        sys.exit(1)
