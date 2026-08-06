// Focus Mode Management
class FocusModeManager {
    constructor() {
        this.currentMode = 'normal';
        this.modes = {
            'normal': { name: 'Normal', description: 'Standard innstillinger', sound: 'pristine.mp3' },
            'silent': { name: 'Stillemodus', description: 'Minimizes distractions.', sound: 'silent.mp3' },
            'adhd': { name: 'ADHD-modus', description: 'Increases focus with engaging tasks.', sound: 'alert.mp3' },
            'elderly': { name: 'Modus for eldre', description: 'Simplifies interface for easier use.', sound: 'chime.mp3' },
            'work': { name: 'Jobbmodus', description: 'Fokus på jobb-relaterte påminnelser', sound: 'work.mp3' },
            'study': { name: 'Studiemodus', description: 'Fokus på studier og deadlines', sound: 'study.mp3' },
            'driving_school': { name: 'Kjøreskolemodus', description: 'Spesialtilpasset for kjøreskoler', sound: 'driving.mp3' }
        };
    }

    setFocusMode(modeKey) {
        if (this.modes[modeKey]) {
            this.currentMode = modeKey;
            console.log(`Focus mode set to: ${this.modes[modeKey].name}`);
            
            // Save to localStorage
            localStorage.setItem('focusMode', modeKey);
            
            // Apply mode-specific settings
            this.applyModeSettings(modeKey);
            
            return true;
        } else {
            console.error('Invalid focus mode selected:', modeKey);
            return false;
        }
    }

    getCurrentMode() {
        return this.currentMode;
    }

    getCurrentModeData() {
        return this.modes[this.currentMode];
    }

    applyModeSettings(modeKey) {
        const mode = this.modes[modeKey];
        
        // Apply visual changes based on mode
        document.body.className = document.body.className.replace(/focus-mode-\w+/g, '');
        document.body.classList.add(`focus-mode-${modeKey}`);
        
        // Update notification sound preference
        if (mode.sound) {
            this.setNotificationSound(mode.sound);
        }
    }

    setNotificationSound(soundFile) {
        // Update user preference for notification sound
        fetch('/update-notification-sound', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sound: soundFile })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                console.log('Notification sound updated:', soundFile);
            }
        })
        .catch(error => {
            console.error('Error updating notification sound:', error);
        });
    }

    testNotificationSound(soundFile) {
        try {
            // Mark user interaction for mobile playback
            window.userInteracted = true;
            const file = soundFile || this.getCurrentModeData().sound;
            const audio = new Audio(`/static/sounds/${file}`);
            audio.volume = 0.5;
            audio.play().then(() => {
                showToastNotification('Lyd avspilt! 🎵', 'success');
            }).catch(error => {
                console.error('Kunne ikke spille lyd:', error);
                showToastNotification('Kunne ikke spille lyd: ' + error.message, 'error');
            });
        } catch (error) {
            console.error('Feil ved testing av lyd:', error);
            showToastNotification('Feil ved testing av lyd.', 'error');
        }
    }

    loadSavedMode() {
        const savedMode = localStorage.getItem('focusMode');
        if (savedMode && this.modes[savedMode]) {
            this.setFocusMode(savedMode);
        }
    }
}

// Initialize focus mode manager
const focusModeManager = new FocusModeManager();

// Load saved mode on page load
document.addEventListener('DOMContentLoaded', function() {
    focusModeManager.loadSavedMode();
});

// Export for global use
window.focusModeManager = focusModeManager;
