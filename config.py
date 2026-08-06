"""
Configuration for Smart Påminner Pro
"""

import os
from pathlib import Path

# Try to load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, use os.environ directly
    pass

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')
    
    # App settings
    REMINDER_CHECK_INTERVAL = int(os.environ.get('REMINDER_CHECK_INTERVAL') or 300)
    NOTIFICATION_ADVANCE_MINUTES = int(os.environ.get('NOTIFICATION_ADVANCE_MINUTES') or 15)
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Session settings
    PERMANENT_SESSION_LIFETIME = 3600 * 24 * 7  # 7 days

    # Cookie security (base defaults; ProductionConfig tightens Secure further)
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = 'Lax'
    PREFERRED_URL_SCHEME = 'https'

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    WTF_CSRF_ENABLED = True
    MAIL_SUPPRESS_SEND = False

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    WTF_CSRF_ENABLED = False
    MAIL_SUPPRESS_SEND = True
    SECRET_KEY = 'test-secret-key'
    REMINDER_CHECK_INTERVAL = 30  # Shorter interval for testing
    NOTIFICATION_ADVANCE_MINUTES = 5

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    WTF_CSRF_ENABLED = True
    
    # HTTPS-only in production. Railway terminates TLS and 301-redirects HTTP->HTTPS,
    # so Secure cookies are safe by default. Opt out only for a non-HTTPS staging box
    # via DISABLE_SECURE_COOKIES=true.
    SESSION_COOKIE_SECURE = os.environ.get('DISABLE_SECURE_COOKIES', 'false').lower() not in ['true', '1', 'yes']
    REMEMBER_COOKIE_SECURE = SESSION_COOKIE_SECURE
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

# Velg konfigurasjon basert på miljø
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}