from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session, abort, send_from_directory, current_app
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from flask_mail import Mail, Message
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import StringField, TextAreaField, SelectField, DateField, TimeField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, Length
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import json
import os
import logging
import shutil
import re
from pathlib import Path
import hashlib
import uuid

# Norsk tidssone: sørger for at datetime.now() (og dermed når påminnelser fyrer)
# følger Europe/Oslo inkl. sommer/vintertid, uansett hva serveren er satt til.
# Kan overstyres med TZ-miljøvariabel. (time.tzset finnes kun på Unix/Linux.)
os.environ.setdefault('TZ', 'Europe/Oslo')
try:
    import time as _time
    _time.tzset()
except (AttributeError, OSError):
    pass

# Import local modules with fallbacks
try:
    from config import config
except ImportError:
    # Fallback configuration if config.py doesn't exist
    class Config:
        SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
        MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.gmail.com'
        MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
        MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', '1', 'yes']
        MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
        MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
        MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER') or os.environ.get('MAIL_USERNAME')
        REMINDER_CHECK_INTERVAL = int(os.environ.get('REMINDER_CHECK_INTERVAL') or 300)
        NOTIFICATION_ADVANCE_MINUTES = int(os.environ.get('NOTIFICATION_ADVANCE_MINUTES') or 15)
        WTF_CSRF_ENABLED = True
        TESTING = False
        MAIL_SUPPRESS_SEND = False
    
    config = {'development': Config, 'testing': Config, 'production': Config, 'default': Config}

try:
    from focus_modes import FocusModeManager
except ImportError:
    # Fallback if focus_modes module doesn't exist
    class FocusModeManager:
        @staticmethod
        def get_all_modes():
            return {
                'normal': type('obj', (object,), {
                    'name': 'Normal', 
                    'description': 'Standard modus for daglig bruk'
                }),
                'silent': type('obj', (object,), {
                    'name': 'Stillemodus', 
                    'description': 'Reduserte notifikasjoner'
                }),
                'adhd': type('obj', (object,), {
                    'name': 'ADHD-modus',
                    'description': 'Økt fokus og struktur'
                }),
                'elderly': type('obj', (object,), {
                    'name': 'Modus for eldre',
                    'description': 'Forenklet grensesnitt'
                })
            }
        
        @staticmethod
        def get_mode(mode_name):
            modes = FocusModeManager.get_all_modes()
            return modes.get(mode_name, modes['normal'])
        
        @staticmethod
        def apply_mode_to_reminders(reminders, mode_name):
            return reminders
        
        @staticmethod
        def get_mode_settings(mode_name):
            return {}

try:
    from shared_noteboard import NoteboardManager
    print("Successfully imported NoteboardManager from shared_noteboard")
except ImportError as e:
    print(f"Failed to import NoteboardManager: {e}")
    # Fallback if shared_noteboard module doesn't exist
    class NoteboardManager:
        def __init__(self, dm):
            self.dm = dm
        
        def get_user_boards(self, email):
            return []
        
        def create_board(self, title, description, creator_email):
            # Mock board object
            return type('Board', (), {
                'board_id': str(uuid.uuid4()),
                'title': title,
                'description': description,
                'access_code': str(uuid.uuid4())[:8].upper(),
                'members': [creator_email]
            })()
        
        def get_board_by_id(self, board_id):
            return None
        
        def join_board(self, access_code, email):
            return None
        
        def save_board(self, board):
            pass

try:
    from email_service import EmailService
except ImportError:
    # Fallback if email_service module doesn't exist
    class EmailService:
        def __init__(self, mail, dm):
            self.mail = mail
            self.dm = dm
        
        def send_reminder_notification(self, reminder, email):
            subject = f"Påminnelse: {reminder['title']}"
            return send_email(email, subject, 'emails/reminder_notification.html', reminder=reminder)
        
        def send_shared_reminder_notification(self, reminder, shared_by, email):
            subject = f"Delt påminnelse fra {shared_by}: {reminder['title']}"
            return send_email(email, subject, 'emails/shared_reminder.html', reminder=reminder, shared_by=shared_by)
        
        def send_test_email(self, email):
            subject = "Test e-post fra SmartReminder"
            return send_email(email, subject, 'emails/test_email.html', user_email=email)
        
        def get_email_statistics(self):
            email_log = self.dm.load_data('email_log')
            total_sent = len([log for log in email_log if log.get('status') == 'sent'])
            total_failed = len([log for log in email_log if log.get('status') == 'failed'])
            success_rate = (total_sent / len(email_log) * 100) if email_log else 0
            
            return {
                'total_sent': total_sent,
                'total_failed': total_failed,
                'success_rate': round(success_rate, 2),
                'by_template': {},
                'recent_emails': email_log[-10:] if email_log else []
            }

# Mock APScheduler for testing
try:
    from apscheduler.schedulers.background import BackgroundScheduler
    if not os.environ.get('TESTING'):
        scheduler = BackgroundScheduler()
        scheduler.start()
    else:
        # Mock scheduler for testing
        class MockScheduler:
            def add_job(self, **kwargs):
                pass
            def start(self):
                pass
        scheduler = MockScheduler()
except ImportError:
    # Mock scheduler for testing
    class MockScheduler:
        def add_job(self, **kwargs):
            pass
        def start(self):
            pass
    scheduler = MockScheduler()

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App
app = Flask(__name__)

# Configuration
config_name = os.environ.get('FLASK_ENV', 'development')
app.config.from_object(config[config_name])

# 🔒 Advar høylytt hvis SECRET_KEY ikke er satt til noe sikkert i produksjon
if not app.config.get('TESTING') and app.config.get('SECRET_KEY') in (None, '', 'dev-secret-key-change-in-production'):
    logger.warning("⚠️  SECRET_KEY er IKKE satt til en sikker verdi! "
                   "Sett SECRET_KEY som miljøvariabel i Railway, ellers kan sesjoner forfalskes.")

# Custom Jinja2 filters
def nl2br_filter(text):
    """HTML-escape user text first (XSS-safe), then convert newlines to <br>."""
    if text is None:
        return ''
    from markupsafe import Markup, escape
    # Escape any HTML in the user content BEFORE inserting our own <br> tags.
    escaped = str(escape(text))
    result = escaped.replace('\r\n', '<br>').replace('\n', '<br>').replace('\r', '<br>')
    return Markup(result)

def as_datetime_filter(date_string):
    """Convert ISO date string to datetime object"""
    if not date_string:
        return None
    try:
        if isinstance(date_string, datetime):
            return date_string
        if isinstance(date_string, str):
            # Handle different date formats
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S.%f']:
                try:
                    return datetime.strptime(date_string.split('.')[0] if '.' in date_string else date_string, fmt)
                except ValueError:
                    continue
        return date_string
    except Exception as e:
        logger.warning(f"as_datetime filter error: {e}")
        return None

def format_datetime_filter(date_input, format_string='%d.%m.%Y %H:%M'):
    """Combined filter to safely format datetime - handles None and invalid dates"""
    if not date_input:
        return 'Ikke satt'
    
    try:
        # First convert to datetime if needed
        if isinstance(date_input, str):
            # Try to parse string to datetime
            for fmt in ['%Y-%m-%d %H:%M:%S', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M', '%Y-%m-%dT%H:%M:%S.%f']:
                try:
                    date_obj = datetime.strptime(date_input.split('.')[0] if '.' in date_input else date_input, fmt)
                    return date_obj.strftime(format_string)
                except ValueError:
                    continue
            return 'Ugyldig datoformat'
        elif hasattr(date_input, 'strftime'):
            # Already a datetime object
            return date_input.strftime(format_string)
        else:
            return str(date_input)
    except Exception as e:
        logger.warning(f"format_datetime filter error: {e} for input: {date_input}")
        return 'Datefeil'

def strftime_filter(date_obj, format_string='%Y-%m-%d %H:%M'):
    """Format datetime object to string"""
    if not date_obj:
        return 'Ikke satt'
    try:
        if isinstance(date_obj, str):
            # If it's already a string, try to parse it first
            date_obj = as_datetime_filter(date_obj)
            if not date_obj:
                return 'Ugyldig dato'
        if hasattr(date_obj, 'strftime'):
            return date_obj.strftime(format_string)
        return str(date_obj)
    except Exception as e:
        logger.warning(f"strftime filter error: {e} for object: {date_obj}")
        return 'Ugyldig dato'

# Register the filters
app.template_filter('nl2br')(nl2br_filter)
app.jinja_env.filters['nl2br'] = nl2br_filter
app.template_filter('as_datetime')(as_datetime_filter)
app.jinja_env.filters['as_datetime'] = as_datetime_filter
app.template_filter('strftime')(strftime_filter)
app.jinja_env.filters['strftime'] = strftime_filter
app.template_filter('format_datetime')(format_datetime_filter)
app.jinja_env.filters['format_datetime'] = format_datetime_filter

# Add safe url_for function
def safe_url_for(endpoint, **values):
    """Safely generate URL, return # if endpoint doesn't exist"""
    try:
        return url_for(endpoint, **values)
    except Exception:
        return '#'

app.jinja_env.globals['safe_url_for'] = safe_url_for

# Verification prints (for debugging)
print(f"🔧 nl2br filter registered: {'nl2br' in app.jinja_env.filters}")
print(f"🔧 as_datetime filter registered: {'as_datetime' in app.jinja_env.filters}")
print(f"🔧 strftime filter registered: {'strftime' in app.jinja_env.filters}")
print(f"🔧 format_datetime filter registered: {'format_datetime' in app.jinja_env.filters}")

# Extensions
csrf = CSRFProtect(app)
mail = Mail(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Vennligst logg inn for å få tilgang til denne siden.'
login_manager.login_message_category = 'info'

# 🔒 Honor Railway's proxy headers so request.is_secure / secure cookies work correctly
try:
    from werkzeug.middleware.proxy_fix import ProxyFix
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)
except Exception as _proxy_err:
    logger.warning(f"ProxyFix not applied: {_proxy_err}")

# 🔒 Rate limiting for brute-force protection on auth endpoints.
# Degrades gracefully to a no-op if flask-limiter isn't installed, so the app always boots.
try:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address
    app.config.setdefault('RATELIMIT_ENABLED', not app.config.get('TESTING', False))
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=[],
        storage_uri="memory://",
        strategy="fixed-window",
    )
except Exception as _limiter_err:
    logger.warning(f"Flask-Limiter unavailable, rate limiting disabled: {_limiter_err}")

    class _NoopLimiter:
        def limit(self, *args, **kwargs):
            def deco(f):
                return f
            return deco

        def exempt(self, f):
            return f

    limiter = _NoopLimiter()

