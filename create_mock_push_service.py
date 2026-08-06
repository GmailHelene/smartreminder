#!/usr/bin/env python3
"""
Create mock push subscription for testing
"""
import os
import sys
import json
import time
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create a test mode version of push_service.py that doesn't actually send notifications
def create_mock_push_service():
    mock_file = """
# Mock push_service.py for testing
def send_push_notification(user_email, title, body, data=None, dm=None):
    print(f"MOCK: Would send notification to {user_email}: {title}")
    print(f"MOCK: Body: {body}")
    print(f"MOCK: Data: {data}")
    return True

def send_reminder_notification(user_email, reminder_title, reminder_time, sound=None, dm=None):
    print(f"MOCK: Would send reminder to {user_email}: {reminder_title} at {reminder_time}")
    if sound:
        print(f"MOCK: Sound: {sound}")
    return True

def send_board_notification(board_id, action, content, exclude_user=None, dm=None):
    print(f"MOCK: Would send board notification for {board_id}")
    print(f"MOCK: Action: {action}, Content: {content}")
    return True

def subscribe_user_to_push(user_email, subscription_data, dm=None):
    print(f"MOCK: Would subscribe {user_email} to push notifications")
    # Still save the subscription for testing
    if dm:
        subscriptions = dm.load_data('push_subscriptions')
        if user_email not in subscriptions:
            subscriptions[user_email] = []
        subscription_data['subscribed_at'] = datetime.now().isoformat()
        subscriptions[user_email].append(subscription_data)
        dm.save_data('push_subscriptions', subscriptions)
    return True

def send_password_reset_notification(user_email, reset_token, dm=None):
    print(f"MOCK: Would send password reset to {user_email} with token {reset_token}")
    return True
"""
    
    # Write to a temporary file
    with open("push_service_mock.py", "w") as f:
        f.write(mock_file)
    
    print("Created mock push_service.py")

if __name__ == "__main__":
    create_mock_push_service()
    print("Run tests with: python3 test_comprehensive_notifications.py --mock")
