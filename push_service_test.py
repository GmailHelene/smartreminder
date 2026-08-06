"""
Test Push Notification Service for SmartReminder
Mock implementation for testing push notifications
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
        # Load subscriptions
        subscriptions_data = dm.load_data('push_subscriptions')
        user_subscriptions = subscriptions_data.get(user_email, [])
        
        if not user_subscriptions:
            logger.info(f"No push subscriptions found for user {user_email}")
            return False
        
        # Mock success for testing
        logger.info(f"MOCK: Would send push notification to {user_email}")
        logger.info(f"MOCK: Title: {title}")
        logger.info(f"MOCK: Body: {body}")
        logger.info(f"MOCK: Data: {data}")
        logger.info(f"MOCK: Found {len(user_subscriptions)} subscriptions")
        
        # Log the notification for debugging
        notifications_log = dm.load_data('notifications_log')
        notifications_log.append({
            'user_email': user_email,
            'title': title,
            'body': body,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'status': 'mock_sent'
        })
        dm.save_data('notifications_log', notifications_log)
        
        return True
        
    except Exception as e:
        logger.error(f"Error in mock push notification service: {e}")
        return False

def get_vapid_public_key():
    """Return mock VAPID public key for testing"""
    return "BFkFOBHkHXjrnR6JFsJjNsY9N3nwZnL1xw2hDRgBs3Y-MnWkjdUTtJU7a8gzBtbdQVVXqGnNRQZcxJhK8gzBtbdQVVXqGnNRQZcxJhK8gzBtbdQVVX"