# 🔒 Security headers on every response
@app.after_request
def set_security_headers(response):
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.setdefault('X-Frame-Options', 'SAMEORIGIN')
    response.headers.setdefault('Referrer-Policy', 'strict-origin-when-cross-origin')
    response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=(), payment=()')
    # CSP allows the CDNs (Bootstrap/Font Awesome) and the inline scripts/styles this app relies on.
    csp = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
        "font-src 'self' https://cdnjs.cloudflare.com data:; "
        "img-src 'self' data: https:; "
        "connect-src 'self'; "
        "manifest-src 'self'; "
        "worker-src 'self'; "
        "frame-ancestors 'self'; "
        "base-uri 'self'; "
        "object-src 'none'; "
        "form-action 'self'"
    )
    response.headers.setdefault('Content-Security-Policy', csp)
    # HSTS is only honored over HTTPS (browsers ignore it on plain HTTP).
    if request.is_secure:
        response.headers.setdefault('Strict-Transport-Security', 'max-age=31536000; includeSubDomains')
    return response

# Friendly 429 for rate-limited requests (JSON for API/fetch endpoints, page otherwise)
@app.errorhandler(429)
def ratelimit_handler(e):
    wants_json = request.path.startswith('/api/') or request.path == '/forgot-password' or request.is_json
    if wants_json:
        return jsonify({'success': False, 'message': 'For mange forsøk. Vent litt og prøv igjen.'}), 429
    return (
        '<!doctype html><html lang="nb-NO"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        '<title>For mange forsøk</title></head>'
        '<body style="font-family:system-ui,sans-serif;max-width:32rem;margin:4rem auto;padding:0 1rem;text-align:center">'
        '<h1>For mange forsøk</h1><p>Du har prøvd for mange ganger. Vent et minutt og prøv igjen.</p>'
        '<p><a href="/login">Tilbake til innlogging</a></p></body></html>',
        429,
    )

# 🔒 Enkel, pålitelig rate limiter i prosessen (appen kjører 1 gunicorn-worker,
# så en modul-lokal teller er deterministisk - i motsetning til Flask-Limiters
# in-memory-lager under --preload, som ikke talte pålitelig).
import time as _rl_time
from collections import defaultdict as _rl_defaultdict, deque as _rl_deque
from functools import wraps as _rl_wraps
_RL_BUCKETS = _rl_defaultdict(_rl_deque)


def rate_limit(max_requests, window_seconds, methods=("POST",)):
    def decorator(fn):
        @_rl_wraps(fn)
        def wrapper(*args, **kwargs):
            if request.method in methods and not app.config.get('TESTING'):
                # Bak Railways proxy er request.remote_addr ustabil; bruk den ekte
                # klient-IP-en (venstre verdi i X-Forwarded-For).
                xff = request.headers.get('X-Forwarded-For', '')
                ip = (xff.split(',')[0].strip() if xff else '') or (request.remote_addr or 'unknown')
                key = f"{ip}:{request.endpoint}"
                now = _rl_time.time()
                dq = _RL_BUCKETS[key]
                while dq and dq[0] <= now - window_seconds:
                    dq.popleft()
                if len(dq) >= max_requests:
                    abort(429)
                dq.append(now)
            return fn(*args, **kwargs)
        return wrapper
    return decorator


# Template context processors
@app.context_processor
def inject_csrf_token():
    """Make CSRF token available in all templates"""
    from flask_wtf.csrf import generate_csrf
    return dict(csrf_token=generate_csrf)

