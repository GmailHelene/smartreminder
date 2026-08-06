#!/usr/bin/env python3
"""
Create sound files for SmartReminder notifications
This script creates basic sound files using system tools or Python audio libraries
"""

import os
import sys
import wave
import struct
import math
from pathlib import Path

def create_beep_sound(filename, frequency=800, duration=0.5, sample_rate=44100):
    """Create a simple beep sound"""
    
    sounds_dir = Path('static/sounds')
    sounds_dir.mkdir(parents=True, exist_ok=True)
    
    # Create both WAV and MP3 versions
    wav_path = sounds_dir / filename.replace('.mp3', '.wav')
    
    print(f"Creating {wav_path}...")
    
    # Generate sine wave with fade in/out
    frames = int(duration * sample_rate)
    sound_data = []
    
    for i in range(frames):
        # Generate sine wave sample
        sample = int(16383 * math.sin(2 * math.pi * frequency * i / sample_rate))
        
        # Add fade in/out to prevent clicks (10ms fade)
        fade_frames = int(0.01 * sample_rate)
        if i < fade_frames:
            sample = int(sample * i / fade_frames)
        elif i > frames - fade_frames:
            sample = int(sample * (frames - i) / fade_frames)
        
        # Pack as 16-bit signed integer, stereo
        sound_data.append(struct.pack('<hh', sample, sample))
    
    # Write WAV file
    try:
        with wave.open(str(wav_path), 'wb') as wav_file:
            wav_file.setnchannels(2)  # Stereo
            wav_file.setsampwidth(2)  # 2 bytes per sample
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(sound_data))
        
        print(f"✅ Created {wav_path} ({len(sound_data)} frames)")
        
        # Also create a symbolic link or copy as MP3 for compatibility
        mp3_path = sounds_dir / filename
        if mp3_path.exists():
            mp3_path.unlink()
        
        # For web compatibility, just copy the WAV as MP3
        # (browsers will handle the format detection)
        import shutil
        shutil.copy(wav_path, mp3_path)
        print(f"✅ Created {mp3_path} (copy of WAV)")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create {wav_path}: {e}")
        return False

def create_chord_sound(filename, frequencies, duration=0.6, sample_rate=44100):
    """Create a chord sound with multiple frequencies"""
    
    sounds_dir = Path('static/sounds')
    sounds_dir.mkdir(parents=True, exist_ok=True)
    
    wav_path = sounds_dir / filename.replace('.mp3', '.wav')
    
    print(f"Creating chord {wav_path} with frequencies {frequencies}...")
    
    frames = int(duration * sample_rate)
    sound_data = []
    
    for i in range(frames):
        # Mix multiple frequencies
        sample = 0
        for freq in frequencies:
            sample += int(8191 * math.sin(2 * math.pi * freq * i / sample_rate))
        
        # Normalize
        sample = int(sample / len(frequencies))
        
        # Add fade in/out
        fade_frames = int(0.02 * sample_rate)  # 20ms fade for chords
        if i < fade_frames:
            sample = int(sample * i / fade_frames)
        elif i > frames - fade_frames:
            sample = int(sample * (frames - i) / fade_frames)
        
        # Pack as stereo
        sound_data.append(struct.pack('<hh', sample, sample))
    
    try:
        with wave.open(str(wav_path), 'wb') as wav_file:
            wav_file.setnchannels(2)
            wav_file.setsampwidth(2)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(sound_data))
        
        print(f"✅ Created chord {wav_path}")
        
        # Also create MP3 copy
        mp3_path = sounds_dir / filename
        if mp3_path.exists():
            mp3_path.unlink()
        
        import shutil
        shutil.copy(wav_path, mp3_path)
        print(f"✅ Created {mp3_path} (copy of WAV)")
        
        return True
    except Exception as e:
        print(f"❌ Failed to create {wav_path}: {e}")
        return False

def create_all_sounds():
    """Create all notification sounds"""
    print("🔊 Creating SmartReminder notification sounds...")
    
    sounds_created = 0
    
    # Simple beeps with different characteristics
    if create_beep_sound('alert.mp3', frequency=1200, duration=0.3):
        sounds_created += 1
    
    if create_beep_sound('ding.mp3', frequency=800, duration=0.2):
        sounds_created += 1
    
    # Chord sounds
    if create_chord_sound('chime.mp3', [523, 659, 784], duration=0.5):  # C-E-G major chord
        sounds_created += 1
    
    if create_chord_sound('pristine.mp3', [440, 554, 659], duration=0.4):  # A-C#-E major chord
        sounds_created += 1
    
    print(f"\n✅ Successfully created {sounds_created}/4 sound files!")
    
    if sounds_created > 0:
        print("\nSound files created in static/sounds/ directory:")
        sounds_dir = Path('static/sounds')
        for sound_file in sounds_dir.glob('*.wav'):
            size = sound_file.stat().st_size
            print(f"  📄 {sound_file.name} ({size} bytes)")
        for sound_file in sounds_dir.glob('*.mp3'):
            size = sound_file.stat().st_size
            print(f"  📄 {sound_file.name} ({size} bytes)")
        
        print("\n💡 Next steps:")
        print("1. Test sounds in your browser: python3 test_sound_playback.py")
        print("2. Restart your SmartReminder application")
        print("3. Test sound on dashboard")
    else:
        print("❌ No sound files were created successfully")
    
    return sounds_created > 0

if __name__ == "__main__":
    create_all_sounds()
