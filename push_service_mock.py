
# Mock push_service.py for testing
import os
from datetime import datetime

def send_push_notification(user_email, title, body, data=None, sound=None, dm=None):
    print(f"MOCK: Would send notification to {user_email}: {title}")
    print(f"MOCK: Body: {body}")
    print(f"MOCK: Data: {data}")
    if sound:
        print(f"MOCK: Sound: {sound}")
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