# 📊 Data Manager — samme API (load_data/save_data), to backends:
#   - Postgres (kv-tabell 'app_store') når DATABASE_URL er satt OG USE_DB=true
#   - JSON-filer på Railway Volume ellers (uendret standardoppførsel / rollback)
class DataManager:
    _COLLECTIONS = ['users', 'reminders', 'shared_reminders', 'notifications',
                    'email_log', 'shared_noteboards', 'password_reset_requests', 'push_subscriptions']
    _DICT_COLLECTIONS = {'users', 'password_reset_requests', 'push_subscriptions', 'shared_noteboards'}

    def _default_for(self, name):
        return {} if name in self._DICT_COLLECTIONS else []

    def __init__(self):
        db_url = os.environ.get('DATABASE_URL', '').strip()
        want_db = os.environ.get('USE_DB', '').lower() in ('true', '1', 'yes')
        self.use_db = bool(db_url) and want_db
        self.engine = None

        if self.use_db:
            try:
                from sqlalchemy import create_engine, text as _sqltext
                self._text = _sqltext
                self.engine = create_engine(self._normalize_url(db_url),
                                            pool_pre_ping=True, pool_recycle=300, future=True)
                with self.engine.begin() as c:
                    c.execute(_sqltext(
                        "CREATE TABLE IF NOT EXISTS app_store ("
                        "collection VARCHAR(64) PRIMARY KEY, "
                        "data TEXT NOT NULL, "
                        "updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"))
                logger.info("DataManager: Postgres backend (app_store kv)")
            except Exception as e:
                logger.error(f"DB-init feilet, faller tilbake til JSON-filer: {e}")
                self.use_db = False
                self.engine = None

        if not self.use_db:
            data_dir_env = os.environ.get('DATA_DIR')
            volume_path = os.environ.get('RAILWAY_VOLUME_MOUNT_PATH')
            base = data_dir_env or volume_path or 'data'
            self.data_dir = Path(base)
            self.data_dir.mkdir(parents=True, exist_ok=True)
            logger.info(
                f"DataManager storage: {self.data_dir.resolve()} "
                f"(DATA_DIR={data_dir_env!r}, RAILWAY_VOLUME_MOUNT_PATH={volume_path!r})"
            )

        self._ensure_data_files()
        if self.use_db:
            self._auto_import_from_json()

    @staticmethod
    def _normalize_url(u):
        if u.startswith('postgres://'):
            u = 'postgresql://' + u[len('postgres://'):]
        if u.startswith('postgresql://'):
            u = 'postgresql+psycopg://' + u[len('postgresql://'):]
        return u

    # ---- Postgres-hjelpere ----
    def _db_get(self, name):
        with self.engine.connect() as c:
            row = c.execute(self._text("SELECT data FROM app_store WHERE collection = :k"),
                            {'k': name}).fetchone()
        return json.loads(row[0]) if row else None

    def _db_put(self, name, data):
        payload = json.dumps(data, ensure_ascii=False)
        with self.engine.begin() as c:
            res = c.execute(self._text(
                "UPDATE app_store SET data = :v, updated_at = CURRENT_TIMESTAMP WHERE collection = :k"),
                {'v': payload, 'k': name})
            if res.rowcount == 0:
                c.execute(self._text("INSERT INTO app_store (collection, data) VALUES (:k, :v)"),
                          {'k': name, 'v': payload})

    def _ensure_data_files(self):
        """Sørg for at alle samlinger finnes med tomme defaults."""
        for name in self._COLLECTIONS:
            if self.use_db:
                try:
                    if self._db_get(name) is None:
                        self._db_put(name, self._default_for(name))
                except Exception as e:
                    logger.error(f"ensure ({name}) feilet: {e}")
            else:
                filepath = self.data_dir / f"{name}.json"
                if not filepath.exists():
                    self.save_data(name, self._default_for(name))
                elif name == 'users':
                    # migrer users fra liste -> dict om nødvendig (kun JSON-modus)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        if isinstance(data, list):
                            users_dict = {}
                            for user in data:
                                uid = user.get('id') or user.get('user_id') or str(uuid.uuid4())
                                users_dict[uid] = user
                            self.save_data('users', users_dict)
                    except Exception as e:
                        logger.error(f"Feil ved migrering av users: {e}")

    def _auto_import_from_json(self):
        """Engangs sømløs cutover: hvis DB er tom og JSON finnes på volumet, importer det."""
        try:
            if self._db_get('users'):
                return  # DB har allerede data
            src = Path(os.environ.get('DATA_DIR') or os.environ.get('RAILWAY_VOLUME_MOUNT_PATH') or 'data')
            imported = {}
            for name in self._COLLECTIONS:
                fp = src / f"{name}.json"
                if fp.exists():
                    with open(fp, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    if data:
                        self._db_put(name, data)
                        imported[name] = len(data)
            if imported:
                logger.info(f"Auto-importerte JSON -> Postgres: {imported}")
        except Exception as e:
            logger.error(f"JSON->DB auto-import hoppet over: {e}")

    def load_data(self, filename, default=None):
        """Last inn en samling. Samme retur som før (users -> dict, reminders -> list, ...)."""
        if self.use_db:
            try:
                data = self._db_get(filename)
                if data is None:
                    return default if default is not None else self._default_for(filename)
                if filename == 'users' and isinstance(data, list):
                    users_dict = {}
                    for user in data:
                        uid = user.get('id') or user.get('user_id') or str(uuid.uuid4())
                        users_dict[uid] = user
                    self.save_data('users', users_dict)
                    return users_dict
                return data
            except Exception as e:
                logger.error(f"DB load_data({filename}) feilet: {e}")
                return default if default is not None else self._default_for(filename)

        filepath = self.data_dir / f"{filename}.json"
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if filename == 'users' and isinstance(data, list):
                    users_dict = {}
                    for user in data:
                        uid = user.get('id') or user.get('user_id') or str(uuid.uuid4())
                        users_dict[uid] = user
                    self.save_data('users', users_dict)
                    return users_dict
                return data
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Feil ved lasting av {filename}: {e}")
            if default is not None:
                return default
            return {} if filename == 'users' else []

    def save_data(self, filename, data):
        """Lagre en samling (DB: upsert i app_store; JSON: fil m/backup)."""
        if self.use_db:
            try:
                self._db_put(filename, data)
            except Exception as e:
                logger.error(f"DB save_data({filename}) feilet: {e}")
                raise
            return

        filepath = self.data_dir / f"{filename}.json"
        backup_path = self.data_dir / f"{filename}.backup.json"
        try:
            if filepath.exists():
                shutil.copy2(filepath, backup_path)
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Feil ved lagring av {filename}: {e}")
            if backup_path.exists():
                shutil.copy2(backup_path, filepath)
            raise

# Global data manager
dm = DataManager()

# Initialize services after dm is created
email_service = EmailService(mail, dm)
noteboard_manager = NoteboardManager(dm)

# 📧 E-post funksjoner
def _send_via_brevo_api(to_addr, subject, html, sender):
    """Send via Brevos HTTP API (unngår SMTP-porter som ofte er blokkert i skyen)."""
    import requests
    api_key = os.environ.get('BREVO_API_KEY')
    resp = requests.post(
        'https://api.brevo.com/v3/smtp/email',
        headers={'api-key': api_key, 'content-type': 'application/json', 'accept': 'application/json'},
        json={
            'sender': {'email': sender, 'name': 'SmartReminder Pro'},
            'to': [{'email': to_addr}],
            'subject': subject,
            'htmlContent': html,
        },
        timeout=15,
    )
    if resp.status_code in (200, 201, 202):
        return True, None
    return False, f"Brevo API HTTP {resp.status_code}: {resp.text[:300]}"


def _send_email_now(to_addr, subject, html, sender):
    """Send én e-post synkront. Brevo HTTP API hvis BREVO_API_KEY finnes, ellers
    SMTP med kort timeout (så tilkoblingen aldri henger). Returnerer (ok, error)."""
    if os.environ.get('BREVO_API_KEY'):
        try:
            return _send_via_brevo_api(to_addr, subject, html, sender)
        except Exception as e:
            return False, f"{type(e).__name__}: {e}"
    # SMTP-fallback med timeout så det ikke henger i det uendelige
    import socket
    old_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(20)
    try:
        msg = Message(subject=subject, recipients=[to_addr], html=html, sender=sender)
        mail.send(msg)
        return True, None
    except Exception as e:
        return False, f"{type(e).__name__}: {e}"
    finally:
        socket.setdefaulttimeout(old_timeout)


def _deliver_email(app_obj, to_addr, subject, html, sender):
    """Send e-posten i en bakgrunnstråd (blokkerer aldri HTTP-responsen)."""
    with app_obj.app_context():
        ok, error = _send_email_now(to_addr, subject, html, sender)
        status = 'sent' if ok else 'failed'
        if ok:
            logger.info(f"E-post sendt til {to_addr}: {subject}")
        else:
            logger.error(f"Feil ved sending av e-post til {to_addr}: {error}")
        try:
            email_log = dm.load_data('email_log')
            entry = {'to': to_addr, 'subject': subject, 'sent_at': datetime.now().isoformat(), 'status': status}
            if error:
                entry['error'] = error
            email_log.append(entry)
            dm.save_data('email_log', email_log)
        except Exception as log_err:
            logger.error(f"Kunne ikke logge e-post: {log_err}")


def send_email(to, subject, template, **kwargs):
    """Render i request-konteksten, send asynkront så siden aldri henger."""
    try:
        html = render_template(template, **kwargs)
    except Exception as e:
        logger.error(f"Kunne ikke bygge e-post til {to}: {e}")
        return False
    sender = app.config.get('MAIL_DEFAULT_SENDER')
    recipient = to if isinstance(to, str) else (to[0] if to else '')
    import threading
    threading.Thread(target=_deliver_email, args=(app, recipient, subject, html, sender), daemon=True).start()
    return True

def send_reminder_notification(reminder, recipient_email):
    """Send påminnelse-notifikasjon via e-post"""
    return email_service.send_reminder_notification(reminder, recipient_email)

def send_shared_reminder_notification(reminder, shared_by, recipient_email):
    """Send notifikasjon om delt påminnelse"""
    return email_service.send_shared_reminder_notification(reminder, shared_by, recipient_email)

def check_reminders_for_notifications():
    """Sjekk påminnelser og send notifikasjoner"""
    try:
        # Ensure we run within app context for all operations
        with app.app_context():
            now = datetime.now()
            notification_time = now + timedelta(minutes=app.config['NOTIFICATION_ADVANCE_MINUTES'])
            
            # Sjekk alle påminnelser
            reminders = dm.load_data('reminders', [])
            shared_reminders = dm.load_data('shared_reminders', [])
            notifications = dm.load_data('notifications', [])
            
            # Ensure reminders are lists and contain dictionaries
            if not isinstance(reminders, list):
                reminders = []
            if not isinstance(shared_reminders, list):
                shared_reminders = []
            if not isinstance(notifications, list):
                notifications = []
            
            sent_notifications = set()
            for n in notifications:
                if isinstance(n, dict) and 'reminder_id' in n:
                    sent_notifications.add(n['reminder_id'])
            
            all_reminders = []
            
            # Forbered mine påminnelser
            for reminder in reminders:
                if not isinstance(reminder, dict):
                    continue
                    
                if (reminder.get('completed', False) == False and 
                    reminder.get('id') not in sent_notifications):
                    
                    try:
                        reminder_dt = datetime.fromisoformat(reminder['datetime'].replace(' ', 'T'))
                        if now <= reminder_dt <= notification_time:
                            # Notify the reminder owner
                            user_id = reminder.get('user_id', '')
                            if user_id:
                                all_reminders.append((reminder, user_id))
                    except (ValueError, KeyError, TypeError) as e:
                        logger.error(f"Error processing reminder {reminder}: {e}")
                        continue
            
            # Forbered delte påminnelser
            for reminder in shared_reminders:
                if not isinstance(reminder, dict):
                    continue
                    
                if (reminder.get('completed', False) == False and 
                    reminder.get('id') not in sent_notifications):
                    
                    try:
                        reminder_dt = datetime.fromisoformat(reminder['datetime'].replace(' ', 'T'))
                        if now <= reminder_dt <= notification_time:
                            # For shared reminders, shared_with is a single email string
                            recipient_email = reminder.get('shared_with', '')
                            if recipient_email:
                                all_reminders.append((reminder, recipient_email))
                    except (ValueError, KeyError, TypeError) as e:
                        logger.error(f"Error processing shared reminder {reminder}: {e}")
                        continue
            
            # Send notifikasjoner (within app context)
            for reminder, recipient_email in all_reminders:
                # Extract sound setting from reminder
                sound = reminder.get('sound', 'pristine.mp3')
                
                # Try to send push notification first
                push_sent = False
                try:
                    # Create push subscriptions file if it doesn't exist
                    import os
                    os.makedirs('data', exist_ok=True)
                    if not os.path.exists('data/push_subscriptions.json'):
                        with open('data/push_subscriptions.json', 'w') as f:
                            json.dump({}, f)
                    
                    # Import and use the push service 
                    from push_service import send_reminder_notification as send_push_reminder
                    push_sent = send_push_reminder(
                        recipient_email, 
                        reminder['title'], 
                        reminder['datetime'], 
                        sound=sound,
                        dm=dm
                    )
                    logger.info(f"Push notification {'sent' if push_sent else 'failed'} for {reminder['id']}")
                except Exception as push_err:
                    logger.error(f"Error sending push notification to {recipient_email}: {push_err}")
                    push_sent = False
                    
                # Send email notification as backup (within app context)
                email_sent = False
                try:
                    email_sent = send_reminder_notification(reminder, recipient_email)
                    if email_sent:
                        logger.info(f"Email notification sent to {recipient_email} for reminder {reminder['id']}")
                    else:
                        logger.warning(f"Email notification failed for {recipient_email}")
                except Exception as email_err:
                    logger.error(f"Email service error for {recipient_email}: {email_err}")
                    email_sent = False
                
                # Logg notifikasjon hvis minst en metode fungerte
                if push_sent or email_sent:
                    notifications.append({
                        'reminder_id': reminder['id'],
                        'recipient': recipient_email,
                        'sent_at': now.isoformat(),
                        'type': 'reminder_notification',
                        'push_sent': push_sent,
                        'email_sent': email_sent
                    })
            
            # Lagre oppdaterte notifikasjoner
            if all_reminders:
                dm.save_data('notifications', notifications)
                logger.info(f"Sendt {len(all_reminders)} påminnelse-notifikasjoner")
                
    except Exception as e:
        logger.error(f"Feil ved sjekking av påminnelser: {e}")

# 📝 WTForms
class LoginForm(FlaskForm):
    username = StringField('Brukernavn/E-post', validators=[DataRequired(), Email()])
    password = PasswordField('Passord', validators=[DataRequired()])
    submit = SubmitField('Logg inn')

class RegisterForm(FlaskForm):
    username = StringField('Brukernavn/E-post', validators=[DataRequired(), Email()])
    password = PasswordField('Passord', validators=[DataRequired(), Length(min=8)])
    submit = SubmitField('Registrer deg')

class ReminderForm(FlaskForm):
    title = StringField('Tittel', validators=[DataRequired()])
    description = TextAreaField('Beskrivelse')
    date = DateField('Dato', validators=[DataRequired()], default=datetime.now().date())
    time = TimeField('Tid', validators=[DataRequired()], default=datetime.now().time())
    priority = SelectField('Prioritet', choices=[('Lav', 'Lav'), ('Medium', 'Medium'), ('Høy', 'Høy')])
    category = SelectField('Kategori', choices=[
        ('Jobb', 'Jobb'), ('Privat', 'Privat'), ('Helse', 'Helse'), 
        ('Familie', 'Familie'), ('Annet', 'Annet')
    ])
    sound = SelectField('Lyd', choices=[
        ('pristine.mp3', 'Standard lyd'), 
        ('ding.mp3', 'Ding lyd'),
        ('chime.mp3', 'Chime lyd'),
        ('alert.mp3', 'Alert lyd')
    ], default='pristine.mp3')
    submit = SubmitField('Opprett påminnelse')

# 👤 User Class (forbedret)
class User(UserMixin):
    def __init__(self, user_id, username, email, password_hash=None, focus_mode='normal'):
        self.id = user_id
        self.username = username
        self.email = email
        self.password_hash = password_hash
        self.focus_mode = focus_mode
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @staticmethod
    def get(user_id):
        users = dm.load_data('users')
        # Sikre at users er dict
        if isinstance(users, list):
            users_dict = {}
            for user in users:
                uid = user.get('id') or user.get('user_id') or str(uuid.uuid4())
                users_dict[uid] = user
            users = users_dict
        if user_id in users:
            user_data = users[user_id]
            return User(user_id, user_data['username'], user_data['email'], 
                       user_data.get('password_hash'), user_data.get('focus_mode', 'normal'))
        return None
    
    @staticmethod
    def get_by_email(email):
        users = dm.load_data('users')
        # Sikre at users er dict
        if isinstance(users, list):
            users_dict = {}
            for user in users:
                uid = user.get('id') or user.get('user_id') or str(uuid.uuid4())
                users_dict[uid] = user
            users = users_dict
        target = str(email or '').strip().lower()
        for user_id, user_data in users.items():
            if str(user_data.get('email', '')).strip().lower() == target:
                return User(user_id, user_data['username'], user_data['email'],
                           user_data.get('password_hash'), user_data.get('focus_mode', 'normal'))
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)

# Planlegg automatisk sjekking av påminnelser (only if not testing)
if not os.environ.get('TESTING'):
    scheduler.add_job(
        func=check_reminders_for_notifications,
        trigger="interval",
        seconds=app.config['REMINDER_CHECK_INTERVAL'],
        id='reminder_check'
    )

# 🌐 Routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/health')
def health_check():
    """Health check endpoint (rapporterer også DB-status når Postgres brukes)."""
    result = {
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'version': '1.0.0',
        'storage': 'postgres' if getattr(dm, 'use_db', False) else 'json_volume',
    }
    if getattr(dm, 'use_db', False):
        try:
            with dm.engine.connect() as _c:
                _c.execute(dm._text('SELECT 1'))
            result['database'] = 'connected'
        except Exception as e:
            result['database'] = f'error: {e}'
            result['status'] = 'degraded'
    return jsonify(result)

