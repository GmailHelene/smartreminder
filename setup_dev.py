#!/usr/bin/env python3
"""
Development setup script for Smart Påminner Pro
Installs dependencies and sets up development environment
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False

def main():
    """Main setup function"""
    print("🚀 Setting up Smart Påminner Pro development environment...")
    print("-" * 60)
    
    # Check Python version
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        sys.exit(1)
    
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor} detected")
    
    # Install requirements
    if not run_command([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'], 
                      "Installing dependencies"):
        print("⚠️  Some dependencies failed to install. Try manually:")
        print("   pip install -r requirements.txt")
    
    # Create data directory
    data_dir = Path('data')
    data_dir.mkdir(exist_ok=True)
    print("✅ Data directory created")
    
    # Check for .env file
    env_file = Path('.env')
    if not env_file.exists():
        env_example = Path('.env.example')
        if env_example.exists():
            print("📋 Creating .env file from example...")
            import shutil
            shutil.copy2(env_example, env_file)
            print("⚠️  Please edit .env with your settings!")
        else:
            print("⚠️  No .env.example found. Please create .env manually.")
    
    print("-" * 60)
    print("🎉 Setup completed!")
    print("🚀 Run the app with: python run_local.py")
    print("🧪 Run tests with: python -m pytest tests/")

if __name__ == '__main__':
    main()
