"""
Data Manager for SmartReminder
Handles all data storage and retrieval operations
"""

import os
import json
import logging
from datetime import datetime
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data storage location
DATA_DIR = os.environ.get('DATA_DIR', 'data')
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def load_data(collection, default=None):
    """Load data from a JSON file"""
    try:
        file_path = os.path.join(DATA_DIR, f"{collection}.json")
        if os.path.exists(file_path):
            with open(file_path, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading {collection}: {e}")
    return default if default is not None else {}

def save_data(collection, data):
    """Save data to a JSON file"""
    try:
        file_path = os.path.join(DATA_DIR, f"{collection}.json")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving {collection}: {e}")
        return False

def get_user(email):
    """Get user data by email"""
    users = load_data('users')
    return users.get(email)

def save_user(email, data):
    """Save user data"""
    users = load_data('users')
    users[email] = data
    return save_data('users', users)

def get_reminders(user_email=None):
    """Get reminders, optionally filtered by user"""
    reminders = load_data('reminders', [])
    if user_email:
        return [r for r in reminders if r.get('user_email') == user_email]
    return reminders

def save_reminder(reminder_data):
    """Save a new reminder"""
    reminders = load_data('reminders', [])
    reminder_data['id'] = str(len(reminders) + 1)  # Simple ID generation
    reminder_data['created_at'] = datetime.now().isoformat()
    reminders.append(reminder_data)
    return save_data('reminders', reminders)

def get_boards(user_email=None):
    """Get shared boards, optionally filtered by user"""
    boards = load_data('boards', [])
    if user_email:
        return [b for b in boards if user_email in b.get('members', [])]
    return boards

def save_board(board_data):
    """Save a shared board"""
    boards = load_data('boards', [])
    board_data['id'] = str(len(boards) + 1)  # Simple ID generation
    board_data['created_at'] = datetime.now().isoformat()
    boards.append(board_data)
    return save_data('boards', boards)

def get_notifications(user_email):
    """Get notifications for a user"""
    notifications = load_data('notifications', {})
    return notifications.get(user_email, [])

def save_notification(user_email, notification):
    """Save a notification for a user"""
    notifications = load_data('notifications', {})
    user_notifications = notifications.get(user_email, [])
    notification['id'] = str(len(user_notifications) + 1)  # Simple ID generation
    notification['created_at'] = datetime.now().isoformat()
    user_notifications.append(notification)
    notifications[user_email] = user_notifications
    return save_data('notifications', notifications)

def clear_notifications(user_email):
    """Clear all notifications for a user"""
    notifications = load_data('notifications', {})
    notifications[user_email] = []
    return save_data('notifications', notifications)
