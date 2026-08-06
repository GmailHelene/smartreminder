"""
Mock Push Notification Service for SmartReminder
Provides working notifications without VAPID key issues
"""

import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def send_push_notification(user_email, title, body, data=None, dm=None):
    """Mock push notification sender for testing"""
    if not dm:
        logger.error("No data manager provided")
        return False
        
    try:
        # Load subscriptions (ensure proper structure)
        subscriptions_data = dm.load_data('push_subscriptions', {})
        
        # Handle case where data might be loaded as a list instead of dict
        if isinstance(subscriptions_data, list):
            subscriptions_data = {}
            dm.save_data('push_subscriptions', subscriptions_data)
        elif not isinstance(subscriptions_data, dict):
            subscriptions_data = {}
            dm.save_data('push_subscriptions', subscriptions_data)
        
        user_subscriptions = subscriptions_data.get(user_email, [])
        
        # Mock successful push notification
        print(f"🔔 MOCK PUSH: {title} -> {user_email}")
        print(f"   Body: {body}")
        if data:
            print(f"   Sound: {data.get('sound', 'None')}")
            print(f"   Priority: {data.get('priority', 'normal')}")
        print(f"   Subscriptions: {len(user_subscriptions)}")
        
        # Log the notification for debugging
        logger.info(f"Mock push notification sent to {user_email}: {title}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error in mock push notification: {e}")
        return False

def send_reminder_notification(user_email, reminder_title, reminder_time, sound=None, dm=None):
    """Send notification for upcoming reminder"""
    title = "⏰ Påminnelse"
    body = f"{reminder_title} - {reminder_time}"
    
    notification_data = {
        "type": "reminder",
        "title": reminder_title,
        "time": reminder_time,
        "url": "/dashboard"
    }
    
    # Add sound if provided
    if sound:
        notification_data["sound"] = sound
    
    return send_push_notification(user_email, title, body, notification_data, dm)

def send_shared_reminder_notification(user_email, title, body, data=None, dm=None):
    """Send notification for shared reminder"""
    return send_push_notification(user_email, title, body, data, dm)

def send_board_notification(board_id, action, content, exclude_user=None, dm=None):
    """Send notification to all board members except the user who performed the action"""
    print(f"🔔 MOCK BOARD NOTIFICATION: {action} on board {board_id}")
    return True

def subscribe_user_to_push(user_email, subscription_data, dm=None):
    """Subscribe user to push notifications"""
    print(f"🔔 MOCK SUBSCRIBE: {user_email} to push notifications")
    
    if dm:
        subscriptions = dm.load_data('push_subscriptions', {})
        if not isinstance(subscriptions, dict):
            subscriptions = {}
        
        if user_email not in subscriptions:
            subscriptions[user_email] = []
        
        subscription_data['subscribed_at'] = datetime.now().isoformat()
        subscriptions[user_email].append(subscription_data)
        dm.save_data('push_subscriptions', subscriptions)
    
    return True

def get_vapid_public_key():
    """Return mock VAPID public key"""
    return "MOCK_VAPID_PUBLIC_KEY"

def send_password_reset_notification(user_email, reset_token, dm=None):
    """Send password reset notification to user"""
    print(f"🔔 MOCK PASSWORD RESET: {user_email}")
    return True
