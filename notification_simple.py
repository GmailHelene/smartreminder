#!/usr/bin/env python3
"""
Simple Notification API for SmartReminder
Alternative to WebPush for client-side notifications
"""
import os
import sys
import uuid
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import data manager module
from models import data_manager as dm

def create_notification(user_email, title, message, options=None):
    """Create a notification for a user"""
    if not options:
        options = {}
    
    # Default sound
    if 'sound' not in options:
        # Try to get user's preferred sound
        users = dm.load_data('users')
        user_data = users.get(user_email, {})
        options['sound'] = user_data.get('notification_sound', 'pristine.mp3')
    
    # Ensure sound playback adheres to browser restrictions
    if 'sound' in options:
        print(f"Sound notification: {options['sound']}")
    else:
        print("Sound notification: pristine.mp3")

    # Log notification creation
    print(f"Notification created for {user_email} with sound: {options.get('sound', 'pristine.mp3')}")

    # Create notification object
    notification = {
        'id': str(uuid.uuid4()),
        'user_email': user_email,
        'title': title,
        'message': message,
        'timestamp': datetime.now().isoformat(),
        'read': False,
        'sound': options.get('sound', 'pristine.mp3'),
        'url': options.get('url', '/dashboard'),
        'icon': options.get('icon', '/static/images/icon-192x192.png'),
        'badge': options.get('badge', '/static/images/badge-96x96.png'),
        'tag': options.get('tag', 'smartreminder-notification'),
        'data': options.get('data', {})
    }
    
    # Save to notifications data store
    notifications = dm.load_data('notifications')
    if not isinstance(notifications, dict):
        notifications = {}
    if user_email not in notifications:
        notifications[user_email] = []
    
    notifications[user_email].append(notification)
    dm.save_data('notifications', notifications)
    
    return notification['id']

def get_user_notifications(user_email, unread_only=True):
    """Get notifications for a user"""
    notifications = dm.load_data('notifications')
    if not isinstance(notifications, dict):
        notifications = {}
    user_notifications = notifications.get(user_email, [])
    
    if unread_only:
        return [n for n in user_notifications if not n.get('read', False)]
    
    return user_notifications

def mark_notification_read(user_email, notification_id):
    """Mark a notification as read"""
    notifications = dm.load_data('notifications')
    if not isinstance(notifications, dict):
        notifications = {}
    user_notifications = notifications.get(user_email, [])
    
    for notification in user_notifications:
        if notification.get('id') == notification_id:
            notification['read'] = True
            break
    
    notifications[user_email] = user_notifications
    dm.save_data('notifications', notifications)
    
    return True

def mark_all_read(user_email):
    """Mark all notifications as read for a user"""
    notifications = dm.load_data('notifications')
    if not isinstance(notifications, dict):
        notifications = {}
    user_notifications = notifications.get(user_email, [])
    
    for notification in user_notifications:
        notification['read'] = True
    
    notifications[user_email] = user_notifications
    dm.save_data('notifications', notifications)
    
    return True

def delete_notification(user_email, notification_id):
    """Delete a notification"""
    notifications = dm.load_data('notifications', {})
    user_notifications = notifications.get(user_email, [])
    
    # Filter out the notification to delete
    filtered_notifications = [n for n in user_notifications if n.get('id') != notification_id]
    
    if len(filtered_notifications) != len(user_notifications):
        notifications[user_email] = filtered_notifications
        dm.save_data('notifications', notifications)
        return True
    
    return False

def delete_all_notifications(user_email):
    """Delete all notifications for a user"""
    notifications = dm.load_data('notifications', {})
    notifications[user_email] = []
    dm.save_data('notifications', notifications)
    
    return True

def send_reminder_notification(user_email, reminder_title, reminder_time, sound=None):
    """Send a reminder notification"""
    title = "⏰ Påminnelse"
    message = f"{reminder_title} - {reminder_time}"
    
    options = {
        'type': 'reminder',
        'url': '/dashboard',
        'data': {
            'reminder_title': reminder_title,
            'reminder_time': reminder_time
        }
    }
    
    if sound:
        options['sound'] = sound
    
    return create_notification(user_email, title, message, options)

def send_board_notification(board_id, action, content, exclude_user=None):
    """Send notification to all board members except the user who performed the action"""
    boards_data = dm.load_data('shared_noteboards', {})
    
    # Find the board
    board = None
    for board_data in boards_data.values():
        if board_data.get('board_id') == board_id:
            board = board_data
            break
    
    if not board:
        return False
    
    title = f"📋 {board['title']}"
    message = f"{action}: {content[:50]}..." if len(content) > 50 else f"{action}: {content}"
    
    options = {
        'type': 'board',
        'url': f"/board/{board_id}",
        'data': {
            'board_id': board_id,
            'board_title': board['title'],
            'action': action
        }
    }
    
    notification_ids = []
    for member in board.get('members', []):
        if member != exclude_user:
            notification_id = create_notification(member, title, message, options)
            notification_ids.append(notification_id)
    
    return len(notification_ids) > 0

