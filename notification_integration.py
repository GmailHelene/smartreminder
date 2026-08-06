#!/usr/bin/env python3
"""
Notification System Integration
This file integrates all notification systems together:
1. WebPush notifications (original system)
2. Simple notifications (new client-side system)
3. Mock mode for testing
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import notification modules
try:
    from push_service import send_push_notification as webpush_send_notification
    from push_service import send_reminder_notification as webpush_send_reminder
    from push_service import send_board_notification as webpush_send_board
    from push_service import send_password_reset_notification as webpush_send_reset
    WEBPUSH_AVAILABLE = True
except Exception as e:
    print(f"WebPush not available: {e}")
    WEBPUSH_AVAILABLE = False

# Import simple notification system
from notification_simple import (
    create_notification,
    send_reminder_notification as simple_send_reminder,
    send_board_notification as simple_send_board,
    send_password_reset_notification as simple_send_reset
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Define the active notification systems
NOTIFICATION_SYSTEMS = []

# Add WebPush if available
if WEBPUSH_AVAILABLE:
    NOTIFICATION_SYSTEMS.append('webpush')

# Always add simple notifications
NOTIFICATION_SYSTEMS.append('simple')

def send_notification(user_email, title, body, data=None, dm=None):
    """Send notification using all available systems"""
    results = []
    
    if 'webpush' in NOTIFICATION_SYSTEMS:
        try:
            webpush_result = webpush_send_notification(user_email, title, body, data, dm)
            results.append(('webpush', webpush_result))
        except Exception as e:
            logger.error(f"Error sending WebPush notification: {e}")
            results.append(('webpush', False))
    
    if 'simple' in NOTIFICATION_SYSTEMS:
        try:
            options = data or {}
            options['title'] = title
            options['message'] = body
            notification_id = create_notification(user_email, title, body, options)
            results.append(('simple', bool(notification_id)))
        except Exception as e:
            logger.error(f"Error sending simple notification: {e}")
            results.append(('simple', False))
    
    # Return True if at least one system was successful
    return any(result for system, result in results)

def send_reminder_notification(user_email, reminder_title, reminder_time, sound=None, dm=None):
    """Send reminder notification using all available systems"""
    results = []
    
    if 'webpush' in NOTIFICATION_SYSTEMS:
        try:
            webpush_result = webpush_send_reminder(user_email, reminder_title, reminder_time, sound, dm)
            results.append(('webpush', webpush_result))
        except Exception as e:
            logger.error(f"Error sending WebPush reminder: {e}")
            results.append(('webpush', False))
    
    if 'simple' in NOTIFICATION_SYSTEMS:
        try:
            simple_result = simple_send_reminder(user_email, reminder_title, reminder_time, sound)
            results.append(('simple', bool(simple_result)))
        except Exception as e:
            logger.error(f"Error sending simple reminder: {e}")
            results.append(('simple', False))
    
    # Return True if at least one system was successful
    return any(result for system, result in results)

def send_board_notification(board_id, action, content, exclude_user=None, dm=None):
    """Send board notification using all available systems"""
    results = []
    
    if 'webpush' in NOTIFICATION_SYSTEMS:
        try:
            webpush_result = webpush_send_board(board_id, action, content, exclude_user, dm)
            results.append(('webpush', webpush_result))
        except Exception as e:
            logger.error(f"Error sending WebPush board notification: {e}")
            results.append(('webpush', False))
    
    if 'simple' in NOTIFICATION_SYSTEMS:
        try:
            simple_result = simple_send_board(board_id, action, content, exclude_user)
            results.append(('simple', bool(simple_result)))
        except Exception as e:
            logger.error(f"Error sending simple board notification: {e}")
            results.append(('simple', False))
    
    # Return True if at least one system was successful
    return any(result for system, result in results)

def send_password_reset_notification(user_email, reset_token, dm=None):
    """Send password reset notification using all available systems"""
    results = []
    
    if 'webpush' in NOTIFICATION_SYSTEMS:
        try:
            webpush_result = webpush_send_reset(user_email, reset_token, dm)
            results.append(('webpush', webpush_result))
        except Exception as e:
            logger.error(f"Error sending WebPush password reset: {e}")
            results.append(('webpush', False))
    
    if 'simple' in NOTIFICATION_SYSTEMS:
        try:
            simple_result = simple_send_reset(user_email, reset_token)
            results.append(('simple', bool(simple_result)))
        except Exception as e:
            logger.error(f"Error sending simple password reset: {e}")
            results.append(('simple', False))
    
    # Return True if at least one system was successful
    return any(result for system, result in results)

def get_vapid_public_key():
    """Get VAPID public key for push notifications"""
    try:
        # Try to get from environment or config
        vapid_key = os.environ.get('VAPID_PUBLIC_KEY')
        if vapid_key:
            return vapid_key
        
        # Try to get from push service
        if WEBPUSH_AVAILABLE:
            try:
                from push_service import get_vapid_public_key as get_key
                return get_key()
            except Exception as e:
                logger.error(f"Error getting VAPID key from push service: {e}")
        
        # Return a default/placeholder key for development
        return "BN4ZvYrQPF9U8J7F0G6TjW7vKKYZvW1fXZqQWZ9b0xRzQF1J8nOZ2vJF7W4UvY9X6sT8Q1fN3zQ0pR2wV4uY7g"
        
    except Exception as e:
        logger.error(f"Error getting VAPID public key: {e}")
        return None

# If this file is run directly, test the integrated notification system
if __name__ == "__main__":
    import argparse
    
    # Import data manager
    from models import data_manager as dm
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the integrated notification system')
    parser.add_argument('user_email', nargs='?', help='User email to send notification to')
    parser.add_argument('--list-systems', action='store_true', help='List active notification systems')
    args = parser.parse_args()
    
    if args.list_systems:
        print("Active notification systems:")
        for system in NOTIFICATION_SYSTEMS:
            print(f"- {system}")
        sys.exit(0)
    
    # Get user email from command line or use default
    user_email = args.user_email
    if not user_email:
        # Try to get the first user from the data
        users = dm.load_data('users', {})
        if users:
            user_email = list(users.keys())[0]
        else:
            user_email = "test-user-123"
            print(f"⚠️ No users found, using default: {user_email}")
    
    print(f"Testing notification systems for user: {user_email}")
    
    # Test notification
    result = send_notification(
        user_email=user_email,
        title="🔔 Integrated Test",
        body="Testing the integrated notification system",
        data={
            "type": "test",
            "timestamp": datetime.now().isoformat(),
            "sound": "pristine.mp3",
            "url": "/dashboard"
        },
        dm=dm
    )
    
    if result:
        print("✅ Test notification sent successfully!")
    else:
        print("❌ Failed to send notification on all systems")
