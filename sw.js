// Service Worker for SmartReminder
const CACHE_NAME = 'smartreminder-v3';
const OFFLINE_URL = '/offline';

// Files to cache
const CACHE_FILES = [
    '/',
    '/dashboard',
    '/static/css/style.css',
    '/static/js/app.js',
    '/static/js/pwa.js',
    '/static/js/notification_client.js',
    '/static/sounds/alert.mp3',
    '/static/sounds/pristine.mp3',
    '/static/sounds/ding.mp3',
    '/static/sounds/chime.mp3',
    '/static/images/icon-192x192.png',
    '/static/images/icon-512x512.png',
    '/static/manifest.json',
    '/offline'
];

// Install Service Worker
self.addEventListener('install', event => {
    console.log('Service Worker installing...');
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caching files...');
                // Cache files individually to handle failures gracefully
                return Promise.allSettled(
                    CACHE_FILES.map(url => {
                        return cache.add(url).catch(error => {
                            console.warn(`Failed to cache ${url}:`, error);
                            return null;
                        });
                    })
                );
            })
            .then(() => {
                console.log('Service Worker installed successfully');
                self.skipWaiting();
            })
    );
});

// Activate new version
self.addEventListener('activate', event => {
    console.log('Service Worker activating...');
    event.waitUntil(
        caches.keys()
            .then(cacheNames => {
                return Promise.all(
                    cacheNames.filter(name => name !== CACHE_NAME)
                        .map(name => {
                            console.log('Deleting old cache:', name);
                            return caches.delete(name);
                        })
                );
            })
            .then(() => {
                console.log('Service Worker activated');
                self.clients.claim();
            })
    );
});

// Handle fetch — real offline support
self.addEventListener('fetch', event => {
    const request = event.request;
    if (request.method !== 'GET') return;              // never cache mutations
    const url = new URL(request.url);
    if (url.origin !== self.location.origin) return;   // only same-origin

    // Navigations (HTML pages): network-first, fall back to cache, then offline page
    if (request.mode === 'navigate') {
        event.respondWith(
            fetch(request)
                .then(resp => {
                    const copy = resp.clone();
                    caches.open(CACHE_NAME).then(c => c.put(request, copy)).catch(() => {});
                    return resp;
                })
                .catch(() => caches.match(request).then(r => r || caches.match(OFFLINE_URL)))
        );
        return;
    }

    // Static assets: cache-first, update cache in the background
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request).then(cached => {
                const network = fetch(request).then(resp => {
                    const copy = resp.clone();
                    caches.open(CACHE_NAME).then(c => c.put(request, copy)).catch(() => {});
                    return resp;
                }).catch(() => cached);
                return cached || network;
            })
        );
        return;
    }

    // Everything else: try network, fall back to cache if offline
    event.respondWith(fetch(request).catch(() => caches.match(request)));
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

    // Show notification and play sound
    event.waitUntil(
        Promise.all([
            self.registration.showNotification(data.title, options),
            playNotificationSound(data.sound || 'pristine.mp3')
        ])
    );
});

// Play notification sound
async function playNotificationSound(soundName) {
    try {
        const soundUrl = `/static/sounds/${soundName}`;
        const audioContext = new (self.AudioContext || self.webkitAudioContext)();
        const response = await fetch(soundUrl);
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
        
        const source = audioContext.createBufferSource();
        source.buffer = audioBuffer;
        source.connect(audioContext.destination);
        source.start(0);
    } catch (error) {
        console.error('Error playing sound:', error);
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
