# SmartReminder Pro 🔔

En moderne progressiv web-app (PWA) for smarte påminnelser med avanserte funksjoner for deling og fokusmoduser.

![SmartReminder Pro](https://img.shields.io/badge/PWA-Ready-blue)
![Python](https://img.shields.io/badge/Python-3.7+-green)
![Flask](https://img.shields.io/badge/Flask-2.3+-lightgrey)

## ✨ Funksjoner

### Kjernefunksjoner
- 📱 **PWA** - Installer som native app på mobil og desktop
- 🔔 **Smart påminnelser** - Opprett og administrer påminnelser
- 👥 **Deling** - Del påminnelser med andre brukere
- 📧 **E-post notifikasjoner** - Automatiske varsler via e-post
- 🔄 **Offline support** - Fungerer uten internettforbindelse

### Avanserte funksjoner
- 🧠 **Fokusmoduser** - Tilpass appen til dine behov
- 📋 **Delte tavler** - Samarbeid på digitale notis-tavler
- 📊 **Statistikk** - Oversikt over fullføringsrate og aktivitet
- 🎨 **Responsiv design** - Optimalisert for alle skjermstørrelser

## 🧠 Fokusmoduser

### Stillemodus
- Reduserte notifikasjoner (kun høy prioritet)
- Stilletimer (22:00-08:00)
- Minimalistisk design

### ADHD-modus
- Ekstra påminnelser og fargekodet prioritering
- Tidstelling og urgency-indikatorer
- Forbedret visuell feedback

### Modus for eldre
- Større tekst og knapper
- Høy kontrast og enkel navigasjon
- Gjentatte notifikasjoner

### Jobbmodus
- Fokus på jobb-relaterte påminnelser
- Skjuler private påminnelser i arbeidstid
- Profesjonelt design

### Studiemodus
- Deadline-fokusert
- Pomodoro-timer integrering
- Fremgangsindikator

## 📋 Delte tavler

- Opprett delte notis-tavler med unik tilgangskode
- Dra-og-slipp funksjonalitet for notiser
- Sanntids samarbeid med andre brukere
- Fargekodede notiser og kategorisering

## 🚀 Kom i gang

### Forutsetninger
- Python 3.7+
- Moderne nettleser med PWA-støtte

### Installasjon

1. **Klon repository**
```bash
git clone https://github.com/GmailHelene/smartreminder.git
cd smartreminder
```

2. **Opprett virtuelt miljø**
```bash
python -m venv venv
source venv/bin/activate  # På Windows: venv\Scripts\activate
```

3. **Installer avhengigheter**
```bash
pip install -r requirements.txt
```

4. **Konfigurer miljøvariabler**
```bash
cp .env.example .env
# Rediger .env med dine innstillinger
```

5. **Start applikasjonen**
```bash
python run_local.py
```

6. **Åpne nettleseren**
```
http://localhost:5000
```

## ⚙️ Konfigurasjon

### E-post innstillinger (.env)
```env
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

### App innstillinger
```env
SECRET_KEY=your-secret-key
REMINDER_CHECK_INTERVAL=300
NOTIFICATION_ADVANCE_MINUTES=15
```

## 🧪 Testing

### Kjør alle tester
```bash
python tests/run_tests.py
```

### Kjør spesifikke tester
```bash
python -m unittest tests.test_app -v
python -m unittest tests.test_comprehensive -v
```

### Generer testdata
```bash
python tests/generate_test_data.py
```

### Manuell testing
```bash
python tests/test_manual.py
```

## 📚 API Dokumentasjon

### Grunnleggende endpoints
- `GET /` - Hovedside (omdirigerer til dashboard)
- `GET /health` - Helse-sjekk
- `POST /login` - Brukerinnlogging
- `POST /register` - Brukerregistrering

### Påminnelser
- `GET /dashboard` - Hovedoversikt
- `POST /add_reminder` - Opprett påminnelse
- `GET /complete_reminder/<id>` - Fullfør påminnelse
- `GET /delete_reminder/<id>` - Slett påminnelse

### Fokusmoduser
- `GET /focus-modes` - Vis tilgjengelige moduser
- `POST /set-focus-mode` - Sett aktiv modus

### Delte tavler
- `GET /noteboards` - Vis alle tavler
- `POST /create-board` - Opprett ny tavle
- `GET /board/<id>` - Vis spesifikk tavle
- `POST /join-board` - Bli med på tavle

## 🏗️ Arkitektur

```
SmartReminder/
├── app.py                 # Hovedapplikasjon
├── config.py             # Konfigurasjon
├── focus_modes.py        # Fokusmoduser
├── shared_noteboard.py   # Delte tavler
├── email_service.py      # E-post tjeneste
├── templates/            # HTML templates
├── static/              # CSS, JS, bilder
├── tests/              # Testfiler
└── data/              # Datalagring (JSON)
```

## 🤝 Bidrag

1. Fork repository
2. Opprett feature branch (`git checkout -b feature/amazing-feature`)
3. Commit endringer (`git commit -m 'Add amazing feature'`)
4. Push til branch (`git push origin feature/amazing-feature`)
5. Åpne Pull Request

## 📄 Lisens

Dette prosjektet er lisensiert under MIT License.

## 📞 Support

- Opprett en [issue](https://github.com/GmailHelene/smartreminder/issues) for bug-rapporter
- Diskusjoner og spørsmål i [Discussions](https://github.com/GmailHelene/smartreminder/discussions)

## 🚀 Deployment

### Lokal utvikling
```bash
python run_local.py
```

### Produksjon med Gunicorn
```bash
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Docker (valgfritt)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["python", "run_local.py"]
```

---

**SmartReminder Pro** - Aldri glem en påminnelse igjen! 🎯