@app.route('/login', methods=['GET', 'POST'])
@rate_limit(20, 60)
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = User.get_by_email(form.username.data)
        
        if user and user.check_password(form.password.data):
            login_user(user, remember=True)
            next_page = request.args.get('next')
            flash(f'Velkommen tilbake, {user.username}!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Feil e-post eller passord!', 'error')
    
    return render_template('login.html', form=form)

# Åpenbart svake/lekkede passord som avvises ved registrering
COMMON_PASSWORDS = {
    '12345678', '123456789', '1234567890', 'password', 'passord', 'passord1',
    'password1', 'qwertyui', 'qwerty123', 'iloveyou', 'admin123', 'welcome1',
    '11111111', '00000000', 'abc12345', 'letmein1', 'sunshine', 'football',
}


@app.route('/register', methods=['GET', 'POST'])
@rate_limit(10, 60)
def register():
    # Honeypot mot spam-boter: ekte brukere ser aldri dette feltet.
    if request.method == 'POST' and request.form.get('website_hp'):
        logger.info("Registrering blokkert (honeypot utfylt).")
        return redirect(url_for('login'))

    form = RegisterForm()

    if form.validate_on_submit():
        # Avvis åpenbart svake/vanlige passord
        if form.password.data.strip().lower() in COMMON_PASSWORDS:
            flash('Det passordet er for vanlig og utrygt. Velg et sterkere passord.', 'error')
            return render_template('login.html', form=LoginForm(), register_form=form)

        # Sjekk om bruker eksisterer
        if User.get_by_email(form.username.data):
            flash('E-post er allerede registrert!', 'error')
            return render_template('login.html', form=LoginForm(), register_form=form)
        
        # Opprett ny bruker
        user_id = str(uuid.uuid4())
        password_hash = generate_password_hash(form.password.data)
        
        users = dm.load_data('users')
        # Sikre at users er dict
        if not isinstance(users, dict):
            users = {}
        users[user_id] = {
            'username': form.username.data,
            'email': form.username.data,
            'password_hash': password_hash,
            'created': datetime.now().isoformat(),
            'focus_mode': 'normal'  # Sett default fokusmodus
        }
        dm.save_data('users', users)

        # Send velkomstepost (best effort — skal aldri blokkere registrering)
        try:
            dashboard_url = url_for('dashboard', _external=True)
            send_email(
                form.username.data,
                'Velkommen til SmartReminder Pro! 🔔',
                'emails/welcome.html',
                dashboard_url=dashboard_url,
            )
        except Exception as mail_err:
            logger.error(f"Kunne ikke sende velkomstepost til {form.username.data}: {mail_err}")

        # Logg inn bruker
        user = User(user_id, form.username.data, form.username.data, password_hash, 'normal')
        login_user(user, remember=True)
        
        flash(f'Velkommen, {user.username}! Din konto er opprettet.', 'success')
        return redirect(url_for('dashboard'))
    
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Du er nå logget ut.', 'info')
    return redirect(url_for('login'))

# Import password reset functionality
try:
    from password_reset import create_password_reset_request, validate_reset_token, reset_user_password
except ImportError:
    # Fallback functions if password_reset module doesn't exist
    def create_password_reset_request(user_email, dm=None):
        return False
    def validate_reset_token(token, dm=None):
        return None
    def reset_user_password(token, new_password, dm=None):
        return False

@app.route('/forgot-password', methods=['GET', 'POST'])
@csrf.exempt
@rate_limit(6, 60)
def forgot_password():
    """Handle forgot password requests"""
    if request.method == 'POST':
        try:
            data = request.get_json()
            email = data.get('email') if data else request.form.get('email')
            
            if not email:
                return jsonify({'success': False, 'message': 'E-post adresse er påkrevd'}), 400
            
            # Check if user exists (case-insensitive)
            users = dm.load_data('users')
            target = str(email or '').strip().lower()
            user_exists = False
            for user_data in users.values():
                if str(user_data.get('email', '')).strip().lower() == target:
                    user_exists = True
                    break
            
            if not user_exists:
                # Don't reveal that user doesn't exist for security
                return jsonify({'success': True, 'message': 'Hvis e-post adressen eksisterer, vil du motta en tilbakestillingslenke.'})
            
            # Create password reset request and send the link by EMAIL
            reset_token = create_password_reset_request(email, dm)
            if reset_token:
                try:
                    reset_url = url_for('reset_password', token=reset_token, _external=True)
                    send_email(
                        email,
                        'Tilbakestill passordet ditt - SmartReminder Pro',
                        'emails/reset_password_email.html',
                        reset_url=reset_url,
                    )
                except Exception as mail_err:
                    logger.error(f"Kunne ikke sende reset-epost til {email}: {mail_err}")

            # Alltid samme svar (avslør ikke om e-posten finnes)
            return jsonify({'success': True, 'message': 'Hvis e-post adressen eksisterer, vil du motta en tilbakestillingslenke.'})
                
        except Exception as e:
            print(f"Error in forgot password: {e}")
            return jsonify({'success': False, 'message': 'Det oppstod en feil. Prøv igjen senere.'})
    
    # GET request - show forgot password form
    return render_template('forgot_password.html')

@app.route('/reset-password/<token>', methods=['GET', 'POST'])
@rate_limit(15, 60)
def reset_password(token):
    """Handle password reset with token"""
    if request.method == 'POST':
        try:
            new_password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if not new_password or not confirm_password:
                flash('Alle felt er påkrevd', 'error')
                return render_template('reset_password.html', token=token)
            
            if new_password != confirm_password:
                flash('Passordene stemmer ikke overens', 'error')
                return render_template('reset_password.html', token=token)
            
            if len(new_password) < 8:
                flash('Passord må være minst 8 tegn', 'error')
                return render_template('reset_password.html', token=token)
            
            # Reset password
            success = reset_user_password(token, new_password, dm)
            
            if success:
                flash('Passord er tilbakestilt. Du kan nå logge inn med det nye passordet.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Ugyldig eller utløpt tilbakestillingslenke', 'error')
                return render_template('reset_password.html', token=token)
                
        except Exception as e:
            print(f"Error in reset password: {e}")
            flash('Det oppstod en feil. Prøv igjen senere.', 'error')
            return render_template('reset_password.html', token=token)
    
    # GET request - validate token and show reset form
    user_email = validate_reset_token(token, dm)
    if not user_email:
        flash('Ugyldig eller utløpt tilbakestillingslenke', 'error')
        return redirect(url_for('login'))
    
    return render_template('reset_password.html', token=token)

@app.route('/dashboard')
@login_required
def dashboard():
    # Hent data
    reminders = dm.load_data('reminders')
    shared_reminders = dm.load_data('shared_reminders')
    users = dm.load_data('users')
    
    # Opprett form for å legge til påminnelser
    form = ReminderForm()
    
    # Filtrer påminnelser (safely handle missing completed field)
    my_reminders = [r for r in reminders if r.get('user_id') == current_user.email and not r.get('completed', False)]
    shared_with_me = [r for r in shared_reminders if r.get('shared_with') == current_user.email and not r.get('completed', False)]
    
    # Sorter etter dato
    my_reminders.sort(key=lambda x: x['datetime'])
    shared_with_me.sort(key=lambda x: x['datetime'])
    
    # Hent brukerens fokus-modus
    user = User.get_by_email(current_user.email)
    current_focus_mode = user.focus_mode if user else 'normal'
    
    # Beregn statistikk
    completed_reminders = [r for r in reminders if r.get('user_id') == current_user.email and r.get('completed', False)]
    total_reminders = len(my_reminders) + len(completed_reminders)
    
    stats = {
        'total': len(my_reminders),
        'completed': len(completed_reminders),
        'shared_count': len(shared_with_me),
        'completion_rate': (len(completed_reminders) / total_reminders * 100) if total_reminders > 0 else 0
    }
    
    return render_template('dashboard.html', 
                         my_reminders=my_reminders, 
                         shared_with_me=shared_with_me,
                         current_focus_mode=current_focus_mode,
                         stats=stats,
                         simple_view=session.get('simple_view', False),
                         form=form)


@app.route('/toggle-simple-view', methods=['POST'])
@login_required
def toggle_simple_view():
    """Skru 'Enkel visning' av/på (lagres i sesjonen)."""
    session['simple_view'] = not session.get('simple_view', False)
    return redirect(url_for('dashboard'))


@app.route('/personvern')
def personvern():
    """Personvernerklæring (GDPR)."""
    return render_template('personvern.html')


