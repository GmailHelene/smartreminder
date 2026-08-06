#!/usr/bin/env python3
"""
Clean up invalid push subscriptions and reset for fresh testing
"""

import sys
import os
import json

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models import data_manager as dm

def clean_push_subscriptions():
    """Clean up old/invalid push subscriptions"""
    
    print("🧹 Cleaning up old push subscriptions...")
    
    # Load current subscriptions
    subscriptions = dm.load_data('push_subscriptions', {})
    
    print(f"📊 Current subscriptions: {len(subscriptions)} users")
    for email, subs in subscriptions.items():
        print(f"  - {email}: {len(subs)} subscription(s)")
    
    # Clear all subscriptions to start fresh
    dm.save_data('push_subscriptions', {})
    
    print("✅ All push subscriptions cleared!")
    print("\n🔧 NEXT STEPS TO TEST PUSH NOTIFICATIONS:")
    print("1. Open the web app in your mobile browser")
    print("2. Go to http://localhost:5000 (or the deployed URL)")
    print("3. Log in to your account")
    print("4. Click the 'Enable Push Notifications' button")
    print("5. Accept the notification permission when prompted")
    print("6. Run: python3 create_test_push_reminder.py")
    print("7. Wait 2 minutes for the test notification")
    print("\n💡 The notification should now include sound!")

if __name__ == "__main__":
    clean_push_subscriptions()
