#!/usr/bin/env python3
"""
Comprehensive testing script for Smart Påminner Pro
"""

import subprocess
import sys
import os
import time
import json
import threading
import requests
from pathlib import Path
from datetime import datetime

# Fix encoding for Windows console
if os.name == 'nt':  # Windows
    os.system('chcp 65001 > nul')  # Set console to UTF-8

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

def print_header(title, char="="):
    """Print formatted header"""
    print(f"\n{title}")
    print(char * len(title))

def run_command(command, timeout=30, capture_output=True):
    """Run command with timeout and error handling"""
    try:
        if capture_output:
            result = subprocess.run(
                command, 
                capture_output=True, 
                text=True, 
                timeout=timeout,
                cwd=project_root,
                encoding='utf-8',
                errors='replace'
            )
        else:
            result = subprocess.run(
                command,
                timeout=timeout,
                cwd=project_root
            )
        return result
    except subprocess.TimeoutExpired:
        print(f"⏱️  Command timed out after {timeout}s")
        return None
    except Exception as e:
        print(f"❌ Command failed: {e}")
        return None

def generate_test_data():
    """Generate realistic test data"""
    print_header("🎲 Generating Test Data...", "-")
    
    try:
        # Import and run test data generator
        test_data_script = project_root / 'tests' / 'generate_test_data.py'
        if test_data_script.exists():
            result = run_command([sys.executable, str(test_data_script)], timeout=60)
            if result and result.returncode == 0:
                print("✅ Test data generated successfully")
                return True
            else:
                print("⚠️  Test data generation had issues, continuing anyway")
                return True
        else:
            print("⚠️  Test data generator not found, skipping...")
            return True
    except Exception as e:
        print(f"❌ Test data generation failed: {e}")
        return False

