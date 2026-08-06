#!/usr/bin/env python3
"""
Production-ready startup script for Smart Påminner Pro
"""

import os
import sys
import logging
from pathlib import Path

# Set environment
os.environ.setdefault('FLASK_ENV', 'production')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main application entry point"""
    try:
        logger.info("🚀 Starting Smart Påminner Pro...")
        
        # Import and initialize app
        from app import app
        
        # Verify critical routes are registered
        with app.app_context():
            critical_routes = ['dashboard', 'noteboards', 'focus_modes', 'email_settings']
            registered_routes = [rule.endpoint for rule in app.url_map.iter_rules()]
            
            missing_routes = []
            for route in critical_routes:
                if route not in registered_routes:
                    missing_routes.append(route)
            
            if missing_routes:
                logger.error(f"❌ Missing critical routes: {missing_routes}")
                logger.error(f"Available routes: {sorted(registered_routes)}")
                sys.exit(1)
            else:
                logger.info(f"✅ All critical routes registered: {critical_routes}")
        
        # Get port from environment
        port = int(os.environ.get('PORT', 8000))
        
        logger.info(f"🌐 Starting server on port {port}")
        
        # Start the app
        app.run(host='0.0.0.0', port=port, debug=False)
        
    except Exception as e:
        logger.error(f"❌ Failed to start application: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()
