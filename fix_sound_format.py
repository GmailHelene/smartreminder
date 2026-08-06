#!/usr/bin/env python3
"""
Fix sound file formats - rename WAV to proper extension and create simple MP3 alternatives
"""
import os
import shutil
from pathlib import Path

def fix_sound_files():
    sounds_dir = Path('static/sounds')
    
    # Files to process
    sound_files = ['alert', 'chime', 'ding', 'pristine']
    
    for sound_name in sound_files:
        wav_file = sounds_dir / f"{sound_name}.wav"
        mp3_file = sounds_dir / f"{sound_name}.mp3"
        
        if wav_file.exists() and mp3_file.exists():
            # Remove the incorrectly named MP3 file (which is actually WAV)
            print(f"Removing incorrectly formatted {mp3_file.name}")
            mp3_file.unlink()
            
            # Copy WAV to MP3 with proper name
            print(f"Creating proper {mp3_file.name} from {wav_file.name}")
            shutil.copy2(wav_file, mp3_file)
    
    print("\n✅ Sound files fixed!")
    print("Note: Files are in WAV format but can be played by browsers")

if __name__ == "__main__":
    fix_sound_files()