@app.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Slett brukerens konto og tilhørende data (GDPR - retten til sletting)."""
    user_id = current_user.id
    email = str(current_user.email or '').strip().lower()

    # Slett brukeren (både UUID-nøkkel og evt. e-post-nøklede rester)
    users = dm.load_data('users', {})
    if isinstance(users, dict):
        users.pop(user_id, None)
        for k in list(users.keys()):
            u = users.get(k)
            if isinstance(u, dict) and str(u.get('email', '')).strip().lower() == email:
                users.pop(k, None)
        dm.save_data('users', users)

    # Slett brukerens påminnelser
    reminders = dm.load_data('reminders', [])
    if isinstance(reminders, list):
        dm.save_data('reminders', [r for r in reminders
                                   if str(r.get('user_id', '')).strip().lower() != email])

    # Slett delte påminnelser knyttet til brukeren
    shared = dm.load_data('shared_reminders', [])
    if isinstance(shared, list):
        dm.save_data('shared_reminders', [r for r in shared
                                          if str(r.get('shared_with', '')).strip().lower() != email
                                          and str(r.get('shared_by', '')).strip().lower() != email])

    # Slett push-subscriptions
    subs = dm.load_data('push_subscriptions', {})
    if isinstance(subs, dict):
        subs.pop(current_user.email, None)
        subs.pop(email, None)
        dm.save_data('push_subscriptions', subs)

    logout_user()
    flash('Kontoen din og alle tilhørende data er slettet.', 'info')
    return redirect(url_for('login'))


@app.route('/export-my-data')
@login_required
def export_my_data():
    """GDPR art. 20 - last ned alle egne data som JSON (uten passord-hash)."""
    email = str(current_user.email or '').strip().lower()
    users = dm.load_data('users', {})
    me = users.get(current_user.id, {}) if isinstance(users, dict) else {}
    reminders = dm.load_data('reminders', [])
    shared = dm.load_data('shared_reminders', [])
    export = {
        'exported_at': datetime.now().isoformat(),
        'account': {
            'email': me.get('email', current_user.email),
            'username': me.get('username'),
            'created': me.get('created'),
            'focus_mode': me.get('focus_mode'),
        },
        'reminders': [r for r in reminders if str(r.get('user_id', '')).strip().lower() == email],
        'shared_with_me': [r for r in shared if str(r.get('shared_with', '')).strip().lower() == email],
    }
    from flask import Response
    resp = Response(json.dumps(export, ensure_ascii=False, indent=2), mimetype='application/json')
    resp.headers['Content-Disposition'] = 'attachment; filename=smartreminder-mine-data.json'
    return resp


@app.route('/admin/mail-status')
@login_required
def admin_mail_status():
    """Admin-diagnostikk for e-post: config-status + siste feil (ingen hemmeligheter vises)."""
    if current_user.email != 'helene721@gmail.com':
        abort(403)
    log = dm.load_data('email_log') or []
    return jsonify({
        'mail_server': app.config.get('MAIL_SERVER'),
        'mail_port': app.config.get('MAIL_PORT'),
        'mail_use_tls': app.config.get('MAIL_USE_TLS'),
        'mail_username_set': bool(app.config.get('MAIL_USERNAME')),
        'mail_password_set': bool(app.config.get('MAIL_PASSWORD')),
        'mail_default_sender': app.config.get('MAIL_DEFAULT_SENDER'),
        'brevo_api_key_set': bool(os.environ.get('BREVO_API_KEY')),
        'send_method': 'brevo_api' if os.environ.get('BREVO_API_KEY') else 'smtp',
        'storage_backend': 'postgres' if getattr(dm, 'use_db', False) else 'json_volume',
        'recent_email_log': log[-8:] if isinstance(log, list) else [],
    })


@app.route('/admin/mail-test')
@login_required
def admin_mail_test():
    """Send en test-epost SYNKRONT og returner nøyaktig resultat/feil (admin)."""
    if current_user.email != 'helene721@gmail.com':
        abort(403)
    method = 'brevo_api' if os.environ.get('BREVO_API_KEY') else 'smtp'
    html = "<p>Dette er en test-epost fra SmartReminder Pro. Hvis du ser denne, virker e-post. 🎉</p>"
    ok, error = _send_email_now(
        current_user.email,
        "SmartReminder – test-epost",
        html,
        app.config.get('MAIL_DEFAULT_SENDER'),
    )
    return jsonify({
        'ok': ok,
        'method': method,
        'to': current_user.email,
        'message': f'Test-epost sendt til {current_user.email}. Sjekk innboks/spam.' if ok else None,
        'error': error,
    })


@app.route('/admin/db-test')
@login_required
def admin_db_test():
    """Admin-diagnostikk: hvorfor bruker appen ikke Postgres? Viser skjema/host + eksakt feil."""
    if current_user.email != 'helene721@gmail.com':
        abort(403)
    db_url = os.environ.get('DATABASE_URL', '') or ''
    info = {
        'USE_DB': os.environ.get('USE_DB'),
        'DATABASE_URL_set': bool(db_url),
        'DATABASE_URL_scheme': db_url.split('://')[0] if '://' in db_url else None,
        'DATABASE_URL_host': (db_url.split('@')[-1].split('/')[0].split('?')[0] if '@' in db_url else None),
        'current_backend': 'postgres' if getattr(dm, 'use_db', False) else 'json_volume',
    }
    if not db_url:
        info['result'] = 'DATABASE_URL er ikke satt i dette servicet.'
        return jsonify(info)
    try:
        from sqlalchemy import create_engine, text as _t
        eng = create_engine(DataManager._normalize_url(db_url), pool_pre_ping=True)
        with eng.connect() as c:
            c.execute(_t('SELECT 1'))
        info['result'] = 'OK - tilkobling til Postgres fungerer. (Restart servicet så tar backend-et over.)'
    except Exception as e:
        info['result'] = f'FEIL: {type(e).__name__}: {str(e)[:400]}'
    return jsonify(info)


@app.route('/complete_reminder/<reminder_id>', methods=['POST'])
@login_required
def complete_reminder(reminder_id):
    # Sjekk mine påminnelser
    reminders = dm.load_data('reminders')
    for reminder in reminders:
        if reminder['id'] == reminder_id and reminder['user_id'] == current_user.email:
            reminder['completed'] = True
            reminder['completed_at'] = datetime.now().isoformat()
            dm.save_data('reminders', reminders)
            flash('Påminnelse fullført!', 'success')
            return redirect(url_for('dashboard'))
    
    # Sjekk delte påminnelser
    shared_reminders = dm.load_data('shared_reminders')
    for reminder in shared_reminders:
        if reminder['id'] == reminder_id and reminder['shared_with'] == current_user.email:
            reminder['completed'] = True
            reminder['completed_at'] = datetime.now().isoformat()
            dm.save_data('shared_reminders', shared_reminders)
            flash('Delt påminnelse fullført!', 'success')
            return redirect(url_for('dashboard'))
    
    flash('Påminnelse ikke funnet!', 'error')
    return redirect(url_for('dashboard'))

@app.route('/delete_reminder/<reminder_id>', methods=['POST'])
@login_required
def delete_reminder(reminder_id):
    reminders = dm.load_data('reminders')
    original_count = len(reminders)
    
    reminders = [r for r in reminders if not (r['id'] == reminder_id and r['user_id'] == current_user.email)]
    
    if len(reminders) < original_count:
        dm.save_data('reminders', reminders)
        flash('Påminnelse slettet!', 'success')
    else:
        flash('Påminnelse ikke funnet eller tilhører ikke deg!', 'error')
    
    return redirect(url_for('dashboard'))

# Add missing API endpoint
@app.route('/api/reminder-count')
@login_required
def api_reminder_count():
    """API endpoint for reminder counts"""
    try:
        # Add some basic caching to reduce load
        cache_key = f"reminder_count_{current_user.email}"
        
        reminders = dm.load_data('reminders')
        shared_reminders = dm.load_data('shared_reminders')
        
        # Safely handle the case where completed field might not exist
        my_count = len([r for r in reminders if r.get('user_id') == current_user.email and not r.get('completed', False)])
        shared_count = len([r for r in shared_reminders if r.get('shared_with') == current_user.email and not r.get('completed', False)])
        completed_count = len([r for r in reminders if r.get('user_id') == current_user.email and r.get('completed', False)])
        
        result = {
            'my_count': my_count,
            'shared_count': shared_count,
            'completed_count': completed_count,
            'total_count': my_count + shared_count,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify(result)
    except Exception as e:
        logger.error(f"API error in reminder_count for user {current_user.email}: {e}")
        return jsonify({
            'error': 'Failed to get reminder counts',
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/api/update-reminder-datetime', methods=['POST'])
@login_required
def api_update_reminder_datetime():
    """API endpoint for updating reminder date/time via drag & drop"""
    try:
        data = request.get_json()
        reminder_id = data.get('reminder_id')
        new_date = data.get('date')
        new_time = data.get('time')
        
        if not all([reminder_id, new_date, new_time]):
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Update in regular reminders
        reminders = dm.load_data('reminders')
        updated = False
        
        for reminder in reminders:
            if reminder['id'] == reminder_id and reminder['user_id'] == current_user.email:
                reminder['datetime'] = f"{new_date} {new_time}"
                updated = True
                break
        
        if updated:
            dm.save_data('reminders', reminders)
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Reminder not found or access denied'}), 404
            
    except Exception as e:
        logger.error(f"API error updating reminder datetime: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/add_reminder', methods=['POST'])
@login_required
def add_reminder():
    """Handle both form and JSON requests for creating reminders"""
    try:
        logger.info(f"add_reminder called - is_json: {request.is_json}, content_type: {request.content_type}")
        
        # Check if it's a JSON request (from calendar)
        if request.is_json:
            data = request.get_json()
            logger.info(f"JSON data received: {data}")
            
            # Validate required fields
            if not data.get('title') or not data.get('date') or not data.get('time'):
                logger.warning(f"Missing required fields in JSON data: {data}")
                return jsonify({'success': False, 'error': 'Missing required fields'}), 400
            
            # Create reminder from JSON data
            reminder_id = str(uuid.uuid4())
            new_reminder = {
                'id': reminder_id,
                'user_id': current_user.email,
                'title': data.get('title'),
                'description': data.get('description', ''),
                'datetime': f"{data.get('date')} {data.get('time')}",
                'priority': data.get('priority', 'Medium'),
                'category': data.get('category', 'Annet'),
                'sound': data.get('sound', 'pristine.mp3'),  # Add sound parameter
                'completed': False,
                'created': datetime.now().isoformat(),
                'shared_with': []
            }
            
            # Save reminder
            reminders = dm.load_data('reminders')
            reminders.append(new_reminder)
            dm.save_data('reminders', reminders)
            
            return jsonify({'success': True, 'reminder_id': reminder_id})
            
        else:
            # Handle regular form submission (existing functionality)
            form = ReminderForm()
            
            if form.validate_on_submit():
                # Hent deling-data fra request
                share_with = request.form.getlist('share_with')
                
                # Opprett påminnelse
                reminder_id = str(uuid.uuid4())
                new_reminder = {
                    'id': reminder_id,
                    'user_id': current_user.email,
                    'title': form.title.data,
                    'description': form.description.data,
                    'datetime': f"{form.date.data} {form.time.data}",
                    'priority': form.priority.data,
                    'category': form.category.data,
                    'sound': request.form.get('sound', 'pristine.mp3'),
                    'completed': False,
                    'created': datetime.now().isoformat(),
                    'shared_with': share_with
                }
                
                # Lagre påminnelse
                reminders = dm.load_data('reminders')
                reminders.append(new_reminder)
                dm.save_data('reminders', reminders)
                
                # Opprett delte påminnelser og send notifikasjoner
                if share_with:
                    shared_reminders = dm.load_data('shared_reminders')
                    
                    for recipient in share_with:
                        shared_reminder = {
                            'id': str(uuid.uuid4()),
                            'original_id': reminder_id,
                            'shared_by': current_user.email,
                            'shared_with': recipient,
                            'title': form.title.data,
                            'description': form.description.data,
                            'datetime': f"{form.date.data} {form.time.data}",
                            'priority': form.priority.data,
                            'category': form.category.data,
                            'sound': request.form.get('sound', 'pristine.mp3'),
                            'completed': False,
                            'created': datetime.now().isoformat(),
                            'is_shared': True
                        }
                        shared_reminders.append(shared_reminder)
                        
                        # Send e-post notifikasjon om delt påminnelse
                        send_shared_reminder_notification(shared_reminder, current_user.email, recipient)
                    
                    dm.save_data('shared_reminders', shared_reminders)
                    flash(f'Påminnelse "{form.title.data}" opprettet og delt med {len(share_with)} personer!', 'success')
                else:
                    flash(f'Påminnelse "{form.title.data}" opprettet!', 'success')
                    
            else:
                flash('Feil i skjema. Sjekk alle felt.', 'error')
            
            return redirect(url_for('dashboard'))
            
    except Exception as e:
        logger.error(f"Error creating reminder: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        else:
            flash('Feil ved opprettelse av påminnelse', 'error')
            return redirect(url_for('dashboard'))

@app.route('/share_reminder', methods=['POST'])
@login_required
def share_reminder():
    """Handle sharing reminders via email"""
    try:
        reminder_id = request.form.get('reminder_id')
        email_addresses = request.form.get('email_addresses', '')
        personal_message = request.form.get('personal_message', '')
        
        if not reminder_id or not email_addresses:
            flash('Påminnelse ID og e-post adresser er påkrevd', 'error')
            return redirect(url_for('dashboard'))
        
        # Find the reminder to share
        reminders = dm.load_data('reminders')
        reminder_to_share = None
        for reminder in reminders:
            if reminder['id'] == reminder_id and reminder['user_id'] == current_user.email:
                reminder_to_share = reminder
                break
        
        if not reminder_to_share:
            flash('Påminnelse ikke funnet eller du har ikke tilgang', 'error')
            return redirect(url_for('dashboard'))
        
        # Parse email addresses (split by comma, semicolon, or whitespace)
        import re
        emails = re.split(r'[,;\s]+', email_addresses.strip())
        emails = [email.strip() for email in emails if email.strip()]
        
        if not emails:
            flash('Ingen gyldig e-post adresser funnet', 'error')
            return redirect(url_for('dashboard'))
        
        # Validate email addresses
        valid_emails = []
        for email in emails:
            if '@' in email and '.' in email.split('@')[1]:
                valid_emails.append(email)
            else:
                flash(f'Ugyldig e-post adresse: {email}', 'warning')
        
        if not valid_emails:
            flash('Ingen gyldige e-post adresser å sende til', 'error')
            return redirect(url_for('dashboard'))
        
        # Load shared reminders
        shared_reminders = dm.load_data('shared_reminders')
        shared_count = 0
        
        # Create shared reminder entries and send notifications
        for email in valid_emails:
            # Check if already shared with this email
            already_shared = False
            for shared in shared_reminders:
                if (shared['original_id'] == reminder_id and 
                    shared['shared_with'] == email):
                    already_shared = True
                    break
            
            if not already_shared:
                # Create shared reminder entry
                shared_reminder = {
                    'id': str(uuid.uuid4()),
                    'original_id': reminder_id,
                    'user_id': reminder_to_share['user_id'],
                    'shared_by': current_user.email,
                    'shared_with': email,
                    'title': reminder_to_share['title'],
                    'description': reminder_to_share['description'],
                    'datetime': reminder_to_share['datetime'],
                    'priority': reminder_to_share['priority'],
                    'category': reminder_to_share['category'],
                    'completed': False,
                    'shared_date': datetime.now().isoformat(),
                    'personal_message': personal_message
                }
                
                shared_reminders.append(shared_reminder)
                
                # Send notification email
                try:
                    email_sent = send_shared_reminder_notification(
                        reminder_to_share, 
                        current_user.email, 
                        email
                    )
                    if email_sent:
                        shared_count += 1
                    else:
                        flash(f'Kunne ikke sende e-post til {email}', 'warning')
                except Exception as e:
                    logger.error(f"Error sending email to {email}: {e}")
                    flash(f'Feil ved sending av e-post til {email}', 'warning')
            else:
                flash(f'Påminnelse allerede delt med {email}', 'info')
        
        # Save shared reminders
        if shared_count > 0:
            dm.save_data('shared_reminders', shared_reminders)
            flash(f'Påminnelse delt med {shared_count} person(er)', 'success')
        else:
            flash('Ingen nye delinger ble opprettet', 'info')
        
        return redirect(url_for('dashboard'))
        
    except Exception as e:
        logger.error(f"Error sharing reminder: {e}")
        flash('Feil ved deling av påminnelse', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/share-calendar-event', methods=['POST'])
@login_required
def api_share_calendar_event():
    """API endpoint for sharing calendar events via email"""
    try:
        data = request.get_json() if request.is_json else request.form
        
        reminder_id = data.get('reminder_id')
        email_addresses = data.get('email_addresses', '')
        personal_message = data.get('personal_message', '')
        
        if not reminder_id or not email_addresses:
            return jsonify({'success': False, 'error': 'Missing required fields'}), 400
        
        # Parse email addresses
        emails = []
        for email in email_addresses.replace(',', ' ').split():
            email = email.strip()
            if email and '@' in email:
                emails.append(email)
        
        if not emails:
            return jsonify({'success': False, 'error': 'No valid email addresses provided'}), 400
        
        # Find the reminder
        reminders = dm.load_data('reminders')
        reminder = None
        
        for r in reminders:
            if r['id'] == reminder_id and r['user_id'] == current_user.email:
                reminder = r
                break
        
        if not reminder:
            return jsonify({'success': False, 'error': 'Reminder not found or access denied'}), 404
        
        # Send calendar invitation emails
        success_count = 0
        for email in emails:
            try:
                send_calendar_invitation_email(reminder, current_user.email, email, personal_message)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to send calendar invitation to {email}: {e}")
        
        if success_count > 0:
            return jsonify({
                'success': True, 
                'message': f'Kalenderinvitasjon sendt til {success_count} av {len(emails)} mottakere'
            })
        else:
            return jsonify({'success': False, 'error': 'Failed to send any invitations'}), 500
            
    except Exception as e:
        logger.error(f"Error sharing calendar event: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

def send_calendar_invitation_email(reminder, shared_by, recipient_email, personal_message=None):
    """
    Send a calendar invitation (ICS) for a reminder via email.
    """
    from flask_mail import Message
    import pytz
    from email.utils import formataddr
    import base64
    
    # Prepare event details
    event_title = reminder.get('title', 'Påminnelse')
    event_description = reminder.get('description', '')
    event_start = reminder.get('datetime')
    event_end = reminder.get('datetime')
    event_category = reminder.get('category', '')
    event_priority = reminder.get('priority', 'Medium')
    
    # Parse start/end time
    try:
        start_dt = datetime.strptime(event_start, '%Y-%m-%d %H:%M')
        end_dt = start_dt + timedelta(minutes=30)
    except Exception:
        start_dt = datetime.now()
        end_dt = start_dt + timedelta(minutes=30)
    
    # ICS content
    dtstamp = start_dt.strftime('%Y%m%dT%H%M%SZ')
    dtstart = start_dt.strftime('%Y%m%dT%H%M%SZ')
    dtend = end_dt.strftime('%Y%m%dT%H%M%SZ')
    uid = f"{reminder.get('id')}@smartreminder"
    
    ics = f"""BEGIN:VCALENDAR\nVERSION:2.0\nPRODID:-//SmartReminder//EN\nCALSCALE:GREGORIAN\nBEGIN:VEVENT\nUID:{uid}\nDTSTAMP:{dtstamp}\nDTSTART:{dtstart}\nDTEND:{dtend}\nSUMMARY:{event_title}\nDESCRIPTION:{event_description}\nCATEGORIES:{event_category}\nPRIORITY:{'1' if event_priority=='Høy' else '5' if event_priority=='Medium' else '9'}\nEND:VEVENT\nEND:VCALENDAR"""
    
    # Email body
    html_body = render_template(
        'emails/calendar_invitation.html',
        reminder=reminder,
        shared_by=shared_by,
        personal_message=personal_message or ''
    )
    
    msg = Message(
        subject=f"Delt kalenderhendelse: {event_title}",
        recipients=[recipient_email],
        html=html_body
    )
    msg.body = f"{event_title}\n\n{event_description}\n\nTid: {event_start}"
    msg.sender = formataddr(("SmartReminder", current_app.config.get('MAIL_DEFAULT_SENDER', shared_by)))
    
    # Attach ICS
    msg.attach(
        filename="invitasjon.ics",
        content_type="text/calendar; charset=utf-8; method=REQUEST",
        data=ics
    )
    
    mail.send(msg)

