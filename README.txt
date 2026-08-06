smart_reminder_pwa/
│
├── app.py                          # Hovedapplikasjon
├── config.py                       # Konfigurasjon
├── requirements.txt                # Python-pakker
├── Procfile                        # Railway deployment
├── railway.json                    # Railway konfigurasjon
├── .env.example                    # Miljøvariabler eksempel
├── .gitignore                      # Git ignore
├── README.md                       # Dokumentasjon
│
├── static/                         # Statiske filer
│   ├── css/
│   │   └── style.css              # Hovedstil
│   ├── js/
│   │   ├── app.js                 # Hovedlogikk
│   │   └── sw.js                  # Service Worker
│   ├── images/
│   │   ├── icon-192x192.png       # PWA ikon 192x192
│   │   ├── icon-512x512.png       # PWA ikon 512x512
│   │   ├── apple-touch-icon.png   # Apple ikon
│   │   └── favicon.ico            # Favicon
│   └── manifest.json              # PWA manifest
│
├── templates/                     # HTML-maler
│   ├── base.html                 # Grunnmal
│   ├── login.html                # Innlogging
│   ├── dashboard.html            # Hovedside
│   ├── offline.html              # Offline-side
│   ├── emails/                   # E-post maler
│   │   ├── reminder_notification.html
│   │   └── shared_reminder.html
│   └── errors/                   # Feilsider
│       ├── 404.html
│       ├── 403.html
│       └── 500.html
│
└── data/                         # Data (genereres automatisk)
    ├── reminders.json
    ├── users.json
    ├── shared_reminders.json
    ├── notifications.json
    └── email_log.json



# Installer avhengigheter
pip install -r requirements.txt

# Sett opp miljøvariabler
cp .env.example .env
# Rediger .env med dine e-post-innstillinger

# Kjør app
python app.py

## 🚂 Railway Deployment Instruksjoner:

### 1. Forbered prosjektet:
```bash
# Opprett mappe og filer
mkdir smart_reminder_pwa
cd smart_reminder_pwa

# Lag alle filene over
# (kopier innholdet fra filene jeg har laget)

# Initialiser git
git init
git add .
git commit -m "Initial commit - Smart Reminder PWA"''

# Installer Railway CLI
npm install -g @railway/cli

# Logg inn
railway login

# Opprett prosjekt
railway init

# Sett miljøvariabler
railway variables set SECRET_KEY="din-super-sikre-nokkel-her"
railway variables set MAIL_USERNAME="din.epost@gmail.com"
railway variables set MAIL_PASSWORD="ditt-app-passord"
railway variables set MAIL_SERVER="smtp.gmail.com"
railway variables set FLASK_ENV="production"

# Deploy
railway up


# Push til GitHub
git remote add origin https://github.com/dittbrukernavn/smart-reminder-pwa.git
git push -u origin main

# Gå til railway.app
# 1. Klikk "New Project"
# 2. Velg "Deploy from GitHub repo"
# 3. Velg ditt repository
# 4. Railway vil automatisk detektere Python/Flask


3. Sett miljøvariabler i Railway Dashboard:

Gå til prosjektet på railway.app
Klikk på "Variables" tab
Legg til disse variablene:
SECRET_KEY = your-very-secure-secret-key-here
MAIL_SERVER = smtp.gmail.com
MAIL_PORT = 587
MAIL_USE_TLS = true
MAIL_USERNAME = din.epost@gmail.com
MAIL_PASSWORD = ditt-app-spesifikke-passord
MAIL_DEFAULT_SENDER = Smart Reminder Pro <din.epost@gmail.com>
FLASK_ENV = production
REMINDER_CHECK_INTERVAL = 300
NOTIFICATION_ADVANCE_MINUTES = 15


4. Gmail App-passord oppsett:

Gå til Google Account Security
Aktiver 2-faktor autentisering
Gå til "App passwords"
Generer nytt passord for "Smart Reminder Pro"
Bruk dette passordet som MAIL_PASSWORD

5. Test deployment:
# Få URL fra Railway
railway domain

# Test appen
curl https://your-app-name.railway.app/health