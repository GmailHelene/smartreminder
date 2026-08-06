"""
Push Notification Service for SmartReminder
Handles web push notifications for mobile devices
"""

import json
import os
import requests
from pywebpush import webpush, WebPushException
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# VAPID keys are read from environment variables — NEVER hardcode private keys in source.
# Set VAPID_PUBLIC_KEY, VAPID_PRIVATE_KEY and (optionally) VAPID_CLAIM_SUB in Railway.
VAPID_PRIVATE_KEY = os.environ.get('VAPID_PRIVATE_KEY', '')
VAPID_PUBLIC_KEY = os.environ.get('VAPID_PUBLIC_KEY', '')
VAPID_CLAIMS = {"sub": os.environ.get('VAPID_CLAIM_SUB', 'mailto:helene721@gmail.com')}

def send_push_notification(user_email, title, body, data=None, dm=None):
    """Send push notification to user with enhanced mobile support"""
    if not dm:
        logger.error("DataManager not provided to send_push_notification")
        return False

    if not (VAPID_PRIVATE_KEY and VAPID_PUBLIC_KEY):
        logger.warning("Push notifications disabled: VAPID keys not configured (set VAPID_PUBLIC_KEY/VAPID_PRIVATE_KEY).")
        return False

    try:
        # Load push subscriptions, handle both dict and list formats
        subscriptions_data = dm.load_data('push_subscriptions', {})
        
        # Handle the case where subscriptions_data might be a list instead of dict
        if isinstance(subscriptions_data, list):
            logger.warning("Push subscriptions data is in list format, converting to dict")
            subscriptions_data = {}
        elif not isinstance(subscriptions_data, dict):
            logger.error("Push subscriptions data is not in expected format")
            subscriptions_data = {}
        
        user_subscriptions = subscriptions_data.get(user_email, [])
        
        # Ensure user_subscriptions is a list
        if not isinstance(user_subscriptions, list):
            logger.warning(f"User subscriptions for {user_email} is not a list, converting")
            user_subscriptions = []
        
        if not user_subscriptions:
            logger.info(f"No push subscriptions found for user {user_email}")
            return False
        
        # Get user preferences for sound
        users_data = dm.load_data('users', {})
        user_data = users_data.get(user_email, {})
        default_sound = user_data.get('notification_sound', 'pristine.mp3')
        
        # Use provided data or create empty dict
        notification_data = data or {}
        
        # Add sound parameter if not already present
        if 'sound' not in notification_data:
            notification_data['sound'] = default_sound
        
        # Enhanced mobile-optimized notification payload
        notification_payload = {
            "title": title,
            "body": body,
            "icon": "/static/images/icon-192x192.png",
            "badge": "/static/images/badge-96x96.png",
            "tag": "smartreminder-notification",
            "renotify": True,
            "requireInteraction": True,  # Keep notification visible until user interacts
            "sound": notification_data.get('sound', default_sound),
            "vibrate": [200, 100, 200, 100, 200],  # Enhanced vibration pattern
            "data": notification_data,
            "actions": [
                {
                    "action": "open",
                    "title": "Åpne app",
                    "icon": "/static/images/icon-192x192.png"
                },
                {
                    "action": "close", 
                    "title": "Lukk",
                    "icon": "/static/images/icon-192x192.png"
                }
            ]
        }
        
        # Add priority handling for mobile
        if notification_data.get('priority') == 'high':
            notification_payload['vibrate'] = [300, 100, 300, 100, 300]
            notification_payload['requireInteraction'] = True
        
        success_count = 0
        invalid_subscriptions = []
        
        for subscription in user_subscriptions:
            try:
                response = webpush(
                    subscription_info=subscription,
                    data=json.dumps(notification_payload),
                    vapid_private_key=VAPID_PRIVATE_KEY,
                    vapid_claims=VAPID_CLAIMS
                )
                success_count += 1
                logger.info(f"Push notification sent successfully to {user_email}")
                
            except WebPushException as e:
                logger.error(f"Failed to send push notification to {user_email}: {e}")
                # Mark subscription for removal if it's invalid
                if e.response and e.response.status_code in [410, 404]:
                    invalid_subscriptions.append(subscription)
            except Exception as e:
                logger.error(f"Unexpected error sending push notification: {e}")
        
        # Remove invalid subscriptions
        if invalid_subscriptions:
            for invalid_sub in invalid_subscriptions:
                if invalid_sub in user_subscriptions:
                    user_subscriptions.remove(invalid_sub)
            
            subscriptions_data[user_email] = user_subscriptions
            dm.save_data('push_subscriptions', subscriptions_data)
            logger.info(f"Removed {len(invalid_subscriptions)} invalid subscriptions for {user_email}")
        
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending push notification to {user_email}: {e}")
        return False

