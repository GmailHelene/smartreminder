#!/usr/bin/env python3
"""
Manual testing script for Smart Påminner Pro
Run this to test the app manually with realistic data
"""

import requests
import json
import time
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# Fix encoding for Windows console
if os.name == 'nt':  # Windows
    os.system('chcp 65001 > nul')  # Set console to UTF-8
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Add project directory to path
project_dir = Path(__file__).parent.parent
sys.path.insert(0, str(project_dir))

class ManualTester:
    def __init__(self, base_url='http://localhost:5000'):
        self.base_url = base_url
        self.session = requests.Session()
        self.test_results = []
    
    def log_test(self, test_name, success, details=''):
        """Log test results"""
        status = "[PASS]" if success else "[FAIL]"
        print(f"{status} {test_name}")
        if details:
            print(f"   {details}")
        
        self.test_results.append({
            'test': test_name,
            'success': success,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
    
    def test_basic_routes(self):
        """Test basic routes and pages"""
        print("\n🌐 Testing Basic Routes...")
        
        routes_to_test = [
            ('/', 'Index page'),
            ('/login', 'Login page'),
            ('/health', 'Health check'),
            ('/offline', 'Offline page'),
        ]
        
        for route, description in routes_to_test:
            try:
                response = self.session.get(f"{self.base_url}{route}")
                success = response.status_code in [200, 302]
                self.log_test(f"GET {route} ({description})", success, 
                            f"Status: {response.status_code}")
            except Exception as e:
                self.log_test(f"GET {route}", False, f"Error: {str(e)}")
    
    def test_authentication(self):
        """Test authentication flow"""
        print("\n🔐 Testing Authentication...")
        
        # Test registration
        try:
            test_email = f"test_{int(time.time())}@example.com"
            response = self.session.post(f"{self.base_url}/register", data={
                'username': test_email,
                'password': 'testpass123'
            }, allow_redirects=False)
            
            success = response.status_code == 302
            self.log_test("User Registration", success, 
                        f"Status: {response.status_code}")
            
            if success:
                # Test login with new user
                response = self.session.post(f"{self.base_url}/login", data={
                    'username': test_email,
                    'password': 'testpass123'
                }, allow_redirects=False)
                
                login_success = response.status_code == 302
                self.log_test("User Login", login_success, 
                            f"Status: {response.status_code}")
                
                return login_success, test_email
                
        except Exception as e:
            self.log_test("Authentication", False, f"Error: {str(e)}")
            
        return False, None
    
    def test_dashboard_and_reminders(self, user_email):
        """Test dashboard and reminder functionality"""
        print("\n📋 Testing Dashboard and Reminders...")
        
        # Test dashboard access
        try:
            response = self.session.get(f"{self.base_url}/dashboard")
            success = response.status_code == 200
            self.log_test("Dashboard Access", success, 
                        f"Status: {response.status_code}")
            
            if success and b'Dashboard' in response.content:
                self.log_test("Dashboard Content", True, "Dashboard loads correctly")
            else:
                self.log_test("Dashboard Content", False, "Dashboard content missing")
            
        except Exception as e:
            self.log_test("Dashboard Access", False, f"Error: {str(e)}")
        
        # Test creating reminder
        try:
            tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            response = self.session.post(f"{self.base_url}/add_reminder", data={
                'title': 'Test Påminnelse',
                'description': 'Dette er en test påminnelse',
                'date': tomorrow,
                'time': '14:30',
                'priority': 'Høy',
                'category': 'Jobb'
            }, allow_redirects=False)
            
            success = response.status_code == 302
            self.log_test("Create Reminder", success, 
                        f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Create Reminder", False, f"Error: {str(e)}")
    
    def test_api_endpoints(self):
        """Test API endpoints"""
        print("\n🔌 Testing API Endpoints...")
        
        api_endpoints = [
            ('/api/reminder-count', 'Reminder Count API'),
            ('/email-log', 'Email Log API'),
        ]
        
        for endpoint, description in api_endpoints:
            try:
                response = self.session.get(f"{self.base_url}{endpoint}")
                success = response.status_code == 200
                
                if success:
                    try:
                        data = response.json()
                        self.log_test(f"API {endpoint}", True, 
                                    f"Returns valid JSON: {type(data)}")
                    except:
                        self.log_test(f"API {endpoint}", False, 
                                    "Response is not valid JSON")
                else:
                    self.log_test(f"API {endpoint}", False, 
                                f"Status: {response.status_code}")
                    
            except Exception as e:
                self.log_test(f"API {endpoint}", False, f"Error: {str(e)}")
    
    def test_focus_modes(self):
        """Test focus modes functionality"""
        print("\n🧠 Testing Focus Modes...")
        
        try:
            # Test focus modes page
            response = self.session.get(f"{self.base_url}/focus-modes")
            success = response.status_code == 200
            self.log_test("Focus Modes Page", success, 
                        f"Status: {response.status_code}")
            
            # Test setting focus mode
            response = self.session.post(f"{self.base_url}/set-focus-mode", data={
                'focus_mode': 'adhd'
            }, allow_redirects=False)
            
            success = response.status_code == 302
            self.log_test("Set Focus Mode", success, 
                        f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Focus Modes", False, f"Error: {str(e)}")
    
    def test_noteboards(self):
        """Test noteboard functionality"""
        print("\n📋 Testing Noteboards...")
        
        try:
            # Test noteboards page
            response = self.session.get(f"{self.base_url}/noteboards")
            success = response.status_code == 200
            self.log_test("Noteboards Page", success, 
                        f"Status: {response.status_code}")
            
            # Test creating board
            response = self.session.post(f"{self.base_url}/create-board", data={
                'title': 'Test Tavle',
                'description': 'Dette er en test tavle'
            }, allow_redirects=False)
            
            success = response.status_code == 302
            self.log_test("Create Noteboard", success, 
                        f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Noteboards", False, f"Error: {str(e)}")
    
    def test_email_functionality(self):
        """Test email-related functionality"""
        print("\n📧 Testing Email Functionality...")
        
        try:
            # Test email settings page
            response = self.session.get(f"{self.base_url}/email-settings")
            success = response.status_code == 200
            self.log_test("Email Settings Page", success, 
                        f"Status: {response.status_code}")
            
        except Exception as e:
            self.log_test("Email Settings", False, f"Error: {str(e)}")
    
    def run_all_tests(self):
        """Run all tests"""
        print("Starting Manual Testing of Smart Paminner Pro")
        print("=" * 50)
        
        start_time = time.time()
        
        # Basic tests
        self.test_basic_routes()
        
        # Authentication tests
        auth_success, user_email = self.test_authentication()
        
        if auth_success:
            # Tests that require authentication
            self.test_dashboard_and_reminders(user_email)
            self.test_api_endpoints()
            self.test_focus_modes()
            self.test_noteboards()
            self.test_email_functionality()
        else:
            print("\nSkipping authenticated tests due to auth failure")
        
        # Print summary
        end_time = time.time()
        duration = end_time - start_time
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t['success']])
        failed_tests = total_tests - passed_tests
        
        print("\n" + "=" * 50)
        print(f"TEST SUMMARY")
        print(f"Total tests: {total_tests}")
        print(f"Passed: {passed_tests} [PASS]")
        print(f"Failed: {failed_tests} [FAIL]")
        print(f"Success rate: {(passed_tests/total_tests*100):.1f}%")
        print(f"Duration: {duration:.2f} seconds")
        
        # Save results
        results_file = Path(__file__).parent / 'test_results.json'
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                'summary': {
                    'total': total_tests,
                    'passed': passed_tests,
                    'failed': failed_tests,
                    'success_rate': passed_tests/total_tests*100,
                    'duration': duration,
                    'timestamp': datetime.now().isoformat()
                },
                'tests': self.test_results
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed results saved to: {results_file}")
        
        if failed_tests > 0:
            print("\nFailed tests:")
            for test in self.test_results:
                if not test['success']:
                    print(f"  - {test['test']}: {test['details']}")
        
        return failed_tests == 0

def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Manual testing for Smart Påminner Pro')
    parser.add_argument('--url', default='http://localhost:5000', 
                       help='Base URL for the app (default: http://localhost:5000)')
    parser.add_argument('--wait', type=int, default=1,
                       help='Wait time between requests in seconds (default: 1)')
    
    args = parser.parse_args()
    
    print(f"Testing app at: {args.url}")
    print(f"Wait time between requests: {args.wait}s")
    
    tester = ManualTester(args.url)
    
    try:
        success = tester.run_all_tests()
        exit_code = 0 if success else 1
        print(f"\nTesting completed with exit code: {exit_code}")
        sys.exit(exit_code)
        
    except KeyboardInterrupt:
        print("\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nTesting failed with error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
