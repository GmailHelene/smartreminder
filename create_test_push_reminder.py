#!/usr/bin/env python3
"""
Create a test reminder for push notification testing
"""

import json
import sys
import os
from datetime import datetime, timedelta

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models import data_manager as dm

def create_test_reminder():
    """Create a test reminder that will trigger in 2 minutes"""
    
    # Set reminder time for 2 minutes from now
    reminder_time = datetime.now() + timedelta(minutes=2)
    
    # Create the reminder
    test_reminder = {
        'id': f'test_push_{int(datetime.now().timestamp())}',
        'title': '🔔 Test Push Notification',
        'description': 'This is a test reminder to verify that push notifications with sound are working properly.',
        'datetime': reminder_time.isoformat(),
        'email': 'helene721@gmail.com',  # Assuming this is the user from the subscription data
        'notification': True,
        'sound': 'pristine.mp3',
        'created_at': datetime.now().isoformat(),
        'status': 'active'
    }
    
    # Load existing reminders
    reminders = dm.load_data('reminders', [])
    
    # Add the test reminder
    reminders.append(test_reminder)
    
    # Save the reminders
    dm.save_data('reminders', reminders)
    
    print(f"✅ Test reminder created!")
    print(f"📅 Title: {test_reminder['title']}")
    print(f"⏰ Time: {test_reminder['datetime']}")
    print(f"📧 User: {test_reminder['email']}")
    print(f"🔔 Notification: {test_reminder['notification']}")
    print(f"🔊 Sound: {test_reminder['sound']}")
    print(f"🆔 ID: {test_reminder['id']}")
    print(f"\n🕐 The reminder will trigger in 2 minutes at {reminder_time.strftime('%H:%M:%S')}")
    print("📱 Make sure you have the web app open in a browser and push notifications enabled!")

if __name__ == "__main__":
    create_test_reminder()
