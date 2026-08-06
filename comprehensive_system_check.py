#!/usr/bin/env python3
"""
OMFATTENDE SYSTEMSJEKK AV SMARTREMINDER
======================================
Tester alle komponenter for å sikre at alt fungerer optimalt
"""

import os
import sys
import json
import requests
import time
from datetime import datetime

def comprehensive_system_check():
    """Kjør en omfattende sjekk av hele systemet"""
    
    print("🔍 OMFATTENDE SMARTREMINDER SYSTEMSJEKK")
    print("=" * 60)
    print(f"📅 Dato: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # 1. STRUKTUR OG FILER
    print("\n1️⃣ STRUKTUR OG FILER")
    print("-" * 30)
    
    # Sjekk kritiske filer
    critical_files = {
        'app.py': 'Hovedapplikasjon',
        'templates/dashboard.html': 'Dashboard template',
        'templates/base.html': 'Base template',
        'static/js/app.js': 'JavaScript hovedfil',
        'static/sw.js': 'Service Worker',
        'static/css/style.css': 'CSS stilfil',
        'static/sounds/pristine.mp3': 'Standard lyd',
        'static/sounds/ding.mp3': 'Ding lyd',
        'static/sounds/chime.mp3': 'Chime lyd',
        'static/sounds/alert.mp3': 'Alert lyd',
        'push_service.py': 'Push notification service'
    }
    
    file_status = {}
    for file_path, description in critical_files.items():
        if os.path.exists(file_path):
            size = os.path.getsize(file_path)
            print(f"✅ {file_path:<35} ({size:,} bytes)")
            file_status[file_path] = True
        else:
            print(f"❌ {file_path:<35} MANGLER!")
            file_status[file_path] = False
    
    # Sjekk data mapper
    print("\n📁 Data mapper:")
    data_files = {
        'data/users.json': 'Brukerdata',
        'data/reminders.json': 'Påminnelser',
        'data/shared_reminders.json': 'Delte påminnelser',
        'data/notifications.json': 'Notifikasjonslogg',
        'data/push_subscriptions.json': 'Push subscriptions'
    }
    
    for file_path, description in data_files.items():
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                size = len(data) if isinstance(data, list) else len(data.keys()) if isinstance(data, dict) else 0
                print(f"✅ {file_path:<35} ({size} items)")
                file_status[file_path] = True
            except Exception as e:
                print(f"⚠️  {file_path:<35} KORRUPT: {e}")
                file_status[file_path] = False
        else:
            print(f"❌ {file_path:<35} MANGLER!")
            file_status[file_path] = False
    
    # 2. PYTHON IMPORTS
    print("\n2️⃣ PYTHON IMPORTS")
    print("-" * 30)
    
    import_status = {}
    imports_to_test = [
        ('app', 'Hovedapp modul'),
        ('push_service', 'Push notification service'),
        ('email_service', 'Email service'),
        ('shared_noteboard', 'Shared noteboard'),
        ('config', 'Konfigurasjon'),
        ('flask', 'Flask framework'),
        ('flask_login', 'Flask-Login'),
        ('flask_mail', 'Flask-Mail')
    ]
    
    for module, description in imports_to_test:
        try:
            __import__(module)
            print(f"✅ {module:<20} {description}")
            import_status[module] = True
        except ImportError as e:
            print(f"⚠️  {module:<20} {description} - {e}")
            import_status[module] = False
        except Exception as e:
            print(f"❌ {module:<20} {description} - Feil: {e}")
            import_status[module] = False
    
    # 3. APP FUNKSJONER
    print("\n3️⃣ APP FUNKSJONER")
    print("-" * 30)
    
    function_status = {}
    try:
        from app import app, dm, check_reminders_for_notifications
        print(f"✅ App objekt tilgjengelig")
        print(f"✅ DataManager tilgjengelig")
        print(f"✅ Notification checker tilgjengelig")
        
        # Test app context
        with app.app_context():
            print(f"✅ App context fungerer")
            
        function_status['app_basic'] = True
    except Exception as e:
        print(f"❌ App grunnfunksjoner: {e}")
        function_status['app_basic'] = False
    
    # 4. NETTVERKSTESTING
    print("\n4️⃣ NETTVERKSTESTING")
    print("-" * 30)
    
    network_status = {}
    
    # Test om appen kjører
    ports_to_test = [5000, 8080, 3000]
    app_port = None
    
    for port in ports_to_test:
        try:
            response = requests.get(f'http://localhost:{port}/health', timeout=2)
            if response.status_code == 200:
                print(f"✅ App kjører på port {port}")
                app_port = port
                network_status['app_running'] = True
                break
        except:
            continue
    
    if not app_port:
        print(f"⚠️  App kjører ikke på noen av portene {ports_to_test}")
        network_status['app_running'] = False
    else:
        # Test spesifikke endpoints
        endpoints_to_test = [
            ('/health', 'Helsesjekk'),
            ('/login', 'Login side'),
            ('/api/calendar-events', 'Kalender API (krever login)')
        ]
        
        for endpoint, description in endpoints_to_test:
            try:
                response = requests.get(f'http://localhost:{app_port}{endpoint}', timeout=2)
                if endpoint == '/api/calendar-events':
                    # Forventer redirect til login
                    if response.status_code in [302, 200] or 'login' in response.text.lower():
                        print(f"✅ {endpoint:<25} {description} - Redirect til login (OK)")
                        network_status[endpoint] = True
                    else:
                        print(f"⚠️  {endpoint:<25} {description} - Uventet respons")
                        network_status[endpoint] = False
                elif response.status_code == 200:
                    print(f"✅ {endpoint:<25} {description}")
                    network_status[endpoint] = True
                else:
                    print(f"⚠️  {endpoint:<25} {description} - Status {response.status_code}")
                    network_status[endpoint] = False
            except Exception as e:
                print(f"❌ {endpoint:<25} {description} - Feil: {e}")
                network_status[endpoint] = False
    
    # 5. JAVASCRIPT OG FRONTEND
    print("\n5️⃣ JAVASCRIPT OG FRONTEND")
    print("-" * 30)
    
    js_status = {}
    
    # Sjekk app.js
    if os.path.exists('static/js/app.js'):
        with open('static/js/app.js', 'r') as f:
            js_content = f.read()
        
        js_features = {
            'PLAY_NOTIFICATION_SOUND': 'Lyd-håndtering fra Service Worker',
            'playNotificationSound': 'Lyd avspilling funksjon',
            'serviceWorker.addEventListener': 'Service Worker lytter',
            'showManualSoundPlayButton': 'Manuell lyd-knapp fallback',
            'initializePushNotifications': 'Push notification initialisering'
        }
        
        for feature, description in js_features.items():
            if feature in js_content:
                print(f"✅ {description}")
                js_status[feature] = True
            else:
                print(f"⚠️  {description} - MANGLER")
                js_status[feature] = False
    else:
        print(f"❌ app.js ikke funnet")
        js_status['app_js'] = False
    
    # Sjekk Service Worker
    if os.path.exists('static/sw.js'):
        with open('static/sw.js', 'r') as f:
            sw_content = f.read()
        
        sw_features = {
            'push': 'Push event handling',
            'sendSoundMessageToClients': 'Lyd melding til klienter',
            'clients.matchAll': 'Klient kommunikasjon',
            'postMessage': 'Message posting'
        }
        
        for feature, description in sw_features.items():
            if feature in sw_content:
                print(f"✅ Service Worker: {description}")
                js_status[f'sw_{feature}'] = True
            else:
                print(f"⚠️  Service Worker: {description} - MANGLER")
                js_status[f'sw_{feature}'] = False
    else:
        print(f"❌ sw.js ikke funnet")
        js_status['sw_js'] = False
    
    # 6. DASHBOARD TEMPLATE
    print("\n6️⃣ DASHBOARD TEMPLATE")
    print("-" * 30)
    
    template_status = {}
    
    if os.path.exists('templates/dashboard.html'):
        with open('templates/dashboard.html', 'r') as f:
            template_content = f.read()
        
        template_features = {
            'id="calendar"': 'Kalender element',
            'FullCalendar.Calendar': 'FullCalendar initialisering',
            'loadCalendarEvents': 'Event loading funksjon',
            'calendar-fallback': 'Fallback UI',
            'checkUserAuthentication': 'Autentisering sjekk',
            'initializeCalendar': 'Kalender initialisering'
        }
        
        for feature, description in template_features.items():
            if feature in template_content:
                print(f"✅ {description}")
                template_status[feature] = True
            else:
                print(f"⚠️  {description} - MANGLER")
                template_status[feature] = False
        
        # Sjekk for problemkode
        problem_patterns = {
            '.then data =>': 'JavaScript syntax feil (mangler parenteser)',
            'duplicate': 'Duplikat kode'
        }
        
        for pattern, description in problem_patterns.items():
            if pattern in template_content:
                print(f"⚠️  PROBLEM: {description}")
                template_status[f'problem_{pattern}'] = True
            else:
                template_status[f'problem_{pattern}'] = False
    else:
        print(f"❌ dashboard.html ikke funnet")
        template_status['dashboard_html'] = False
    
    # 7. OPPSUMMERING
    print("\n7️⃣ SYSTEMSTATUS OPPSUMMERING")
    print("=" * 60)
    
    # Beregn totale score
    total_checks = 0
    passed_checks = 0
    
    for status_dict in [file_status, import_status, function_status, network_status, js_status]:
        for key, value in status_dict.items():
            total_checks += 1
            if value:
                passed_checks += 1
    
    # Template status krever spesiell håndtering for problem patterns
    for key, value in template_status.items():
        total_checks += 1
        if key.startswith('problem_'):
            # For problem patterns: False = bra (ingen problem), True = dårlig (problem funnet)
            if not value:
                passed_checks += 1
        else:
            # For normale features: True = bra, False = dårlig
            if value:
                passed_checks += 1
    
    success_rate = (passed_checks / total_checks * 100) if total_checks > 0 else 0
    
    print(f"📊 TOTAL SCORE: {passed_checks}/{total_checks} ({success_rate:.1f}%)")
    
    if success_rate >= 90:
        print("🎉 UTMERKET! Systemet fungerer svært godt.")
        status_emoji = "🟢"
    elif success_rate >= 75:
        print("✅ BRA! Systemet fungerer godt med mindre problemer.")
        status_emoji = "🟡"
    elif success_rate >= 50:
        print("⚠️  MIDDELS! Systemet har noen problemer som bør fikses.")
        status_emoji = "🟠"
    else:
        print("❌ KRITISK! Systemet har alvorlige problemer.")
        status_emoji = "🔴"
    
    print(f"\n{status_emoji} HOVEDKOMPONENTER:")
    component_scores = {
        'Filer og struktur': file_status,
        'Python imports': import_status,
        'App funksjoner': function_status,
        'Nettverkstest': network_status,
        'JavaScript/Frontend': js_status,
        'Templates': template_status
    }
    
    for component, status_dict in component_scores.items():
        passed = sum(1 for v in status_dict.values() if v)
        total = len(status_dict)
        percentage = (passed / total * 100) if total > 0 else 0
        emoji = "✅" if percentage >= 80 else "⚠️" if percentage >= 50 else "❌"
        print(f"{emoji} {component}: {passed}/{total} ({percentage:.0f}%)")
    
    print(f"\n📋 ANBEFALINGER:")
    
    # Spesifikke anbefalinger basert på resultater
    if not file_status.get('static/sounds/pristine.mp3', True):
        print("🔊 - Installer lydfiler for notifikasjoner")
    
    if not network_status.get('app_running', True):
        print("🚀 - Start applikasjonen")
    
    if not js_status.get('PLAY_NOTIFICATION_SOUND', True):
        print("🔊 - Implementer lyd-håndtering i JavaScript")
    
    if not template_status.get('FullCalendar.Calendar', True):
        print("📅 - Fiks kalender initialisering")
    
    if success_rate == 100:
        print("🎯 - Ingen problemer funnet! Alt ser ut til å fungere perfekt.")
    
    print(f"\n🕐 Test fullført: {datetime.now().strftime('%H:%M:%S')}")
    print("=" * 60)
    
    return success_rate

if __name__ == "__main__":
    try:
        score = comprehensive_system_check()
        sys.exit(0 if score >= 80 else 1)
    except Exception as e:
        print(f"❌ KRITISK FEIL under systemsjekk: {e}")
        sys.exit(2)
