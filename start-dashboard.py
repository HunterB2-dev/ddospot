#!/usr/bin/env python3
"""
DDoSPot Dashboard Entry Point

Run: python start-dashboard.py
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
    from app.dashboard import create_app, logger
    
    try:
        # Ensure dashboard is accessible from all interfaces
        os.environ['FLASK_ENV'] = 'production'
        
        logger.info("Starting DDoSPot dashboard...")
        app = create_app()
        
        # Run with explicit configuration
        app.run(
            debug=False,
            host='0.0.0.0',
            port=5000,
            threaded=True,
            use_reloader=False
        )
    except KeyboardInterrupt:
        logger.info("Dashboard stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        sys.exit(1)
