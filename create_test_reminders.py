#!/usr/bin/env python3
"""Create some test reminders to test the calendar"""

import json
import uuid
from datetime import datetime, timedelta
import os

def create_test_reminders():
    """Create test reminders for the calendar"""
    
    # Get current user from users.json
    users_file = '/workspaces/smartreminder/data/users.json'
    if os.path.exists(users_file):
        with open(users_file, 'r') as f:
            users = json.load(f)
        
        if users:
            # Use first user as test user
            user_id = next(iter(users.keys()))
            user_email = users[user_id].get('email', 'test@example.com')
            print(f"Creating test reminders for user: {user_email}")
        else:
            user_email = 'test@example.com'
            print(f"No users found, using default: {user_email}")
    else:
        user_email = 'test@example.com'
        print(f"No users file found, using default: {user_email}")
    
    # Create test reminders
    now = datetime.now()
    test_reminders = [
        {
            'id': str(uuid.uuid4()),
            'user_id': user_email,
            'title': 'Test Meeting',
            'description': 'En viktig møte test',
            'datetime': (now + timedelta(days=1)).strftime('%Y-%m-%dT%H:%M'),
            'priority': 'Høy',
            'category': 'Møte',
            'created_at': now.strftime('%Y-%m-%dT%H:%M:%S')
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': user_email,
            'title': 'Handleliste',
            'description': 'Kjøpe mat til helgen',
            'datetime': (now + timedelta(days=2)).strftime('%Y-%m-%dT%H:%M'),
            'priority': 'Medium',
            'category': 'Personal',
            'created_at': now.strftime('%Y-%m-%dT%H:%M:%S')
        },
        {
            'id': str(uuid.uuid4()),
            'user_id': user_email,
            'title': 'Prosjekt Deadline',
            'description': 'Ferdigstille kodeprosjekt',
            'datetime': (now + timedelta(days=7)).strftime('%Y-%m-%dT%H:%M'),
            'priority': 'Høy',
            'category': 'Arbeid',
            'created_at': now.strftime('%Y-%m-%dT%H:%M:%S')
        }
    ]
    
    # Save to reminders.json
    reminders_file = '/workspaces/smartreminder/data/reminders.json'
    with open(reminders_file, 'w') as f:
        json.dump(test_reminders, f, indent=2, ensure_ascii=False)
    
    print(f"Created {len(test_reminders)} test reminders in {reminders_file}")
    
    # Also create a shared reminder
    shared_reminder = {
        'id': str(uuid.uuid4()),
        'shared_by': 'colleague@example.com',
        'shared_with': user_email,
        'title': 'Shared Team Meeting',
        'description': 'Månedlig teammøte',
        'datetime': (now + timedelta(days=3)).strftime('%Y-%m-%dT%H:%M'),
        'priority': 'Medium',
        'category': 'Møte',
        'created_at': now.strftime('%Y-%m-%dT%H:%M:%S')
    }
    
    shared_file = '/workspaces/smartreminder/data/shared_reminders.json'
    shared_reminders = []
    if os.path.exists(shared_file):
        with open(shared_file, 'r') as f:
            shared_reminders = json.load(f)
    
    shared_reminders.append(shared_reminder)
    
    with open(shared_file, 'w') as f:
        json.dump(shared_reminders, f, indent=2, ensure_ascii=False)
    
    print(f"Created 1 shared reminder in {shared_file}")

if __name__ == '__main__':
    create_test_reminders()