# 📝 Noteboard Routes
@app.route('/noteboards')
@login_required
def noteboards():
    """Display all noteboards for the current user"""
    try:
        boards = noteboard_manager.get_user_boards(current_user.email)
        return render_template('noteboards.html', boards=boards)
    except Exception as e:
        logger.error(f"Error loading noteboards: {e}")
        flash('Feil ved lasting av tavler', 'error')
        return redirect(url_for('dashboard'))

@app.route('/create-board', methods=['POST'])
@login_required
def create_board():
    """Create a new noteboard"""
    try:
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        
        if not title:
            flash('Tavletittel er påkrevd', 'error')
            return redirect(url_for('noteboards'))
        
        board = noteboard_manager.create_board(title, description, current_user.email)
        flash(f'Tavle "{title}" opprettet! Tilgangskode: {board.access_code}', 'success')
        return redirect(url_for('view_board', board_id=board.board_id))
        
    except Exception as e:
        logger.error(f"Error creating board: {e}")
        flash('Feil ved opprettelse av tavle', 'error')
        return redirect(url_for('noteboards'))

@app.route('/join-board', methods=['GET', 'POST'])
@login_required
def join_board():
    """Join a noteboard using access code"""
    if request.method == 'GET':
        # Handle join via URL with code parameter
        access_code = request.args.get('code')
        if access_code:
            try:
                board = noteboard_manager.join_board(access_code, current_user.email)
                if board:
                    flash(f'Du har blitt med på tavlen "{board.title}"!', 'success')
                    return redirect(url_for('view_board', board_id=board.board_id))
                else:
                    flash('Ugyldig tilgangskode', 'error')
            except Exception as e:
                logger.error(f"Error joining board: {e}")
                flash('Feil ved tilkobling til tavle', 'error')
        
        return redirect(url_for('noteboards'))
    
    # Handle POST request from form
    try:
        access_code = request.form.get('access_code', '').strip().upper()
        
        if not access_code:
            flash('Tilgangskode er påkrevd', 'error')
            return redirect(url_for('noteboards'))
        
        board = noteboard_manager.join_board(access_code, current_user.email)
        if board:
            flash(f'Du har blitt med på tavlen "{board.title}"!', 'success')
            return redirect(url_for('view_board', board_id=board.board_id))
        else:
            flash('Ugyldig tilgangskode', 'error')
            return redirect(url_for('noteboards'))
            
    except Exception as e:
        logger.error(f"Error joining board: {e}")
        flash('Feil ved tilkobling til tavle', 'error')
        return redirect(url_for('noteboards'))

@app.route('/board/<board_id>')
@app.route('/noteboard/<board_id>')
@login_required 
def view_board(board_id):
    """View a specific noteboard"""
    try:
        board = noteboard_manager.get_board_by_id(board_id)
        
        if not board:
            flash('Tavle ikke funnet', 'error')
            return redirect(url_for('noteboards'))
        
        # Check if user has access to this board
        if current_user.email not in board.members:
            flash('Du har ikke tilgang til denne tavlen', 'error')
            return redirect(url_for('noteboards'))
        
        return render_template('noteboard.html', board=board)
        
    except Exception as e:
        logger.error(f"Error viewing board {board_id}: {e}")
        flash('Feil ved lasting av tavle', 'error')
        return redirect(url_for('noteboards'))

