// Service Worker for SmartReminder
const CACHE_NAME = 'smartreminder-v1';
const OFFLINE_URL = '/offline.html';

// Files to cache
const CACHE_FILES = [
    '/',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/driving_school_mode.js',
    '/static/sounds/alert.mp3',
    '/static/sounds/pristine.mp3',
    '/static/sounds/ding.mp3',
    '/static/sounds/chime.mp3',
    OFFLINE_URL
];

// Install Service Worker
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(CACHE_FILES))
            .then(() => self.skipWaiting())
    );
});

// Activate new version
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.filter(name => name !== CACHE_NAME)
                        .map(name => caches.delete(name))
                );
            })
            .then(() => self.clients.claim())
    );
});

// Handle push notifications
self.addEventListener('push', event => {
    const data = event.data.json();
    
    // Set up notification options
    const options = {
        body: data.body,
        icon: '/static/images/notification-icon.png',
        badge: '/static/images/badge-icon.png',
        tag: data.tag || 'default',
        requireInteraction: data.priority === 'high',
        vibrate: data.priority === 'high' 
            ? [200, 100, 200, 100, 200]  // High priority vibration
            : [100, 50, 100],            // Normal vibration
        data: {
            priority: data.priority || 'normal',
            url: data.url,
            sound: data.sound || 'pristine.mp3'
        }
    };

    // Show notification and play sound using client message passing
    event.waitUntil(
        Promise.all([
            self.registration.showNotification(data.title, options),
            sendSoundMessageToClients(data.sound || 'pristine.mp3')
        ])
    );
});

// Play notification sound by sending message to all clients
async function sendSoundMessageToClients(soundName) {
    try {
        // Get all clients
        const clients = await self.clients.matchAll({
            includeUncontrolled: true,
            type: 'window'
        });
        
        // Check if we have any clients
        if (clients.length > 0) {
            console.log(`Sending PLAY_NOTIFICATION_SOUND message to ${clients.length} clients`);
            
            // Send message to all clients
            clients.forEach(client => {
                client.postMessage({
                    type: 'PLAY_NOTIFICATION_SOUND',
                    sound: soundName
                });
            });
            
            return true;
        } else {
            console.log('No clients available, storing sound for later playback');
            // Since service workers can't directly access localStorage, this is a placeholder.
            // The actual implementation would use IndexedDB, but for testing purposes
            // we'll rely on the app.js checkPendingSounds function.
            return false;
        }
    } catch (error) {
        console.error('Error sending sound message to clients:', error);
        return false;
    }
}

// Handle notification click
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    // Open relevant URL if available
    if (event.notification.data.url) {
        event.waitUntil(
            clients.openWindow(event.notification.data.url)
        );
    }
});
