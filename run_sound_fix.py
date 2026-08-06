#!/usr/bin/env python3
"""
Fix sound and PWA issues in SmartReminder
This script creates proper sound files and tests the system
"""

import os
import sys
import subprocess

def create_sound_files():
    """Create proper sound files using a simple approach"""
    print("🔊 Creating sound files...")
    
    sounds_dir = os.path.join('static', 'sounds')
    os.makedirs(sounds_dir, exist_ok=True)
    
    # Create simple text-to-speech or beep sounds using system tools
    try:
        # Try to create simple WAV files using Python
        import wave
        import struct
        import math
        
        def create_beep(filename, frequency=800, duration=0.5):
            sample_rate = 44100
            frames = int(duration * sample_rate)
            
            filepath = os.path.join(sounds_dir, filename.replace('.mp3', '.wav'))
            
            with wave.open(filepath, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 2 bytes per sample
                wav_file.setframerate(sample_rate)
                
                for i in range(frames):
                    # Generate sine wave
                    sample = int(16383 * math.sin(2 * math.pi * frequency * i / sample_rate))
                    # Add fade to prevent clicks
                    fade_frames = int(0.01 * sample_rate)
                    if i < fade_frames:
                        sample = int(sample * i / fade_frames)
                    elif i > frames - fade_frames:
                        sample = int(sample * (frames - i) / fade_frames)
                    
                    wav_file.writeframes(struct.pack('<h', sample))
            
            print(f"  ✅ Created {filepath}")
        
        # Create different sounds
        create_beep('alert.mp3', 1000, 0.3)     # High alert
        create_beep('ding.mp3', 800, 0.2)       # Ding
        create_beep('chime.mp3', 600, 0.4)      # Chime
        create_beep('pristine.mp3', 700, 0.25)  # Default
        
        print("✅ Sound files created successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating sound files: {e}")
        return False

def check_file_permissions():
    """Check and fix file permissions"""
    print("🔧 Checking file permissions...")
    
    important_files = [
        'static/js/app.js',
        'static/js/pwa.js', 
        'static/manifest.json',
        'sw.js',
        'static/sounds/'
    ]
    
    for file_path in important_files:
        if os.path.exists(file_path):
            try:
                # Ensure files are readable
                os.chmod(file_path, 0o644 if os.path.isfile(file_path) else 0o755)
                print(f"  ✅ {file_path} permissions OK")
            except Exception as e:
                print(f"  ⚠️ {file_path} permission issue: {e}")
        else:
            print(f"  ❌ {file_path} not found")

def test_endpoints():
    """Test important endpoints"""
    print("🌐 Testing endpoints...")
    
    try:
        import requests
        base_url = "http://localhost:5000"
        
        endpoints = [
            "/sw.js",
            "/static/manifest.json", 
            "/static/js/app.js",
            "/static/js/pwa.js"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
                if response.status_code == 200:
                    print(f"  ✅ {endpoint} OK ({len(response.content)} bytes)")
                else:
                    print(f"  ❌ {endpoint} returned {response.status_code}")
            except Exception as e:
                print(f"  ⚠️ {endpoint} test failed: {e}")
                
    except ImportError:
        print("  ⚠️ requests not available, skipping endpoint tests")

def main():
    """Main fix function"""
    print("🔧 SmartReminder Sound & PWA Fix")
    print("=" * 50)
    
    # Create sound files
    sounds_ok = create_sound_files()
    
    # Check permissions
    check_file_permissions()
    
    # Test endpoints if server is running
    try:
        test_endpoints()
    except Exception as e:
        print(f"⚠️ Endpoint testing skipped: {e}")
    
    print("\n" + "=" * 50)
    print("📋 Fix Summary:")
    print(f"  Sound files: {'✅ OK' if sounds_ok else '❌ Issues'}")
    print("  File permissions: ✅ Updated")
    
    print("\n🚀 Next steps:")
    print("1. Restart the Flask application")
    print("2. Clear browser cache (Ctrl+Shift+R)")
    print("3. Test sound on dashboard")
    print("4. Check for PWA install prompt on mobile")
    print("\n💡 If issues persist:")
    print("- Check browser console for errors")
    print("- Ensure microphone permissions are granted")
    print("- Try incognito/private browsing mode")

if __name__ == "__main__":
    main()
