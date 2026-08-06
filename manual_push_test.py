#!/usr/bin/env python3
"""
Manual test of push notification sending
"""

import sys
import os
from datetime import datetime

# Add the parent directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from models import data_manager as dm
from push_service import send_push_notification

def test_send_push_notification():
    """Test sending a push notification directly"""
    
    # Load existing subscriptions
    subscriptions = dm.load_data('push_subscriptions', {})
    
    print("📱 Available push subscriptions:")
    for email, subs in subscriptions.items():
        print(f"  - {email}: {len(subs)} subscription(s)")
    
    if not subscriptions:
        print("❌ No push subscriptions found. User needs to enable notifications in the web app first.")
        return False
    
    # Test with the first available user
    test_email = list(subscriptions.keys())[0]
    print(f"\n🧪 Testing push notification to: {test_email}")
    
    try:
        result = send_push_notification(
            user_email=test_email,
            title="🔔 Manual Test Notification",
            body="This is a test notification sent manually to verify push notifications with sound are working.",
            data={
                'sound': 'pristine.mp3',
                'priority': 'high',
                'url': '/'
            },
            dm=dm
        )
        
        if result:
            print("✅ Push notification sent successfully!")
            print("📱 Check your mobile device for the notification with sound")
            return True
        else:
            print("❌ Failed to send push notification")
            return False
            
    except Exception as e:
        print(f"❌ Error sending push notification: {e}")
        return False

if __name__ == "__main__":
    print("🔔 Manual Push Notification Test")
    print("=" * 40)
    
    success = test_send_push_notification()
    
    if success:
        print("\n✅ Manual test completed successfully!")
        print("💡 If you received the notification with sound, the system is working correctly.")
    else:
        print("\n❌ Manual test failed.")
        print("🔧 Make sure to enable push notifications in the web app first.")
