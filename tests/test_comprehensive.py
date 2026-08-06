import unittest
import tempfile
import os
import sys
import json
from pathlib import Path
from datetime import datetime, timedelta

# Add project directory to path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# Mock APScheduler before importing app
import unittest.mock as mock
sys.modules['apscheduler'] = mock.MagicMock()
sys.modules['apscheduler.schedulers'] = mock.MagicMock()
sys.modules['apscheduler.schedulers.background'] = mock.MagicMock()

# Set testing environment before importing app
os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'

from app import app, dm

class SmartReminderComprehensiveTest(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        
        # Configure app for testing
        app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'MAIL_SUPPRESS_SEND': True,
            'LOGIN_DISABLED': False
        })
        
        # Override data manager for testing
        dm.data_dir = Path(self.test_dir)
        dm._ensure_data_files()
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # Create test user
        self.test_user_email = 'test@example.com'
        self.test_user_password = 'testpassword123'
        self.test_user_id = self._create_test_user()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.app_context.pop()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def _create_test_user(self):
        """Create a test user"""
        from werkzeug.security import generate_password_hash
        import uuid
        
        user_id = str(uuid.uuid4())
        users = dm.load_data('users')
        users[user_id] = {
            'username': self.test_user_email,
            'email': self.test_user_email,
            'password_hash': generate_password_hash(self.test_user_password),
            'created': datetime.now().isoformat()
        }
        dm.save_data('users', users)
        return user_id
    
    def _login_test_user(self):
        """Login the test user using actual form submission"""
        response = self.app.post('/login', data={
            'username': self.test_user_email,
            'password': self.test_user_password
        }, follow_redirects=False)
        return response.status_code == 302  # Successful login redirects
    
    def test_app_startup(self):
        """Test app starts up correctly"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_user_registration_and_login(self):
        """Test user registration and login flow"""
        # Test registration
        new_email = 'newuser@example.com'
        response = self.app.post('/register', data={
            'username': new_email,
            'password': 'newpassword123'
        }, follow_redirects=False)
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
        
        # Test login with new user
        response = self.app.post('/login', data={
            'username': new_email,
            'password': 'newpassword123'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
    
    def test_reminder_creation(self):
        """Test creating reminders"""
        # Login first
        login_success = self._login_test_user()
        self.assertTrue(login_success, "Login should be successful")
        
        # Create reminder
        tomorrow = (datetime.now() + timedelta(days=1)).date()
        response = self.app.post('/add_reminder', data={
            'title': 'Test Reminder',
            'description': 'This is a test reminder',
            'date': tomorrow.isoformat(),
            'time': '14:30',
            'priority': 'Høy',
            'category': 'Jobb'
        }, follow_redirects=True)
        
        self.assertEqual(response.status_code, 200)
        
        # Verify reminder was created
        reminders = dm.load_data('reminders')
        self.assertTrue(any(r['title'] == 'Test Reminder' for r in reminders))
    
    def test_dashboard_access(self):
        """Test dashboard requires login and shows correct data"""
        # Test unauthorized access
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login
        
        # Test authorized access
        login_success = self._login_test_user()
        self.assertTrue(login_success, "Login should be successful")
        
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 200)
    
    def test_data_persistence(self):
        """Test data is properly saved and loaded"""
        # Create test data
        test_data = {'test': 'value', 'number': 42}
        dm.save_data('test_file', test_data)
        
        # Load and verify
        loaded_data = dm.load_data('test_file')
        self.assertEqual(loaded_data, test_data)
        
        # Test file exists
        test_file = dm.data_dir / 'test_file.json'
        self.assertTrue(test_file.exists())
    
    def test_error_pages(self):
        """Test error pages render correctly"""
        # Test 404
        response = self.app.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        # Login first
        login_success = self._login_test_user()
        self.assertTrue(login_success, "Login should be successful")
        
        # Test reminder count API
        response = self.app.get('/api/reminder-count')
        self.assertEqual(response.status_code, 200)
        
        data = response.get_json()
        self.assertIn('my_reminders', data)
        self.assertIn('shared_reminders', data)
        self.assertIn('completed', data)
    
    def test_offline_functionality(self):
        """Test offline page and PWA features"""
        response = self.app.get('/offline')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'offline', response.data.lower())
        
        # Test service worker
        response = self.app.get('/static/sw.js')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/javascript')
        
        # Test manifest
        response = self.app.get('/static/manifest.json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.headers['Content-Type'], 'application/manifest+json')
    
    def test_login_form_validation(self):
        """Test login form validation"""
        # Test empty form
        response = self.app.post('/login', data={}, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Test invalid email
        response = self.app.post('/login', data={
            'username': 'invalid-email',
            'password': 'password'
        }, follow_redirects=True)
        self.assertEqual(response.status_code, 200)
    
    def test_reminder_deletion(self):
        """Test deleting reminders"""
        # Login and create reminder
        login_success = self._login_test_user()
        self.assertTrue(login_success, "Login should be successful")
        
        import uuid
        reminder_id = str(uuid.uuid4())
        reminders = dm.load_data('reminders')
        reminders.append({
            'id': reminder_id,
            'user_id': self.test_user_email,
            'title': 'Delete Me',
            'description': 'Test deletion',
            'datetime': '2024-12-31 12:00',
            'priority': 'Low',
            'category': 'Annet',
            'completed': False,
            'created': datetime.now().isoformat(),
            'shared_with': []
        })
        dm.save_data('reminders', reminders)
        
        # Delete the reminder
        response = self.app.get(f'/delete_reminder/{reminder_id}', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        
        # Verify deletion
        updated_reminders = dm.load_data('reminders')
        self.assertFalse(any(r['id'] == reminder_id for r in updated_reminders))

class TestDataManager(unittest.TestCase):
    """Test data manager functionality"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        # Create a new DataManager instance for testing
        from app import DataManager
        self.dm = DataManager()
        self.dm.data_dir = Path(self.test_dir)
        self.dm._ensure_data_files()
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_data_file_creation(self):
        """Test data files are created properly"""
        expected_files = ['users.json', 'reminders.json', 'shared_reminders.json', 
                         'notifications.json', 'email_log.json']
        
        for filename in expected_files:
            filepath = self.dm.data_dir / filename
            self.assertTrue(filepath.exists(), f"{filename} should exist")
    
    def test_data_save_and_load(self):
        """Test saving and loading data"""
        test_data = {'key': 'value', 'number': 123, 'list': [1, 2, 3]}
        
        # Save data
        self.dm.save_data('test', test_data)
        
        # Load and verify
        loaded_data = self.dm.load_data('test')
        self.assertEqual(loaded_data, test_data)
    
    def test_backup_functionality(self):
        """Test backup creation during save"""
        initial_data = {'version': 1}
        updated_data = {'version': 2}
        
        # Save initial data
        self.dm.save_data('backup_test', initial_data)
        
        # Update data (should create backup)
        self.dm.save_data('backup_test', updated_data)
        
        # Check backup exists
        backup_file = self.dm.data_dir / 'backup_test.backup.json'
        self.assertTrue(backup_file.exists())
        
        # Verify backup contains initial data
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_data = json.load(f)
        self.assertEqual(backup_data, initial_data)

if __name__ == '__main__':
    unittest.main(verbosity=2)