@app.route('/add-note-to-board/<board_id>', methods=['POST'])
@login_required
def add_note_to_board(board_id):
    """Add a note to a noteboard"""
    try:
        board = noteboard_manager.get_board_by_id(board_id)
        
        if not board or current_user.email not in board.members:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Access denied'}), 403
            flash('Du har ikke tilgang til denne tavlen', 'error')
            return redirect(url_for('noteboards'))
        
        if request.is_json:
            # Handle JSON request (from JavaScript)
            data = request.get_json()
            content = data.get('content', '').strip()
            color = data.get('color', 'warning')
            x = data.get('x', 0)
            y = data.get('y', 0)
        else:
            # Handle form request
            content = request.form.get('content', '').strip()
            color = request.form.get('color', 'warning')
            x = 0
            y = 0
        
        if not content:
            if request.is_json:
                return jsonify({'success': False, 'error': 'Content is required'}), 400
            flash('Innhold er påkrevd', 'error')
            flash('Innhold er påkrevd', 'error')
            return redirect(url_for('view_board', board_id=board_id))
        
        # Add note to board
        note = board.add_note(content, current_user.email, color=color)
        if x or y:
            note['position'] = {'x': x, 'y': y}
        
        # Save board
        noteboard_manager.save_board(board)
        
        # Send notification to other board members
        try:
            noteboard_manager.notify_board_update(
                board_id, 
                'Nytt notat lagt til', 
                current_user.email, 
                note_content=content
            )
        except Exception as e:
            logger.error(f"Error sending board update notification: {e}")
        
        if request.is_json:
            return jsonify({'success': True, 'note_id': note['id']})
        else:
            flash('Notat lagt til!', 'success')
            return redirect(url_for('view_board', board_id=board_id))
            
    except Exception as e:
        logger.error(f"Error adding note to board {board_id}: {e}")
        if request.is_json:
            return jsonify({'success': False, 'error': str(e)}), 500
        flash('Feil ved tillegging av notat', 'error')
        return redirect(url_for('view_board', board_id=board_id))

