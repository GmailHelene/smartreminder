#!/usr/bin/env python3
"""
Complete test for PWA functionality and mobile notifications
Tests all aspects of PWA installation and notification system
"""

import os
import sys
import json
from datetime import datetime

def test_pwa_manifest():
    """Test PWA manifest.json configuration"""
    print("🔍 Testing PWA manifest...")
    
    manifest_path = "/workspaces/smartreminder/static/manifest.json"
    
    if not os.path.exists(manifest_path):
        print("❌ Manifest file not found")
        return False
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        required_fields = ['name', 'short_name', 'start_url', 'display', 'icons']
        missing_fields = [field for field in required_fields if field not in manifest]
        
        if missing_fields:
            print(f"❌ Missing required manifest fields: {missing_fields}")
            return False
        
        # Check icons
        if len(manifest.get('icons', [])) < 3:
            print("❌ Manifest should have at least 3 icons")
            return False
        
        print("✅ Manifest validation passed")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Manifest JSON is invalid: {e}")
        return False
    except Exception as e:
        print(f"❌ Error reading manifest: {e}")
        return False

def test_service_worker():
    """Test Service Worker implementation"""
    print("\n🔧 Testing Service Worker...")
    
    sw_path = "/workspaces/smartreminder/sw.js"
    
    if not os.path.exists(sw_path):
        print("❌ Service Worker file not found")
        return False
    
    try:
        with open(sw_path, 'r') as f:
            sw_content = f.read()
        
        required_features = [
            "addEventListener('install'",
            "addEventListener('activate'", 
            "addEventListener('push'",
            "addEventListener('notificationclick'",
            "showNotification"
        ]
        
        missing_features = [feature for feature in required_features if feature not in sw_content]
        
        if missing_features:
            print(f"❌ Service Worker missing features: {missing_features}")
            return False
        
        print("✅ Service Worker validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error reading Service Worker: {e}")
        return False

def test_pwa_javascript():
    """Test PWA JavaScript implementation"""
    print("\n📱 Testing PWA JavaScript...")
    
    pwa_js_path = "/workspaces/smartreminder/static/js/pwa.js"
    
    if not os.path.exists(pwa_js_path):
        print("❌ PWA JavaScript file not found")
        return False
    
    try:
        with open(pwa_js_path, 'r') as f:
            pwa_content = f.read()
        
        required_features = [
            "beforeinstallprompt",
            "deferredPrompt",
            "showInstallPrompt",
            "installPWA"
        ]
        
        missing_features = [feature for feature in required_features if feature not in pwa_content]
        
        if missing_features:
            print(f"❌ PWA JavaScript missing features: {missing_features}")
            return False
        
        print("✅ PWA JavaScript validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error reading PWA JavaScript: {e}")
        return False

def test_notification_javascript():
    """Test notification JavaScript implementation"""
    print("\n🔔 Testing notification JavaScript...")
    
    app_js_path = "/workspaces/smartreminder/static/js/app.js"
    
    if not os.path.exists(app_js_path):
        print("❌ App JavaScript file not found")
        return False
    
    try:
        with open(app_js_path, 'r') as f:
            app_content = f.read()
        
        required_features = [
            "playNotificationSound",
            "requestNotificationPermission",
            "setupPushNotifications"
        ]
        
        present_features = [feature for feature in required_features if feature in app_content]
        
        if len(present_features) < 2:
            print(f"❌ App JavaScript missing notification features")
            return False
        
        print("✅ Notification JavaScript validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error reading app JavaScript: {e}")
        return False

def test_dashboard_integration():
    """Test dashboard PWA integration"""
    print("\n🎯 Testing dashboard PWA integration...")
    
    dashboard_path = "/workspaces/smartreminder/templates/dashboard.html"
    
    if not os.path.exists(dashboard_path):
        print("❌ Dashboard template not found")
        return False
    
    try:
        with open(dashboard_path, 'r') as f:
            dashboard_content = f.read()
        
        pwa_features = [
            "pwa.js",
            "app.js"
        ]
        
        present_features = [feature for feature in pwa_features if feature in dashboard_content]
        
        if len(present_features) < 2:
            print(f"❌ Dashboard missing PWA script includes")
            return False
        
        print("✅ Dashboard PWA integration validation passed")
        return True
        
    except Exception as e:
        print(f"❌ Error reading dashboard template: {e}")
        return False

def test_sound_files():
    """Test notification sound files"""
    print("\n🔊 Testing notification sound files...")
    
    sounds_dir = "/workspaces/smartreminder/static/sounds"
    
    if not os.path.exists(sounds_dir):
        print("❌ Sounds directory not found")
        return False
    
    try:
        required_sounds = ['pristine.mp3', 'alert.mp3', 'ding.mp3', 'chime.mp3']
        found_sounds = []
        
        for sound_file in required_sounds:
            sound_path = os.path.join(sounds_dir, sound_file)
            if os.path.exists(sound_path):
                found_sounds.append(sound_file)
            else:
                print(f"⚠️ Sound file missing: {sound_file}")
        
        if len(found_sounds) < 2:
            print("❌ Too few sound files found")
            return False
        
        print(f"✅ Sound files validation passed ({len(found_sounds)}/{len(required_sounds)} files)")
        return True
        
    except Exception as e:
        print(f"❌ Error checking sound files: {e}")
        return False

