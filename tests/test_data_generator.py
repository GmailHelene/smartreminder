#!/usr/bin/env python3
"""
Test data generator for Smart Påminner Pro
Creates realistic test data for development and testing
"""

import json
import uuid
from datetime import datetime, timedelta
import random
from pathlib import Path
import sys
import os

# Fix encoding for Windows console
if os.name == 'nt':  # Windows
    os.system('chcp 65001 > nul')  # Set console to UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project directory to path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

from werkzeug.security import generate_password_hash

class TestDataGenerator:
    def __init__(self, data_dir=None):
        self.data_dir = data_dir or Path(project_dir) / 'data'
        self.data_dir.mkdir(exist_ok=True)
        
        # Sample data
        self.sample_titles = [
            "Møte med kunden", "Handle mat", "Trening", "Lege-time",
            "Levere rapport", "Ring mamma", "Betale regninger", "Hente barn",
            "Prosjektmøte", "Tannlege", "Yoga-time", "Studiesesjon",
            "Jobbintervju", "Veterinær-time", "Familie-middag", "Film-kveld"
        ]
        
        self.sample_descriptions = [
            "Viktig møte - husk dokumenter",
            "Kjøp melk, brød, og grønnsaker",
            "30 min løpetur i parken",
            "Årlig kontroll",
            "Deadline i morgen",
            "Ikke glemt i så lenge",
            "Strøm og internett",
            "Skoleslutttid 15:00",
            "Sprint review - demo klar",
            "Sjekk av tann",
            "Meditasjon og stretching",
            "Eksamen forberedelse",
            "Forbered CV og referanser",
            "Årlig vaksinering",
            "Hele familien samlet",
            "Popcorn og brus"
        ]
        
        self.categories = ['Jobb', 'Privat', 'Helse', 'Familie', 'Annet']
        self.priorities = ['Lav', 'Medium', 'Høy']
        
        self.sample_emails = [
            'anna.hansen@email.com',
            'lars.olsen@email.com', 
            'marie.berg@email.com',
            'erik.dahl@email.com',
            'sofia.lund@email.com'
        ]
    
    def save_data(self, filename, data):
        """Save data to JSON file"""
        filepath = self.data_dir / f"{filename}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"[OK] Saved {filename}.json with {len(data)} items")
    
    def generate_users(self, count=5):
        """Generate test users"""
        users = {}
        
        for i, email in enumerate(self.sample_emails[:count]):
            user_id = str(uuid.uuid4())
            users[user_id] = {
                'username': email,
                'email': email,
                'password_hash': generate_password_hash('test123'),
                'created': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'focus_mode': random.choice(['normal', 'adhd', 'silent', 'work', 'study'])
            }
        
        self.save_data('users', users)
        return users
    
    def generate_reminders(self, users, count=20):
        """Generate test reminders"""
        reminders = []
        user_emails = [u['email'] for u in users.values()]
        
        for i in range(count):
            # Mix of past, present and future reminders
            if i < count // 3:
                # Past reminders (completed)
                date_offset = -random.randint(1, 30)
                completed = True
            elif i < 2 * count // 3:
                # Recent/today reminders
                date_offset = random.randint(0, 2)
                completed = random.choice([True, False])
            else:
                # Future reminders
                date_offset = random.randint(1, 30)
                completed = False
            
            reminder_date = datetime.now() + timedelta(days=date_offset)
            reminder_time = datetime.now().replace(
                hour=random.randint(8, 20),
                minute=random.choice([0, 15, 30, 45])
            ).time()
            
            reminder = {
                'id': str(uuid.uuid4()),
                'user_id': random.choice(user_emails),
                'title': random.choice(self.sample_titles),
                'description': random.choice(self.sample_descriptions),
                'datetime': f"{reminder_date.strftime('%Y-%m-%d')} {reminder_time}",
                'priority': random.choice(self.priorities),
                'category': random.choice(self.categories),
                'completed': completed,
                'created': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                'shared_with': []
            }
            
            if completed:
                reminder['completed_at'] = (reminder_date + timedelta(hours=random.randint(0, 2))).isoformat()
            
            reminders.append(reminder)
        
        self.save_data('reminders', reminders)
        return reminders
    
    def generate_shared_reminders(self, users, count=10):
        """Generate shared reminders"""
        shared_reminders = []
        user_emails = [u['email'] for u in users.values()]
        
        for i in range(count):
            date_offset = random.randint(-5, 15)
            reminder_date = datetime.now() + timedelta(days=date_offset)
            reminder_time = datetime.now().replace(
                hour=random.randint(8, 20),
                minute=random.choice([0, 15, 30, 45])
            ).time()
            
            shared_by = random.choice(user_emails)
            shared_with = random.choice([email for email in user_emails if email != shared_by])
            
            shared_reminder = {
                'id': str(uuid.uuid4()),
                'original_id': str(uuid.uuid4()),
                'shared_by': shared_by,
                'shared_with': shared_with,
                'title': f"Delt: {random.choice(self.sample_titles)}",
                'description': random.choice(self.sample_descriptions),
                'datetime': f"{reminder_date.strftime('%Y-%m-%d')} {reminder_time}",
                'priority': random.choice(self.priorities),
                'category': random.choice(self.categories),
                'completed': random.choice([True, False]) if date_offset < 0 else False,
                'created': (datetime.now() - timedelta(hours=random.randint(1, 48))).isoformat(),
                'is_shared': True
            }
            
            shared_reminders.append(shared_reminder)
        
        self.save_data('shared_reminders', shared_reminders)
        return shared_reminders
    
    def generate_noteboards(self, users, count=3):
        """Generate test noteboards"""
        boards = {}
        user_emails = [u['email'] for u in users.values()]
        
        board_titles = [
            "Prosjekt Alpha",
            "Familie-planlegging", 
            "Studiemål 2024",
            "Ferieplanlegging",
            "Husarbeid"
        ]
        
        colors = ['yellow', 'blue', 'green', 'pink', 'orange']
        
        for i in range(count):
            board_id = str(uuid.uuid4())
            created_by = random.choice(user_emails)
            members = [created_by] + random.sample(
                [email for email in user_emails if email != created_by], 
                random.randint(1, 3)
            )
            
            # Generate notes for this board
            notes = []
            for j in range(random.randint(3, 8)):
                note = {
                    'id': str(uuid.uuid4()),
                    'content': f"Notis {j+1}: {random.choice(self.sample_descriptions)}",
                    'author': random.choice(members),
                    'type': 'text',
                    'color': random.choice(colors),
                    'position': {
                        'x': random.randint(50, 800),
                        'y': random.randint(50, 600)
                    },
                    'created_at': (datetime.now() - timedelta(hours=random.randint(1, 72))).isoformat(),
                    'updated_at': (datetime.now() - timedelta(minutes=random.randint(0, 60))).isoformat(),
                    'tags': [],
                    'completed': None
                }
                notes.append(note)
            
            board = {
                'board_id': board_id,
                'title': board_titles[i] if i < len(board_titles) else f"Tavle {i+1}",
                'description': f"Dette er en test-tavle for {board_titles[i] if i < len(board_titles) else f'diverse notiser {i+1}'}",
                'created_by': created_by,
                'access_code': ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8)),
                'created_at': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                'members': members,
                'notes': notes,
                'settings': {
                    'public': False,
                    'allow_anonymous': False,
                    'moderation': False
                }
            }
            
            boards[board_id] = board
        
        self.save_data('shared_noteboards', boards)
        return boards
    
    def generate_email_log(self, count=15):
        """Generate email log entries"""
        email_log = []
        templates = [
            'emails/reminder_notification.html',
            'emails/shared_reminder.html',
            'emails/noteboard_invitation.html',
            'emails/email_test.html'
        ]
        
        for i in range(count):
            entry = {
                'recipient': random.choice(self.sample_emails),
                'subject': f"Test e-post {i+1}",
                'template': random.choice(templates),
                'status': random.choices(['sent', 'failed'], weights=[0.9, 0.1])[0],
                'timestamp': (datetime.now() - timedelta(hours=random.randint(1, 168))).isoformat(),
                'error': 'SMTP connection failed' if random.random() < 0.1 else None
            }
            email_log.append(entry)
        
        self.save_data('email_log', email_log)
        return email_log
    
    def generate_notifications(self, reminders, count=10):
        """Generate notification log"""
        notifications = []
        
        for i in range(min(count, len(reminders))):
            reminder = reminders[i]
            notification = {
                'reminder_id': reminder['id'],
                'recipient': reminder['user_id'],
                'sent_at': (datetime.now() - timedelta(hours=random.randint(1, 24))).isoformat(),
                'type': 'reminder_notification'
            }
            notifications.append(notification)
        
        self.save_data('notifications', notifications)
        return notifications
    
    def generate_all_data(self):
        """Generate all test data"""
        print("Generating test data for Smart Paminner Pro...")
        print("=" * 50)
        
        # Generate in dependency order
        users = self.generate_users(5)
        reminders = self.generate_reminders(users, 20)
        shared_reminders = self.generate_shared_reminders(users, 10)
        noteboards = self.generate_noteboards(users, 3)
        email_log = self.generate_email_log(15)
        notifications = self.generate_notifications(reminders, 10)
        
        print("\nTest data generation completed!")
        print(f"Data saved to: {self.data_dir}")
        print("\nTest user credentials (all passwords: 'test123'):")
        for email in self.sample_emails[:5]:
            print(f"  - {email}")
        
        return {
            'users': users,
            'reminders': reminders,
            'shared_reminders': shared_reminders,
            'noteboards': noteboards,
            'email_log': email_log,
            'notifications': notifications
        }

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test data for Smart Påminner Pro')
    parser.add_argument('--data-dir', help='Data directory path')
    parser.add_argument('--users', type=int, default=5, help='Number of users (default: 5)')
    parser.add_argument('--reminders', type=int, default=20, help='Number of reminders (default: 20)')
    parser.add_argument('--boards', type=int, default=3, help='Number of noteboards (default: 3)')
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir) if args.data_dir else None
    generator = TestDataGenerator(data_dir)
    
    try:
        generator.generate_all_data()
        print("\nReady to test the app with realistic data!")
        
    except Exception as e:
        print(f"\nError generating test data: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