@app.route('/api/update-note-position/<note_id>', methods=['POST'])
@login_required
def api_update_note_position(note_id):
    """Update note position via API"""
    try:
        data = request.get_json()
        x = data.get('x', 0)
        y = data.get('y', 0)
        
        # Find the board containing this note
        boards = noteboard_manager.dm.load_data('shared_noteboards')
        for board_data in boards.values():
            if current_user.email in board_data.get('members', []):
                board = noteboard_manager.get_board_by_id(board_data['board_id'])
                if board:
                    updated_note = board.update_note(note_id, position={'x': x, 'y': y})
                    if updated_note:
                        noteboard_manager.save_board(board)
                        return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Note not found'}), 404
        
    except Exception as e:
        logger.error(f"Error updating note position: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/edit-note/<note_id>', methods=['POST'])
@login_required  
def api_edit_note(note_id):
    """Edit note content via API"""
    try:
        data = request.get_json()
        content = data.get('content', '').strip()
        
        if not content:
            return jsonify({'success': False, 'error': 'Content is required'}), 400
        
        # Find the board containing this note
        boards = noteboard_manager.dm.load_data('shared_noteboards')
        for board_data in boards.values():
            if current_user.email in board_data.get('members', []):
                board = noteboard_manager.get_board_by_id(board_data['board_id'])
                if board:
                    # Check if user can edit this note
                    for note in board.notes:
                        if note['id'] == note_id:
                            if note['author'] == current_user.email or board.created_by == current_user.email:
                                updated_note = board.update_note(note_id, content=content)
                                if updated_note:
                                    noteboard_manager.save_board(board)
                                    
                                    # Send notifications
                                    try:
                                        noteboard_manager.notify_board_update(
                                            board.board_id,
                                            'Notat oppdatert',
                                            current_user.email,
                                            note_content=content
                                        )
                                    except Exception as e:
                                        logger.error(f"Error sending update notification: {e}")
                                    
                                    return jsonify({'success': True})
                            else:
                                return jsonify({'success': False, 'error': 'Permission denied'}), 403
        
        return jsonify({'success': False, 'error': 'Note not found'}), 404
        
    except Exception as e:
        logger.error(f"Error editing note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/delete-note/<note_id>', methods=['DELETE'])
@login_required
def api_delete_note(note_id):
    """Delete note via API"""
    try:
        # Find the board containing this note
        boards = noteboard_manager.dm.load_data('shared_noteboards')
        for board_data in boards.values():
            if current_user.email in board_data.get('members', []):
                board = noteboard_manager.get_board_by_id(board_data['board_id'])
                if board:
                    if board.delete_note(note_id, current_user.email):
                        noteboard_manager.save_board(board)
                        
                        # Send notifications
                        try:
                            noteboard_manager.notify_board_update(
                                board.board_id,
                                'Notat slettet',
                                current_user.email
                            )
                        except Exception as e:
                            logger.error(f"Error sending delete notification: {e}")
                        
                        return jsonify({'success': True})
        
        return jsonify({'success': False, 'error': 'Note not found or permission denied'}), 404
        
    except Exception as e:
        logger.error(f"Error deleting note: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Email settings route
@app.route('/email-settings', methods=['GET', 'POST'])
@login_required
def email_settings():
    """Email settings page - restricted to admin only"""
    # Only allow admin access
    if current_user.email != 'helene721@gmail.com':
        flash('Du har ikke tilgang til denne siden', 'error')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Handle email settings form
        flash('E-postinnstillinger oppdatert!', 'success')
        return redirect(url_for('email_settings'))
    
    # Get email statistics
    email_log = dm.load_data('email_log')
    total_sent = len([e for e in email_log if e.get('status') == 'sent'])
    total_failed = len([e for e in email_log if e.get('status') == 'failed'])
    total_emails = len(email_log)
    success_rate = round((total_sent / total_emails * 100) if total_emails > 0 else 0)
    recent_emails = sorted(email_log, key=lambda x: x.get('timestamp', ''), reverse=True)[:10]
    
    email_stats = {
        'total_sent': total_sent,
        'total_failed': total_failed,
        'success_rate': success_rate,
        'recent_emails': recent_emails
    }
    
    return render_template('email_settings.html', email_stats=email_stats, config=app.config)

@app.route('/test-email', methods=['POST'])
@login_required
def test_email():
    """Send test email - restricted to admin only"""
    # Only allow admin access
    if current_user.email != 'helene721@gmail.com':
        flash('Du har ikke tilgang til denne funksjonen', 'error')
        return redirect(url_for('dashboard'))
        
    try:
        email = request.form.get('email')
        if not email:
            flash('E-post adresse er påkrevd', 'error')
            return redirect(url_for('email_settings'))
        
        # Send test email
        success = email_service.send_test_email(email)
        if success:
            flash(f'Test-e-post sendt til {email}!', 'success')
        else:
            flash('Kunne ikke sende test-e-post', 'error')
            
    except Exception as e:
        logger.error(f"Error sending test email: {e}")
        flash('Feil ved sending av test-e-post', 'error')
    
    return redirect(url_for('email_settings'))

# Service Worker route
@app.route('/sw.js')
def service_worker():
    """Serve service worker from root path"""
    return send_from_directory('.', 'sw.js', mimetype='application/javascript')

# Offline page route
@app.route('/offline')
def offline():
    """Offline page for PWA"""
    return render_template('offline.html')

# --- Manglende notify_delay route for dashboard.html ---
@app.route('/notify_delay', methods=['POST'])
@login_required
def notify_delay():
    """Dummy endpoint for delay notification (brukes av dashboard.html)"""
    # Her kan du implementere logikk for å sende forsinkelsesvarsel hvis ønskelig
    flash('Forsinkelsesvarsel sendt (dummy endpoint)', 'info')
    return redirect(url_for('dashboard'))

# Focus modes route
@app.route('/focus-modes', methods=['GET', 'POST'])
@login_required
def focus_modes():
    """Focus modes page with comprehensive error handling"""
    try:
        logger.info(f"Focus modes route accessed by user: {current_user.email}")
        
        if request.method == 'POST':
            # Handle focus mode update
            focus_mode = request.form.get('focus_mode', 'normal')
            logger.info(f"Updating focus mode to: {focus_mode}")
            
            # Validate focus mode
            valid_modes = ['normal', 'silent', 'adhd', 'elderly', 'work', 'study', 'driving_school']
            if focus_mode not in valid_modes:
                logger.warning(f"Invalid focus mode received: {focus_mode}")
                flash('Ugyldig fokusmodus valgt', 'error')
                return redirect(url_for('focus_modes'))
            
            # Update user's focus mode
            users = dm.load_data('users')
            if not isinstance(users, dict):
                users = {}
            
            logger.debug(f"Loaded users data: {len(users)} users")
            
            # Find user and update focus mode
            user_updated = False
            for user_id, user_data in users.items():
                if user_data.get('email') == current_user.email:
                    user_data['focus_mode'] = focus_mode
                    user_data['focus_mode_updated'] = datetime.now().isoformat()
                    user_updated = True
                    logger.info(f"Focus mode updated for user: {current_user.email}")
                    break
            
            if not user_updated:
                # User not found, create entry
                logger.warning(f"User {current_user.email} not found in users data, creating entry")
                new_user_id = str(uuid.uuid4())
                users[new_user_id] = {
                    'email': current_user.email,
                    'username': current_user.email,
                    'focus_mode': focus_mode,
                    'focus_mode_updated': datetime.now().isoformat(),
                    'created': datetime.now().isoformat()
                }
                user_updated = True
                logger.info(f"Created new user entry for: {current_user.email}")
            
            if user_updated:
                try:
                    dm.save_data('users', users)
                    logger.info("Users data saved successfully")
                    flash(f'Fokusmodus oppdatert til "{focus_mode}"!', 'success')
                except Exception as save_error:
                    logger.error(f"Failed to save users data: {save_error}")
                    flash('Feil ved lagring av fokusmodus', 'error')
            else:
                logger.error("Failed to update user focus mode")
                flash('Kunne ikke oppdatere fokusmodus', 'error')
            
            return redirect(url_for('focus_modes'))
        
        # GET request - show focus modes page
        # Get current user's focus mode
        users = dm.load_data('users')
        if not isinstance(users, dict):
            users = {}
        
        current_focus_mode = 'normal'
        
        for user_id, user_data in users.items():
            if user_data.get('email') == current_user.email:
                current_focus_mode = user_data.get('focus_mode', 'normal')
                break
        
        logger.info(f"Current focus mode for user {current_user.email}: {current_focus_mode}")
        
        # FIXED: Get available focus modes without duplication
        focus_modes_dict = {
            'normal': {
                'name': 'Normal',
                'description': 'Standard modus for daglig bruk'
            },
            'silent': {
                'name': 'Stillemodus', 
                'description': 'Reduserte notifikasjoner, kun høy prioritet'
            },
            'adhd': {
                'name': 'ADHD-modus',
                'description': 'Økt fokus og struktur med ekstra påminnelser'
            },
            'elderly': {
                'name': 'Modus for eldre',
                'description': 'Større tekst og forenklet grensesnitt'
            },
            'work': {
                'name': 'Jobbmodus',
                'description': 'Fokus på jobb-relaterte påminnelser'
            },
            'study': {
                'name': 'Studiemodus',
                'description': 'Optimert for læring og deadlines'
            },
            'driving_school': {
                'name': 'Kjøreskolemodus',
                'description': 'Spesialtilpasset for kjøreskoler og instruktører'
            }
        }
        
        # Ensure the current focus mode exists in available modes
        if current_focus_mode not in focus_modes_dict:
            logger.warning(f"Current focus mode '{current_focus_mode}' not in available modes, defaulting to 'normal'")
            current_focus_mode = 'normal'
        
        logger.info(f"Rendering focus modes page with {len(focus_modes_dict)} modes")
        
        return render_template('focus_modes.html', 
                             current_focus_mode=current_focus_mode,
                             focus_modes=focus_modes_dict)
                             
    except Exception as e:
        logger.error(f"Critical error in focus_modes route: {e}", exc_info=True)
        flash('En intern feil oppstod ved lasting av fokusmoduser. Prøv igjen senere.', 'error')
        return redirect(url_for('dashboard'))

@app.route('/api/calendar-events')
@login_required
def api_calendar_events():
    """API endpoint to get all calendar events for the current user (my + shared)"""
    try:
        # Get all reminders
        all_reminders = dm.load_data('reminders')
        shared_reminders = dm.load_data('shared_reminders')
        
        # Filter for current user's reminders
        my_reminders = [r for r in all_reminders if r.get('user_id') == current_user.email]
        
        # Filter shared reminders that are shared with current user
        shared_with_me = [r for r in shared_reminders if r.get('shared_with') == current_user.email]
        
        events_json = []
        
        # Add my reminders
        for reminder in my_reminders:
            color = '#dc3545' if reminder['priority'] == 'Høy' else '#fd7e14' if reminder['priority'] == 'Medium' else '#198754'
            events_json.append({
                'id': reminder['id'],
                'title': reminder['title'],
                'start': reminder['datetime'],
                'color': color,
                'extendedProps': {
                    'type': 'my',
                    'description': reminder.get('description', ''),
                    'priority': reminder.get('priority', 'Medium'),
                    'category': reminder.get('category', 'Annet')
                }
            })

        # Add shared reminders
        for reminder in shared_with_me:
            color = '#17a2b8'  # Blue color for shared reminders
            events_json.append({
                'id': f"shared_{reminder['id']}",
                'title': f"[Delt] {reminder['title']}",
                'start': reminder['datetime'],
                'color': color,
                'extendedProps': {
                    'type': 'shared',
                    'description': reminder.get('description', ''),
                    'priority': reminder.get('priority', 'Medium'),
                    'category': reminder.get('category', 'Delt'),
                    'shared_by': reminder.get('shared_by', 'Ukjent')
                }
            })
        
        return jsonify(events_json)
        
    except Exception as e:
        logger.error(f"Error loading calendar events: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/send-test-notification', methods=['POST'])
@csrf.exempt
@login_required
def send_test_notification():
    """Send a test push notification to the current user"""
    try:
        logger.info(f"Sending test notification to {current_user.email}...")
        
        # Import push service
        from push_service import send_push_notification
        
        # Send test notification
        success = send_push_notification(
            current_user.email,
            "Test Notification",
            "Dette er en test av push-varsler fra SmartReminder!",
            data={
                'url': '/dashboard',
                'sound': 'pristine.mp3',
                'priority': 'high'
            },
            dm=dm
        )
        
        if success:
            logger.info(f"Test notification sent successfully to {current_user.email}")
            return jsonify({'success': True, 'message': 'Test notification sent successfully!'})
        else:
            logger.warning(f"Test notification failed for {current_user.email}")
            return jsonify({'success': False, 'error': 'Failed to send test notification. Make sure you have enabled push notifications.'})
            
    except Exception as e:
        logger.error(f"Error sending test notification: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# VAPID public key endpoint for push notifications
@app.route('/api/vapid-public-key')
@csrf.exempt
def get_vapid_public_key():
    """Get VAPID public key for push notifications"""
    try:
        from notification_integration import get_vapid_public_key as get_key
        public_key = get_key()
        if public_key:
            return jsonify({'public_key': public_key})
        else:
            return jsonify({'error': 'VAPID public key not available'}), 500
    except ImportError:
        # Return a placeholder if notification system is not available
        return jsonify({'error': 'Push notifications not configured'}), 500
    except Exception as e:
        logger.error(f"Error getting VAPID public key: {e}")
        return jsonify({'error': 'Failed to get VAPID public key'}), 500

@app.route('/api/push-subscription', methods=['POST'])
@login_required
@csrf.exempt
def subscribe_push_notifications():
    """Subscribe user to push notifications"""
    try:
        subscription_data = request.get_json()
        
        if not subscription_data or 'subscription' not in subscription_data:
            return jsonify({'success': False, 'error': 'Invalid subscription data'}), 400
        
        subscription = subscription_data['subscription']
        
        # Store subscription in user data
        subscriptions = dm.load_data('push_subscriptions', {})
        user_email = current_user.email
        
        if user_email not in subscriptions:
            subscriptions[user_email] = []
        
        # Check if subscription already exists
        existing = False
        for sub in subscriptions[user_email]:
            if sub.get('endpoint') == subscription.get('endpoint'):
                existing = True
                break
        
        if not existing:
            subscription['created_at'] = datetime.now().isoformat()
            subscriptions[user_email].append(subscription)
            dm.save_data('push_subscriptions', subscriptions)
            logger.info(f"New push subscription added for {user_email}")
        else:
            logger.info(f"Push subscription already exists for {user_email}")
        
        return jsonify({'success': True, 'message': 'Push notifications enabled'})
        
    except Exception as e:
        logger.error(f"Error subscribing to push notifications: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/set-instructor-status', methods=['POST'])
@login_required
def set_instructor_status():
    status = request.form.get('status')
    users = dm.load_data('users', {})
    # NB: users er nøklet på user_id (UUID), ikke e-post.
    user = users.get(current_user.id, {})
    user['status'] = status
    users[current_user.id] = user
    dm.save_data('users', users)
    # Varsle eier hvis konfigurert
    owner_email = user.get('owner')
    if owner_email and owner_email != current_user.email:
        from notification_integration import send_notification
        send_notification(
            owner_email,
            "Instruktørstatus oppdatert",
            f"{current_user.email} satte status til '{status}'",
            data={"type": "instructor_status", "status": status, "by": current_user.email},
            dm=dm
        )
    flash(f'Status oppdatert til {status}', 'success')
    return redirect(url_for('dashboard'))
@app.route('/send-quick-message', methods=['POST'])
@login_required
def send_quick_message():
    message = request.form.get('template') or request.form.get('message')
    users = dm.load_data('users', {})
    user = users.get(current_user.id, {})
    owner_email = user.get('owner')
    if not message:
        flash('Ingen melding å sende.', 'warning')
        return redirect(url_for('dashboard'))
    if owner_email and owner_email != current_user.email:
        from notification_integration import send_notification
        send_notification(
            owner_email,
            "Hurtigmelding",
            f"{current_user.email}: {message}",
            data={"type": "quick_message", "message": message, "by": current_user.email},
            dm=dm
        )
        flash('Melding sendt!', 'success')
    else:
        flash('Ingen mottaker er konfigurert for hurtigmelding ennå.', 'info')
    return redirect(url_for('dashboard'))
@app.route('/log-lesson', methods=['POST'])
@login_required
def log_lesson():
    note = request.form.get('note')
    # Append to lesson log
    lesson_log = dm.load_data('lesson_log', [])
    lesson_log.append({
        'user': current_user.email,
        'timestamp': datetime.now().strftime('%d.%m.%Y %H:%M'),
        'note': note
    })
    dm.save_data('lesson_log', lesson_log)
    
    # Varsle eier (eller instruktør)
    users = dm.load_data('users', {})
    user = users.get(current_user.id, {})
    owner_email = user.get('owner')
    if owner_email and owner_email != current_user.email:
        from notification_integration import send_notification
        send_notification(
            owner_email,
            "Kjøretime logget",
            f"{current_user.email}: {note}",
            data={"type": "lesson_log", "by": current_user.email, "note": note},
            dm=dm
        )
    flash('Kjøretime logget!', 'success')
    return redirect(url_for('dashboard'))
@app.route('/sound-test')
def sound_test():
    """Test page for sound playback"""
    return render_template('sound_test.html')
@app.route('/sw-test')
def sw_test():
    """Test page for service worker sound playback"""
    return send_from_directory('static', 'sw_sound_test.html')

# Static file routes to fix 404 errors
@app.route('/robots.txt')
def robots_txt():
    """Serve robots.txt file"""
    try:
        return send_from_directory('static', 'robots.txt', mimetype='text/plain')
    except:
        # Fallback with basic robots.txt content
        from flask import Response
        return Response("User-agent: *\nDisallow:", mimetype='text/plain')

@app.route('/favicon.ico')
def favicon():
    """Serve favicon.ico file"""
    try:
        return send_from_directory('static/images', 'favicon.ico', mimetype='image/vnd.microsoft.icon')
    except:
        # Return 404 if favicon not found
        abort(404)

@app.route('/static/sounds/<filename>')
def serve_sounds(filename):
    """Serve sound files with proper headers for audio playback"""
    try:
        # Security check - only allow audio files
        if not (filename.endswith('.mp3') or filename.endswith('.wav')):
            abort(404)
        
        # Check if file exists
        sound_path = Path('static/sounds') / filename
        if not sound_path.exists():
            logger.warning(f"Sound file {filename} not found")
            abort(404)
        
        # Determine MIME type based on actual file content
        if filename.endswith('.mp3'):
            # Check if it's actually a WAV file with .mp3 extension
            with open(sound_path, 'rb') as f:
                header = f.read(4)
                if header == b'RIFF':
                    mimetype = 'audio/wav'
                else:
                    mimetype = 'audio/mpeg'
        else:
            mimetype = 'audio/wav'
            
        response = send_from_directory('static/sounds', filename, mimetype=mimetype)
        # Add headers for better browser compatibility
        response.headers['Accept-Ranges'] = 'bytes'
        response.headers['Cache-Control'] = 'public, max-age=3600'
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        logger.error(f"Error serving sound file {filename}: {e}")
        abort(404)

# Flask app startup
if __name__ == '__main__':
    import os
    
    # Ensure data directory exists
    os.makedirs('data', exist_ok=True)
    os.makedirs('static/sounds', exist_ok=True)
    
    # Get port from environment or use default
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('FLASK_ENV') == 'development'
    
    print(f"🚀 Starting SmartReminder on {host}:{port}")
    print(f"🔧 Debug mode: {debug}")
    print(f"🗄️ Data directory: data/")
    print(f"🔊 Sounds directory: static/sounds/")
    
    # Start Flask app
    app.run(
        host=host,
        port=port,
        debug=debug,
        threaded=True
    )