#!/usr/bin/env python3
"""
Create simple audio data URIs for notification sounds
This creates minimal audio files that browsers can play
"""
import base64
from pathlib import Path

# Minimal WAV file header for 1 second 440Hz tone
def create_simple_wav_data(frequency=440, duration=0.5, sample_rate=8000):
    """Create minimal WAV data"""
    import struct
    import math
    
    frames = int(duration * sample_rate)
    
    # WAV header
    wav_header = struct.pack('<4sI4s', b'RIFF', 36 + frames * 2, b'WAVE')
    fmt_chunk = struct.pack('<4sIHHIIHH', b'fmt ', 16, 1, 1, sample_rate, sample_rate * 2, 2, 16)
    data_header = struct.pack('<4sI', b'data', frames * 2)
    
    # Generate simple sine wave
    audio_data = b''
    for i in range(frames):
        sample = int(16383 * math.sin(2 * math.pi * frequency * i / sample_rate))
        audio_data += struct.pack('<h', sample)
    
    return wav_header + fmt_chunk + data_header + audio_data

def create_browser_compatible_sounds():
    """Create minimal sound files that work in browsers"""
    sounds_dir = Path('static/sounds')
    sounds_dir.mkdir(parents=True, exist_ok=True)
    
    # Sound configurations
    sounds = {
        'pristine.wav': (440, 0.3),    # A4 note, short
        'ding.wav': (800, 0.2),        # High ping
        'chime.wav': (523, 0.4),       # C5 note
        'alert.wav': (1000, 0.5)       # Alert tone
    }
    
    for filename, (freq, duration) in sounds.items():
        wav_data = create_simple_wav_data(freq, duration)
        wav_path = sounds_dir / filename
        
        with open(wav_path, 'wb') as f:
            f.write(wav_data)
        
        # Also create .mp3 version (same data, different extension)
        mp3_path = sounds_dir / filename.replace('.wav', '.mp3')
        with open(mp3_path, 'wb') as f:
            f.write(wav_data)
        
        print(f"✅ Created {filename} and {filename.replace('.wav', '.mp3')} ({len(wav_data)} bytes)")
    
    print(f"\n🎵 Created {len(sounds)} sound files!")

if __name__ == "__main__":
    create_browser_compatible_sounds()