def send_board_notification(board_id, action, content, exclude_user=None, dm=None):
    """Send notification to all board members except the user who performed the action"""
    if not dm:
        return False
        
    try:
        boards_data = dm.load_data('shared_noteboards')
        
        # Find the board
        board = None
        for board_data in boards_data.values():
            if board_data.get('board_id') == board_id:
                board = board_data
                break
        
        if not board:
            logger.warning(f"Board {board_id} not found for notification")
            return False
        
        title = f"📋 {board['title']}"
        body = f"{action}: {content[:50]}..." if len(content) > 50 else f"{action}: {content}"
        
        notification_data = {
            "board_id": board_id,
            "action": action,
            "board_title": board['title'],
            "url": f"/board/{board_id}"
        }
        
        success_count = 0
        for member in board.get('members', []):
            if member != exclude_user:
                if send_push_notification(member, title, body, notification_data, dm):
                    success_count += 1
        
        logger.info(f"Sent board notifications to {success_count} members for board {board_id}")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Error sending board notification for {board_id}: {e}")
        return False

def send_reminder_notification(user_email, reminder_title, reminder_time, sound=None, dm=None):
    """Send notification for upcoming reminder"""
    if not dm:
        return False
        
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

def subscribe_user_to_push(user_email, subscription_data, dm=None):
    """Subscribe user to push notifications"""
    if not dm:
        return False
        
    try:
        subscriptions = dm.load_data('push_subscriptions')
        
        if user_email not in subscriptions:
            subscriptions[user_email] = []
        
        # Check if subscription already exists
        existing = False
        for sub in subscriptions[user_email]:
            if sub.get('endpoint') == subscription_data.get('endpoint'):
                existing = True
                break
        
        if not existing:
            # Add timestamp to subscription
            subscription_data['subscribed_at'] = datetime.now().isoformat()
            subscriptions[user_email].append(subscription_data)
            dm.save_data('push_subscriptions', subscriptions)
            logger.info(f"Added push subscription for {user_email}")
            return True
        else:
            logger.info(f"Push subscription already exists for {user_email}")
            return True
            
    except Exception as e:
        logger.error(f"Error subscribing user {user_email} to push notifications: {e}")
        return False

def get_user_subscriptions(user_email, dm=None):
    """Get all push subscriptions for a user"""
    if not dm:
        return []
        
    try:
        subscriptions = dm.load_data('push_subscriptions')
        return subscriptions.get(user_email, [])
    except Exception as e:
        logger.error(f"Error getting subscriptions for {user_email}: {e}")
        return []

def unsubscribe_user_from_push(user_email, endpoint, dm=None):
    """Unsubscribe user from push notifications"""
    if not dm:
        return False
        
    try:
        subscriptions = dm.load_data('push_subscriptions')
        user_subs = subscriptions.get(user_email, [])
        
        # Remove subscription with matching endpoint
        updated_subs = [sub for sub in user_subs if sub.get('endpoint') != endpoint]
        
        if len(updated_subs) != len(user_subs):
            subscriptions[user_email] = updated_subs
            dm.save_data('push_subscriptions', subscriptions)
            logger.info(f"Removed push subscription for {user_email}")
            return True
        else:
            logger.warning(f"No matching subscription found for {user_email}")
            return False
            
    except Exception as e:
        logger.error(f"Error unsubscribing user {user_email}: {e}")
        return False

def send_password_reset_notification(user_email, reset_token, dm=None):
    """Send password reset notification to user"""
    if not dm:
        return False
        
    title = "🔐 Tilbakestill passord"
    body = "Klikk for å tilbakestille passordet ditt"
    
    notification_data = {
        "type": "password_reset",
        "reset_token": reset_token,
        "url": f"/reset-password?token={reset_token}",
        "sound": "pristine.mp3"
    }
    
    return send_push_notification(user_email, title, body, notification_data, dm)

def send_password_reset_confirmation(user_email, dm=None):
    """Send confirmation when password has been reset"""
    if not dm:
        return False
        
    title = "✅ Passord oppdatert"
    body = "Passordet ditt har blitt oppdatert"
    
    notification_data = {
        "type": "password_reset_success",
        "url": "/login"
    }
    
    return send_push_notification(user_email, title, body, notification_data, dm)

def get_vapid_public_key():
    """Return the VAPID public key for push notifications"""
    return VAPID_PUBLIC_KEY
