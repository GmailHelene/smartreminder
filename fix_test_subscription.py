#!/usr/bin/env python3
"""
Fix test subscriptions to work with WebPush
"""
import json
import os
import random
import string
import base64
from datetime import datetime

# Generate a random base64 string of specified length
def generate_random_b64(length):
    random_bytes = os.urandom(length)
    return base64.urlsafe_b64encode(random_bytes).decode('utf8').rstrip('=')

# Create a valid test subscription for WebPush
def create_valid_test_subscription():
    # Generate auth (16 bytes)
    auth = generate_random_b64(16)
    
    # Generate p256dh (65 bytes - for an uncompressed EC point)
    p256dh = "BP" + generate_random_b64(63)
    
    # Create the subscription object
    timestamp = int(datetime.now().timestamp())
    subscription = {
        "endpoint": f"https://fcm.googleapis.com/fcm/send/test-endpoint-{timestamp}",
        "expirationTime": None,
        "keys": {
            "p256dh": p256dh,
            "auth": auth
        }
    }
    
    # Print the subscription
    print("Valid test subscription:")
    print(json.dumps(subscription, indent=2))
    
    # Save to a file
    with open('valid_test_subscription.json', 'w') as f:
        json.dump(subscription, f, indent=2)
    
    print("Saved to valid_test_subscription.json")
    return subscription

if __name__ == "__main__":
    create_valid_test_subscription()
    print("\nTo use this subscription in tests:")
    print("1. Copy the JSON data from valid_test_subscription.json")
    print("2. Replace the test subscription in test_notification_fix.py")
    print("3. Run test_notification_fix.py to test it")
