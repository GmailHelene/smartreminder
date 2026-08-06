import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add project directory to path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# Mock APScheduler before importing app
import unittest.mock as mock
sys.modules['apscheduler'] = mock.MagicMock()
sys.modules['apscheduler.schedulers'] = mock.MagicMock()
sys.modules['apscheduler.schedulers.background'] = mock.MagicMock()

# Set testing environment
os.environ['FLASK_ENV'] = 'testing'

from app import app, dm

class SmartReminderTestCase(unittest.TestCase):
    
    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        
        # Configure app for testing
        app.config.update({
            'TESTING': True,
            'WTF_CSRF_ENABLED': False,
            'SECRET_KEY': 'test-secret-key',
            'MAIL_SUPPRESS_SEND': True
        })
        
        # Override data manager for testing
        dm.data_dir = Path(self.test_dir)
        dm._ensure_data_files()
        
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
    
    def tearDown(self):
        """Clean up test fixtures"""
        self.app_context.pop()
        import shutil
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_index_redirect(self):
        """Test index page redirects to login"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 302)
    
    def test_login_page(self):
        """Test login page loads"""
        response = self.app.get('/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Smart P\xc3\xa5minner Pro', response.data)
    
    def test_health_check(self):
        """Test health check endpoint"""
        response = self.app.get('/health')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'healthy')
    
    def test_user_registration(self):
        """Test user registration"""
        response = self.app.post('/register', data={
            'username': 'test@example.com',
            'password': 'testpassword123'
        }, follow_redirects=False)
        
        # Should redirect after successful registration
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_requires_login(self):
        """Test dashboard requires authentication"""
        response = self.app.get('/dashboard')
        self.assertEqual(response.status_code, 302)  # Redirect to login
    
    def test_offline_page(self):
        """Test offline page loads"""
        response = self.app.get('/offline')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'offline', response.data.lower())
    
    def test_static_files(self):
        """Test static files are served correctly"""
        # Test service worker with proper cleanup
        with self.app as client:
            response = client.get('/static/sw.js')
            self.assertEqual(response.status_code, 200)
            # Close the response to prevent resource warnings
            response.close()
        
        # Test manifest with proper cleanup
        with self.app as client:
            response = client.get('/static/manifest.json')
            self.assertEqual(response.status_code, 200)
            response.close()
    
    def test_error_handling(self):
        """Test error pages"""
        response = self.app.get('/nonexistent-page')
        self.assertEqual(response.status_code, 404)

if __name__ == '__main__':
    unittest.main(verbosity=2)
