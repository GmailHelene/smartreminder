#!/usr/bin/env python3
"""
Lokal utviklingsserver for Smart Påminner Pro
"""

import os
import sys
from pathlib import Path

# Legg til prosjektmappen i Python path
project_dir = Path(__file__).parent
sys.path.insert(0, str(project_dir))

# Sett miljøvariabler for utvikling
if 'FLASK_ENV' not in os.environ:
    os.environ['FLASK_ENV'] = 'development'
if 'FLASK_DEBUG' not in os.environ:
    os.environ['FLASK_DEBUG'] = '1'

# Import og kjør app
if __name__ == '__main__':
    try:
        # Import with graceful handling
        print("🔧 Importing application modules...")
        
        # Check for required files
        required_files = ['app.py', 'config.py']
        missing_files = []
        for file in required_files:
            if not (project_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            print("📋 Make sure all files are in place")
            sys.exit(1)
        
        from app import app
        
        print("🚀 Starter Smart Påminner Pro...")
        print("📱 Åpne http://localhost:5000 i nettleseren")
        print("⏹️  Trykk Ctrl+C for å stoppe serveren")
        print("-" * 50)
        
        # Check if port is already in use
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('localhost', 5000))
        if result == 0:
            print("⚠️  Port 5000 is already in use. Trying port 5001...")
            port = 5001
        else:
            port = 5000
        sock.close()
        
        app.run(
            host='0.0.0.0',
            port=port,
            debug=True,
            use_reloader=False,  # Disable reloader for testing
            threaded=True
        )
        
    except ImportError as e:
        print(f"❌ Import feil: {e}")
        print("📦 Installer avhengigheter med: pip install -r requirements.txt")
        print("🔧 Eller kjør: python setup_dev.py")
        sys.exit(1)
    except ModuleNotFoundError as e:
        print(f"❌ Modul ikke funnet: {e}")
        print("📦 Noen moduler mangler. Kjør: pip install -r requirements.txt")
        print("💡 Eller kjør: python setup_dev.py")
        sys.exit(1)
    except OSError as e:
        if "Address already in use" in str(e):
            print("❌ Port 5000 er allerede i bruk")
            print("💡 Stopp andre instanser eller vent litt")
        else:
            print(f"❌ OS feil: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Serveren stoppet")
    except Exception as e:
        print(f"❌ Feil ved oppstart: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
