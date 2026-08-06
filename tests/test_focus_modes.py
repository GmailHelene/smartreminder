import unittest
import tempfile
import os
import sys
from pathlib import Path

# Add project directory to path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

# Mock APScheduler
import unittest.mock as mock
sys.modules['apscheduler'] = mock.MagicMock()
sys.modules['apscheduler.schedulers'] = mock.MagicMock()
sys.modules['apscheduler.schedulers.background'] = mock.MagicMock()

os.environ['FLASK_ENV'] = 'testing'
os.environ['TESTING'] = 'true'

from focus_modes import FocusModeManager, SilentMode, ADHDMode, ElderlyMode

class TestFocusModes(unittest.TestCase):
    """Test focus modes functionality"""
    
    def test_focus_mode_manager(self):
        """Test the focus mode manager"""
        # Test getting all modes
        modes = FocusModeManager.get_all_modes()
        self.assertIsInstance(modes, dict)
        self.assertIn('normal', modes)
        self.assertIn('silent', modes)
        self.assertIn('adhd', modes)
        self.assertIn('elderly', modes)
    
    def test_silent_mode(self):
        """Test silent mode functionality"""
        mode = SilentMode()
        self.assertEqual(mode.name, "Stillemodus")
        
        # Test filtering reminders
        reminders = [
            {'priority': 'Høy', 'title': 'Important'},
            {'priority': 'Medium', 'title': 'Regular'},
            {'priority': 'Lav', 'title': 'Low'}
        ]
        
        filtered = mode.apply_to_reminders(reminders)
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]['priority'], 'Høy')
    
    def test_adhd_mode(self):
        """Test ADHD mode functionality"""
        mode = ADHDMode()
        self.assertEqual(mode.name, "ADHD-modus")
        
        # Test reminder enhancement
        from datetime import datetime, timedelta
        reminders = [{
            'datetime': (datetime.now() + timedelta(minutes=30)).isoformat(),
            'title': 'Test reminder'
        }]
        
        enhanced = mode.apply_to_reminders(reminders)
        self.assertIn('urgency', enhanced[0])
        self.assertIn('time_until', enhanced[0])
    
    def test_elderly_mode(self):
        """Test elderly mode functionality"""
        mode = ElderlyMode()
        self.assertEqual(mode.name, "Modus for eldre")
        
        settings = mode.get_notification_settings()
        self.assertTrue(settings['large_text'])
        self.assertTrue(settings['email_enabled'])

if __name__ == '__main__':
    unittest.main(verbosity=2)
