#!/usr/bin/env python3
"""
Create test push subscription for a user
This script creates a test push subscription for a specified user or the default test user
"""

import os
import sys
import json
from datetime import datetime

# Add the current directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import app and push service
from app import app, dm
from push_service import subscribe_user_to_push

def create_test_subscription(user_email="test-user-123"):
    """Create a test subscription for the specified user"""
    print(f"Creating test subscription for user: {user_email}")
    
    # Check if user exists
    users = dm.load_data('users')
    if user_email not in users and users:
        print(f"User {user_email} not found in database. Using first available user.")
        user_email = list(users.keys())[0]
        print(f"Selected user: {user_email}")
    
    # Create a test subscription
    test_subscription = {
        "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint-" + str(int(datetime.now().timestamp())),
        "expirationTime": None,
        "keys": {
            "p256dh": "BGEw2wsHgLwzerjvR0O0hmOI3zt6pJWzAvVejXc5p8GUpS03ro0bviBDb-iqQD1qOU7G5GlrYJr0W5SWgE-oEWU",
            "auth": "8O_K-rlSQUxMpBmx3NspGQ"
        }
    }
    
    # Subscribe user to push
    result = subscribe_user_to_push(user_email, test_subscription, dm)
    
    if result:
        print(f"✅ Successfully created test subscription for {user_email}")
        
        # Verify subscription was created
        subscriptions = dm.load_data('push_subscriptions')
        user_subscriptions = subscriptions.get(user_email, [])
        print(f"User now has {len(user_subscriptions)} subscriptions")
    else:
        print(f"❌ Failed to create test subscription for {user_email}")
    
    return result

if __name__ == "__main__":
    # Get user email from command line argument or use default
    if len(sys.argv) > 1:
        user_email = sys.argv[1]
    else:
        user_email = "test-user-123"
    
    create_test_subscription(user_email)
