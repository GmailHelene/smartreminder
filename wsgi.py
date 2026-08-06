"""
WSGI entry point for production deployment
"""

import os
import sys
from pathlib import Path

# Add project directory to path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Set production environment explicitly for Railway
os.environ.setdefault('FLASK_ENV', 'production')
os.environ.setdefault('FLASK_APP', 'app.py')

# Ensure we have a secret key for production
if not os.environ.get('SECRET_KEY'):
    import secrets
    os.environ['SECRET_KEY'] = secrets.token_hex(32)
    print("Warning: Using generated SECRET_KEY. Set SECRET_KEY environment variable for production.")

try:
    from app import app as application
    
    # Ensure the app is configured for production
    if application.config.get('ENV') != 'production':
        application.config['ENV'] = 'production'
        application.config['DEBUG'] = False
        
except ImportError as e:
    print(f"Import error: {e}")
    import traceback
    traceback.print_exc()
    raise

if __name__ == "__main__":
    port = int(os.environ.get('PORT', 8000))
    application.run(host='0.0.0.0', port=port)