def send_password_reset_notification(user_email, reset_token):
    """Send password reset notification"""
    title = "🔐 Tilbakestill passord"
    message = "Klikk for å tilbakestille passordet ditt"
    
    options = {
        'type': 'password_reset',
        'url': f"/reset-password?token={reset_token}",
        'sound': 'pristine.mp3',
        'data': {
            'reset_token': reset_token
        }
    }
    
    return create_notification(user_email, title, message, options)

# Flask routes should be defined in the main app.py file, not here
# These functions are available for import by app.py

if __name__ == "__main__":
    # Test the notification system
    print("Testing notification system...")
    # Test code here if needed

# API functions that can be imported and used in app.py
def api_mark_notifications_read_handler(request_data):
    """Handler for marking notifications as read"""
    user_email = request_data.get('user_email')
    notification_ids = request_data.get('ids', [])
    
    if not user_email:
        return {'error': 'User email required'}, 400
    
    if not notification_ids:
        # Mark all as read
        mark_all_read(user_email)
    else:
        # Mark specific notifications as read
        for notification_id in notification_ids:
            mark_notification_read(user_email, notification_id)
    
    return {'success': True}

def api_delete_notification_handler(request_data):
    """Handler for deleting notifications"""
    user_email = request_data.get('user_email')
    notification_id = request_data.get('id')
    
    if not user_email:
        return {'error': 'User email required'}, 400
    
    if not notification_id:
        # Delete all
        delete_all_notifications(user_email)
    else:
        # Delete specific notification
        delete_notification(user_email, notification_id)
    
    return {'success': True}

def send_browser_notification(user_email, title, message, sound="pristine.mp3", **options):
    """
    Send a browser notification with sound support
    This is a fallback function for testing browser notifications
    """
    try:
        # Create notification using existing system
        notification_id = create_notification(
            user_email=user_email,
            title=title,
            message=message,
            options={
                'sound': sound,
                'icon': options.get('icon', '/static/images/icon-192x192.png'),
                'badge': options.get('badge', '/static/images/badge-96x96.png'),
                'url': options.get('url', '/dashboard'),
                'tag': options.get('tag', 'browser-notification'),
                'data': options.get('data', {})
            }
        )
        
        # Log the notification attempt
        print(f"Browser notification created for {user_email}: {title}")
        print(f"Sound file: {sound}")
        print(f"Notification ID: {notification_id}")
        
        # In a real implementation, this would trigger browser API
        # For testing, we just return success
        return True
        
    except Exception as e:
        print(f"Error sending browser notification: {e}")
        return False

def send_reminder_notification(user_email, title, datetime_str, sound="pristine.mp3", dm=None):
    """
    Send a reminder notification with sound
    Compatible with the main notification system
    """
    try:
        message = f"Påminnelse for {datetime_str}"
        
        # Use the browser notification system
        success = send_browser_notification(
            user_email=user_email,
            title=title,
            message=message,
            sound=sound,
            tag='reminder-notification',
            data={
                'type': 'reminder',
                'datetime': datetime_str,
                'sound': sound
            }
        )
        
        if success:
            print(f"✅ Reminder notification sent to {user_email} with sound {sound}")
        else:
            print(f"❌ Failed to send reminder notification to {user_email}")
            
        return success
        
    except Exception as e:
        print(f"Error in send_reminder_notification: {e}")
        return False

# If this file is run directly, test the notification system
if __name__ == "__main__":
    import argparse
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Test the notification system')
    parser.add_argument('user_email', nargs='?', help='User email to send notification to')
    parser.add_argument('--list', action='store_true', help='List user notifications')
    parser.add_argument('--clear', action='store_true', help='Clear all notifications for user')
    args = parser.parse_args()
    
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
    
    print(f"Using user: {user_email}")
    
    # List notifications if requested
    if args.list:
        notifications = get_user_notifications(user_email, unread_only=False)
        print(f"Found {len(notifications)} notifications for {user_email}")
        for i, notification in enumerate(notifications):
            read_status = "✓" if notification.get('read') else "●"
            print(f"{i+1}. [{read_status}] {notification.get('title')}: {notification.get('message')}")
        sys.exit(0)
    
    # Clear notifications if requested
    if args.clear:
        delete_all_notifications(user_email)
        print(f"✅ Cleared all notifications for {user_email}")
        sys.exit(0)
    
    # Otherwise send a test notification
    print("Sending test notification...")
    notification_id = create_notification(
        user_email=user_email,
        title="🔔 Test Notification",
        message="This is a test notification from the simple notification system",
        options={
            'sound': 'pristine.mp3',
            'url': '/dashboard',
            'data': {
                'test': True,
                'timestamp': datetime.now().isoformat()
            }
        }
    )
    
    print(f"✅ Created notification with ID: {notification_id}")
    print("Check notifications with: python notification_simple.py --list")