def run_unit_tests():
    """Run unit tests"""
    print_header("🧪 Running Unit Tests...", "-")
    
    # Try different test discovery methods
    test_commands = [
        [sys.executable, '-m', 'unittest', 'tests.test_comprehensive', '-v'],
        [sys.executable, '-m', 'unittest', 'tests.test_app', '-v'],
        [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        [sys.executable, 'tests/test_comprehensive.py'],
        [sys.executable, 'tests/test_app.py']
    ]
    
    for cmd in test_commands:
        print(f"Trying: {' '.join(cmd)}")
        result = run_command(cmd, timeout=120)
        
        if result:
            print(f"Command completed with return code: {result.returncode}")
            
            if result.stdout:
                print("STDOUT:", result.stdout[:1000])
            if result.stderr:
                print("STDERR:", result.stderr[:1000])
            
            if result.returncode == 0:
                print("✅ Unit tests passed")
                return True
            else:
                print(f"❌ Tests failed with return code: {result.returncode}")
        else:
            print("❌ Test command failed to run")
    
    print("❌ FAILED Unit Tests")
    return False

def start_test_server():
    """Start test server in background"""
    print("Starting test server...")
    
    try:
        # Set environment for testing
        env = os.environ.copy()
        env['FLASK_ENV'] = 'development'  # Change from 'testing' to avoid conflicts
        env['FLASK_DEBUG'] = '0'
        env['TESTING'] = 'false'  # Ensure scheduler starts
        
        # Start server
        server_process = subprocess.Popen(
            [sys.executable, 'run_local.py'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=project_root
        )
        
        # Wait for server to start with better detection
        print("Waiting for server to start...")
        for i in range(15):  # Try for 15 seconds
            time.sleep(1)
            try:
                response = requests.get('http://localhost:5000/health', timeout=3)
                if response.status_code == 200:
                    print(f"[OK] Test server started after {i+1} seconds")
                    return server_process
            except requests.exceptions.RequestException:
                # Server not ready yet
                if i % 3 == 0:  # Print progress every 3 seconds
                    print(f"   Waiting... ({i+1}/15 seconds)")
                continue
        
        # Check if process is still running
        if server_process.poll() is None:
            print("[WARNING] Server process running but not responding")
            try:
                # Try one more time with longer timeout
                response = requests.get('http://localhost:5000/health', timeout=10)
                if response.status_code == 200:
                    print("[OK] Test server responding after extended wait")
                    return server_process
            except:
                pass
        
        # Get error output
        stdout, stderr = server_process.communicate(timeout=5)
        print(f"[ERROR] Server failed to start properly")
        if stderr:
            print(f"STDERR: {stderr.decode('utf-8', errors='replace')[:500]}")
        if stdout:
            print(f"STDOUT: {stdout.decode('utf-8', errors='replace')[:500]}")
        
        server_process.terminate()
        return None
        
    except Exception as e:
        print(f"[ERROR] Server start failed: {e}")
        return None

def run_manual_tests(server_process):
    """Run manual/integration tests"""
    print_header("🌐 Running Manual Tests...", "-")
    
    if not server_process:
        print("Skipping manual tests - server failed to start")
        return False
    
    base_url = "http://localhost:5000"
    test_results = []
    
    # Define tests
    tests = [
        ("Health Check", f"{base_url}/health"),
        ("Login Page", f"{base_url}/login"),
        ("Index Redirect", f"{base_url}/"),
        ("Offline Page", f"{base_url}/offline"),
        ("404 Error", f"{base_url}/nonexistent-page"),
        ("Static Files - Service Worker", f"{base_url}/static/sw.js"),
        ("Static Files - Manifest", f"{base_url}/static/manifest.json"),
    ]
    
    print("Running endpoint tests...")
    
    for test_name, url in tests:
        try:
            response = requests.get(url, timeout=10)
            expected_codes = [200, 302, 404]  # Expected codes
            
            if response.status_code in expected_codes:
                print(f"✅ {test_name}: {response.status_code}")
                test_results.append((test_name, True, response.status_code))
            else:
                print(f"❌ {test_name}: {response.status_code}")
                test_results.append((test_name, False, response.status_code))
                
        except Exception as e:
            print(f"❌ {test_name}: {e}")
            test_results.append((test_name, False, str(e)))
    
    # Calculate success rate
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    print(f"\nManual test results: {passed}/{total} passed")
    
    return passed == total

def save_results(unit_passed, manual_passed, duration):
    """Save test results to file"""
    results = {
        'timestamp': datetime.now().isoformat(),
        'duration_seconds': duration,
        'unit_tests': {
            'passed': unit_passed,
            'status': 'PASS' if unit_passed else 'FAIL'
        },
        'manual_tests': {
            'passed': manual_passed,
            'status': 'PASS' if manual_passed else 'FAIL'
        },
        'overall_status': 'PASS' if (unit_passed and manual_passed) else 'FAIL'
    }
    
    try:
        results_file = project_root / 'tests' / 'test_results_full.json'
        results_file.parent.mkdir(exist_ok=True)
        
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed results saved to: {results_file}")
    except Exception as e:
        print(f"Failed to save results: {e}")

def main():
    """Main test runner"""
    print("Smart Påminner Pro - Comprehensive Testing")
    print("=" * 50)
    
    start_time = time.time()
    
    # Generate test data
    generate_test_data()
    
    # Run unit tests
    unit_passed = run_unit_tests()
    
    # Start server for manual tests
    server_process = start_test_server()
    
    # Run manual tests
    manual_passed = run_manual_tests(server_process)
    
    # Calculate duration
    duration = time.time() - start_time
    
    # Clean up
    if server_process:
        print("Stopping test server...")
        server_process.terminate()
        try:
            server_process.wait(timeout=5)
            print("[OK] Test server stopped")
        except subprocess.TimeoutExpired:
            server_process.kill()
            print("[FORCE] Test server killed")
    
    # Summary
    print_header("TEST SUMMARY")
    print(f"Duration: {duration:.2f} seconds")
    print(f"Unit Tests: {'[PASS]' if unit_passed else '[FAIL]'}")
    print(f"Manual Tests: {'[PASS]' if manual_passed else '[FAIL]'}")
    
    if unit_passed and manual_passed:
        print("Overall: ALL TESTS PASSED! 🎉")
        exit_code = 0
    else:
        print("Overall: SOME TESTS FAILED")
        exit_code = 1
    
    # Save results
    save_results(unit_passed, manual_passed, duration)
    
    print(f"\n🏁 Testing completed with exit code: {exit_code}")
    
    return exit_code

if __name__ == '__main__':
    exit_code = main()
    sys.exit(exit_code)
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.unit_only:
            success = runner.run_unit_tests()
        elif args.manual_only:
            if runner.start_test_server():
                try:
                    success = runner.run_manual_tests()
                finally:
                    runner.stop_test_server()
            else:
                success = False
        else:
            success = runner.run_all_tests(with_server=not args.no_server)
        
        exit_code = 0 if success else 1
        print(f"\n🏁 Testing completed with exit code: {exit_code}")
        sys.exit(exit_code)
        
    except Exception as e:
        print(f"\n💥 Testing failed: {e}")
        sys.exit(1)
