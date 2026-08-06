/**
 * Driving School Mode - Håndterer funksjonalitet for kjøreskole-modus
 * Inkluderer:
 * - Lydvarsler med høy prioritet
 * - Fokusmodusbytte
 * - PWA-støtte (Progressive Web App)
 * - Deling av påminnelser med høy prioritet
 */

// Konstanter for lydvarsler
const NOTIFICATION_SOUNDS = {
    ALERT: '/static/sounds/alert.mp3',
    PRISTINE: '/static/sounds/pristine.mp3',
    DING: '/static/sounds/ding.mp3',
    CHIME: '/static/sounds/chime.mp3'
};

class DrivingSchoolMode {
    constructor() {
        this.focusMode = 'driving_school';
        this.audioContext = null;
        this.initialized = false;
        this.notificationPermission = false;
    }

    async initialize() {
        if (this.initialized) return;

        // Sjekk og be om tillatelser
        await this.requestPermissions();
        
        // Initialiser lydsystem
        this.initAudioSystem();
        
        // Sett opp event listeners
        this.setupEventListeners();
        
        // Sjekk PWA-status
        this.checkPWAStatus();
        
        this.initialized = true;
        console.log('🚗 Kjøreskole-modus initialisert');
    }

    async requestPermissions() {
        // Be om tillatelse til å vise varsler
        if ('Notification' in window) {
            const permission = await Notification.requestPermission();
            this.notificationPermission = permission === 'granted';
        }
    }

    initAudioSystem() {
        // Opprett AudioContext for lydavspilling
        this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
        
        // Forhåndslast lydene
        this.preloadSounds();
    }

    async preloadSounds() {
        try {
            for (const [key, path] of Object.entries(NOTIFICATION_SOUNDS)) {
                const response = await fetch(path);
                const arrayBuffer = await response.arrayBuffer();
                await this.audioContext.decodeAudioData(arrayBuffer);
            }
            console.log('🔊 Lyder lastet');
        } catch (error) {
            console.error('Feil ved lasting av lyder:', error);
        }
    }

    setupEventListeners() {
        // Lytt etter fokusmodus-endringer
        document.addEventListener('focusModeChange', this.handleFocusModeChange.bind(this));
        
        // Lytt etter nye påminnelser
        document.addEventListener('newReminder', this.handleNewReminder.bind(this));
        
        // Lytt etter delte påminnelser
        document.addEventListener('sharedReminder', this.handleSharedReminder.bind(this));
    }

    async handleFocusModeChange(event) {
        const newMode = event.detail.mode;
        
        // Lagre forrige modus
        const previousMode = this.focusMode;
        this.focusMode = newMode;
        
        // Oppdater UI
        this.updateFocusModeUI(newMode);
        
        // Lagre endringen i localStorage
        localStorage.setItem('focusMode', newMode);
        
        // Send til server
        try {
            await fetch('/api/update-focus-mode', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ mode: newMode })
            });
            
            // Spill av bekreftelseslyd
            await this.playNotificationSound(NOTIFICATION_SOUNDS.DING);
            
        } catch (error) {
            console.error('Feil ved oppdatering av fokusmodus:', error);
            // Rull tilbake ved feil
            this.focusMode = previousMode;
            this.updateFocusModeUI(previousMode);
        }
    }

    updateFocusModeUI(mode) {
        // Oppdater aktiv klasse på fokusmodusknapper
        document.querySelectorAll('.focus-mode-btn').forEach(btn => {
            btn.classList.toggle('active', btn.dataset.mode === mode);
        });
    }

    async handleNewReminder(event) {
        const reminder = event.detail;
        
        if (this.focusMode === 'driving_school') {
            // Alltid høy prioritet i kjøreskole-modus
            await this.showHighPriorityNotification(reminder);
        }
    }

    async handleSharedReminder(event) {
        const { reminder, sender } = event.detail;
        
        // Vis høyprioritetsvarsel for delte påminnelser
        await this.showHighPriorityNotification({
            ...reminder,
            title: `Delt av ${sender}: ${reminder.title}`,
            shared: true
        });
    }

    async showHighPriorityNotification(reminder) {
        if (!this.notificationPermission) return;

        // Spill høyprioritetslyd
        await this.playNotificationSound(NOTIFICATION_SOUNDS.ALERT);

        // Vis varsling
        const notification = new Notification(reminder.title, {
            body: reminder.description || 'Ny høyprioritets påminnelse',
            icon: '/static/images/notification-icon-urgent.png',
            badge: '/static/images/badge-icon.png',
            tag: `reminder-${reminder.id}`,
            requireInteraction: true, // Krever interaksjon
            silent: true, // Vi håndterer lyd selv
            vibrate: [200, 100, 200, 100, 200], // Sterkere vibrasjonsmønster
            data: {
                priority: 'high',
                reminderId: reminder.id,
                shared: reminder.shared || false
            }
        });

        // Håndter klikk på varsling
        notification.onclick = () => {
            window.focus();
            if (reminder.url) {
                window.location.href = reminder.url;
            }
        };
    }

    async playNotificationSound(soundUrl) {
        try {
            if (!this.audioContext) {
                this.initAudioSystem();
            }

            const response = await fetch(soundUrl);
            const arrayBuffer = await response.arrayBuffer();
            const audioBuffer = await this.audioContext.decodeAudioData(arrayBuffer);
            
            const source = this.audioContext.createBufferSource();
            source.buffer = audioBuffer;
            source.connect(this.audioContext.destination);
            source.start(0);
            
        } catch (error) {
            console.error('Feil ved avspilling av lyd:', error);
        }
    }

    checkPWAStatus() {
        // Sjekk om appen kjører som PWA
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('📱 Kjører som installert app');
        } else {
            // Vis installer-banner hvis tilgjengelig
            window.addEventListener('beforeinstallprompt', (e) => {
                e.preventDefault();
                const installButton = document.getElementById('install-pwa');
                if (installButton) {
                    installButton.style.display = 'block';
                    installButton.onclick = () => {
                        e.prompt();
                        e.userChoice.then((choiceResult) => {
                            if (choiceResult.outcome === 'accepted') {
                                console.log('📱 Bruker installerte appen');
                                installButton.style.display = 'none';
                            }
                        });
                    };
                }
            });
        }
    }
}

// Initialiser kjøreskole-modus
const drivingSchoolMode = new DrivingSchoolMode();
document.addEventListener('DOMContentLoaded', () => {
    drivingSchoolMode.initialize();
});

// Eksporter for testing
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DrivingSchoolMode, NOTIFICATION_SOUNDS };
}