def test_icon_files():
    """Test PWA icon files"""
    print("\n🖼️ Testing PWA icon files...")
    
    images_dir = "/workspaces/smartreminder/static/images"
    
    if not os.path.exists(images_dir):
        print("❌ Images directory not found")
        return False
    
    try:
        required_icons = [
            'icon-72x72.png',
            'icon-96x96.png', 
            'icon-128x128.png',
            'icon-144x144.png',
            'icon-152x152.png',
            'icon-192x192.png',
            'icon-384x384.png',
            'icon-512x512.png'
        ]
        
        found_icons = []
        
        for icon_file in required_icons:
            icon_path = os.path.join(images_dir, icon_file)
            if os.path.exists(icon_path):
                found_icons.append(icon_file)
            else:
                print(f"⚠️ Icon file missing: {icon_file}")
        
        if len(found_icons) < 4:
            print("❌ Too few icon files found")
            return False
        
        print(f"✅ Icon files validation passed ({len(found_icons)}/{len(required_icons)} files)")
        return True
        
    except Exception as e:
        print(f"❌ Error checking icon files: {e}")
        return False

def run_complete_pwa_test():
    """Run complete PWA and notification test"""
    print("🚀 Starting complete PWA and notification system test")
    print("=" * 60)
    
    tests = [
        ("PWA Manifest", test_pwa_manifest),
        ("Service Worker", test_service_worker),
        ("PWA JavaScript", test_pwa_javascript),
        ("Notification JavaScript", test_notification_javascript),
        ("Dashboard Integration", test_dashboard_integration),
        ("Sound Files", test_sound_files),
        ("Icon Files", test_icon_files)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} test failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! PWA is ready for deployment.")
    elif passed >= total * 0.7:
        print("⚠️ Most tests passed. Some minor issues need attention.")
    else:
        print("❌ Multiple issues found. Please fix before deployment.")
    
    return passed == total

if __name__ == "__main__":
    success = run_complete_pwa_test()
    sys.exit(0 if success else 1)
    
    return passed == total

if __name__ == "__main__":
    success = run_complete_pwa_test()
    exit(0 if success else 1)
        
        return len(sound_files) > 0
        
    except Exception as e:
        print(f"   ❌ Error checking sound files: {e}")
        return False

def test_icon_files():
    """Test PWA icon files"""
    print("\n🖼️ Testing PWA icon files...")
    
    images_dir = "/workspaces/smartreminder/static/images"
    
    if not os.path.exists(images_dir):
        print("   ❌ Images directory not found")
        return False
    
    try:
        image_files = os.listdir(images_dir)
        print(f"   ℹ️ Found {len(image_files)} image files")
        
        # Check for required PWA icons
        required_icons = [
            'icon-192x192.png',
            'icon-512x512.png',
            'badge-96x96.png'
        ]
        
        for icon in required_icons:
            if icon in image_files:
                print(f"   ✅ Required icon {icon} found")
            else:
                print(f"   ❌ Required icon {icon} missing")
        
        # Check for additional recommended icons
        recommended_icons = [
            'icon-72x72.png',
            'icon-96x96.png',
            'icon-128x128.png',
            'icon-144x144.png',
            'icon-152x152.png',
            'icon-384x384.png'
        ]
        
        found_recommended = 0
        for icon in recommended_icons:
            if icon in image_files:
                found_recommended += 1
        
        print(f"   ℹ️ Found {found_recommended}/{len(recommended_icons)} recommended icons")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error checking icon files: {e}")
        return False

def run_complete_pwa_test():
    """Run complete PWA and notification test"""
    print("🚀 Starting complete PWA and notification system test")
    print("=" * 60)
    
    tests = [
        ("PWA Manifest", test_pwa_manifest),
        ("Service Worker", test_service_worker),
        ("PWA JavaScript", test_pwa_javascript),
        ("Notification JavaScript", test_notification_javascript),
        ("Dashboard Integration", test_dashboard_integration),
        ("Sound Files", test_sound_files),
        ("Icon Files", test_icon_files)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   💥 Test {test_name} failed with error: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n📈 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("🎉 All PWA and notification tests passed!")
        print("✅ PWA functionality is ready for mobile deployment")
        print("✅ Notification system is fully functional")
    else:
        print("⚠️ Some tests failed. Please fix the issues above.")
        print("📱 PWA may not work optimally on mobile devices")
        print("🔔 Notification system may have issues")
    
    return passed == total

if __name__ == "__main__":
    success = run_complete_pwa_test()
    exit(0 if success else 1)
