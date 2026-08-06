#!/usr/bin/env python3
"""
Health check script for Railway deployment
"""

import sys
import os

def check_imports():
    """Check if all required modules can be imported"""
    try:
        import flask
        print("✓ Flask imported successfully")
        
        import werkzeug
        print("✓ Werkzeug imported successfully")
        
        import flask_login
        print("✓ Flask-Login imported successfully")
        
        import flask_wtf
        print("✓ Flask-WTF imported successfully")
        
        import wtforms
        print("✓ WTForms imported successfully")
        
        import flask_mail
        print("✓ Flask-Mail imported successfully")
        
        import email_validator
        print("✓ Email-validator imported successfully")
        
        import apscheduler
        print("✓ APScheduler imported successfully")
        
        import requests
        print("✓ Requests imported successfully")
        
        import gunicorn
        print("✓ Gunicorn imported successfully")
        
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_app():
    """Check if the app can be created"""
    try:
        # Set environment for testing
        os.environ['FLASK_ENV'] = 'production'
        os.environ['SECRET_KEY'] = 'test-key'
        
        from app import app
        print("✓ App created successfully")
        
        # Test health endpoint
        with app.test_client() as client:
            response = client.get('/health')
            if response.status_code == 200:
                print("✓ Health endpoint works")
                return True
            else:
                print(f"❌ Health endpoint returned {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ App creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    print("🔍 Checking Railway deployment health...")
    
    if not check_imports():
        print("❌ Import check failed")
        sys.exit(1)
    
    if not check_app():
        print("❌ App check failed")
        sys.exit(1)
    
    print("✅ All checks passed!")
    return 0

if __name__ == "__main__":
    sys.exit(main())
