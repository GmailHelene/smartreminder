// Main Application JavaScript
document.addEventListener('DOMContentLoaded', function() {
    // Initialize app features
    initializeApp();
    
    // Form validation
    initializeFormValidation();
    
    // Real-time updates
    initializeRealTimeUpdates();
    
    // PWA features
    initializePWAFeatures();
    
    // Push notifications
    initializePushNotifications();
    
    // Check for pending notification sounds
    checkPendingSounds();
    
    // Set user interaction flag for audio playback on mobile
    document.body.addEventListener('click', function() {
        window.userInteracted = true;
    }, { once: true });
});

// Check if user is authenticated
async function checkUserAuthentication() {
    try {
        const response = await fetch('/api/reminder-count', {
            method: 'GET',
            credentials: 'same-origin',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        if (response.status === 401 || response.status === 403) {
            return false;
        }
        
        if (response.ok) {
            return true;
        }
        
        // If we get here, assume authenticated but there might be other issues
        return true;
    } catch (error) {
        console.error('Error checking authentication:', error);
        // Assume authenticated if we can't check (network issues, etc.)
        return true;
    }
}

function initializeApp() {
    // Auto-focus first input on forms
    const firstInput = document.querySelector('input[type="text"], input[type="email"]');
    if (firstInput) {
        firstInput.focus();
    }
    
    // Update connection status
    updateConnectionStatus();
    
    // Initialize tooltips
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

function initializeFormValidation() {
    // Bootstrap form validation
    const forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function(form) {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });
}

function initializeRealTimeUpdates() {
    // Update reminder counts every 30 seconds
    setInterval(() => {
        fetchReminderCounts();
    }, 30000);
}

// Enhanced PWA features initialization
function initializePWAFeatures() {
    console.log('🚀 Initializing PWA features...');
    
    // Check if app is already installed
    if (window.matchMedia && window.matchMedia('(display-mode: standalone)').matches) {
        console.log('📱 App is running in standalone mode (installed)');
        hideInstallButton();
        return;
    }
    
    // Show install button if PWA can be installed
    if (window.deferredPrompt) {
        console.log('💾 PWA can be installed, showing install button');
        showInstallButton();
    }
    
    // Enhanced notification permission handling
    if ('Notification' in window) {
        console.log('🔔 Notification permission status:', Notification.permission);
        
        if (Notification.permission === 'default') {
            // Don't auto-request on page load, wait for user interaction
            console.log('ℹ️ Notification permission is default, will request on user interaction');
        } else if (Notification.permission === 'granted') {
            console.log('✅ Notification permission already granted');
            initializePushNotifications();
        } else {
            console.log('❌ Notification permission denied');
        }
    } else {
        console.log('❌ Notifications not supported in this browser');
    }
}

// Enhanced push notification initialization
function initializePushNotifications() {
    console.log('🔔 Initializing push notifications...');
    
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.ready.then(function(registration) {
            console.log('✅ Service Worker ready for push notifications');
            
            // Check if user is already subscribed
            return registration.pushManager.getSubscription();
        }).then(function(subscription) {
            if (subscription) {
                console.log('✅ Already subscribed to push notifications');
                // Update server with current subscription
                sendSubscriptionToServer(subscription);
                hidePushButton();
            } else {
                console.log('ℹ️ Not subscribed to push notifications');
                showPushButton();
            }
        }).catch(error => {
            console.error('❌ Error checking push subscription:', error);
        });
    } else {
        console.log('❌ Push notifications not supported');
    }
}

// Show/hide push notification button
function showPushButton() {
    const enableBtn = document.getElementById('enablePushBtn');
    if (enableBtn) {
        enableBtn.style.display = 'inline-block';
        enableBtn.onclick = requestPushPermission;
    }
}

function hidePushButton() {
    const enableBtn = document.getElementById('enablePushBtn');
    if (enableBtn) {
        enableBtn.style.display = 'none';
    }
}

// Enhanced push permission request
function requestPushPermission() {
    console.log('🔔 User requesting push notification permission');
    
    if (!('Notification' in window)) {
        showToastNotification('Varslinger støttes ikke av denne nettleseren', 'info');
        return;
    }
    
    if (Notification.permission === 'denied') {
        // Show helpful instructions for enabling notifications
        const helpText = `
            <div style="text-align: left; font-size: 0.9em;">
                <p><strong>💡 Slik aktiverer du varslinger (helt valgfritt):</strong></p>
                <p><strong>Chrome/Edge:</strong> Klikk på låsikonet 🔒 ved adresselinjen → Tillat notifikasjoner</p>
                <p><strong>Firefox:</strong> Klikk på skjoldikonet 🛡️ → Tillat notifikasjoner</p>
                <p><strong>Safari:</strong> Safari → Innstillinger → Nettsteder → Notifikasjoner</p>
                <p><strong>Mobil:</strong> Innstillinger → Nettleser → Nettsteder → Tillatelser</p>
                <br>
                <p><em>✨ Husk: Varslinger er kun for push-meldinger til mobilen. Appen fungerer perfekt uten dem!</em></p>
            </div>
        `;
        
        // Show a helpful modal with instructions
        showNotificationHelpModal(helpText);
        return;
    }
    
    // Request permission
    Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            console.log('✅ Notification permission granted');
            showToastNotification('Varslinger aktivert! 🎉', 'success');
            initializePushNotifications();
        } else {
            console.log('❌ Notification permission denied');
            showToastNotification('Varslinger ikke aktivert - appen fungerer normalt uten dem! 👍', 'info');
        }
    }).catch(error => {
        console.error('Error requesting notification permission:', error);
        showToastNotification('Feil ved aktivering av varslinger', 'error');
    });
}

// Show notification help modal
function showNotificationHelpModal(content) {
    const modal = document.createElement('div');
    modal.className = 'modal fade show';
    modal.style.display = 'block';
    modal.style.backgroundColor = 'rgba(0,0,0,0.5)';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">🔔 Varslinger er blokkert</h5>
                    <button type="button" class="btn-close" onclick="this.closest('.modal').remove()"></button>
                </div>
                <div class="modal-body">
                    ${content}
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="this.closest('.modal').remove()">OK</button>
                </div>
            </div>
        </div>
    `;
    document.body.appendChild(modal);
    
    // Auto-remove after 15 seconds
    setTimeout(() => {
        if (modal.parentNode) {
            modal.remove();
        }
    }, 15000);
}

// Subscribe to push notifications
function subscribeToPushNotifications() {
    if ('serviceWorker' in navigator && 'PushManager' in window) {
        navigator.serviceWorker.ready.then(function(registration) {
            console.log('� Subscribing to push notifications...');
            
            return registration.pushManager.subscribe({
                userVisibleOnly: true,
                applicationServerKey: urlBase64ToUint8Array('YOUR_VAPID_PUBLIC_KEY') // Replace with actual key
function requestNotificationPermissionWithFallback() {
    if (!('Notification' in window)) {
        console.log('This browser does not support notifications');
        showToastNotification('Varslinger støttes ikke av denne nettleseren', 'warning');
        return Promise.resolve('denied');
    }
    
    if (Notification.permission === 'granted') {
        return Promise.resolve('granted');
    }
    
    if (Notification.permission === 'denied') {
        showToastNotification('📱 Varslinger er valgfritt - appen fungerer uten dem også!', 'info', 5000);
        return Promise.resolve('denied');
    }
    
    // Request permission
    return Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
            showToastNotification('Varslinger aktivert! 🔔', 'success');
            // Try to initialize push notifications
            if ('serviceWorker' in navigator && 'PushManager' in window) {
                initializePushNotifications();
            }
        } else {
            showToastNotification('💡 Appen fungerer perfekt uten varslinger også!', 'info');
        }
        return permission;
    });
}

// Board notifications
function notifyBoardUpdate(boardId, updateType, noteContent, sound = 'pristine.mp3') {
    if ('Notification' in window && Notification.permission === 'granted') {
        // Create notification
        new Notification('Tavle oppdatert', {
            body: `${updateType}: ${noteContent?.substring(0, 50)}...`,
            icon: '/static/icon-192x192.png',
            tag: `board-${boardId}`,
            sound: sound,
            silent: false
        });
        
        // Play sound separately (because browser notification sound support is limited)
        playNotificationSound(sound);
    }
}

// Enhanced mobile-specific notification sound handling
function playNotificationSound(sound) {
    try {
        console.log(`🔊 Attempting to play notification sound: ${sound}`);
        const soundFile = sound || 'pristine.mp3';
        const audio = new Audio(`/static/sounds/${soundFile}`);
        audio.volume = 0.8;
        
        // Enhanced mobile device detection
        const isMobile = /Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        
        if (isMobile) {
            console.log('📱 Mobile device detected, using enhanced mobile sound handling');
            
            // Check if user has interacted with the page
            if (window.userInteracted) {
                console.log('✅ User has interacted, attempting direct play');
                const playPromise = audio.play();
                
                if (playPromise !== undefined) {
                    playPromise.then(() => {
                        console.log('✅ Mobile sound played successfully');
                        showToastNotification('Lyd avspilt! 🎵', 'success');
                        // Add haptic feedback if available
                        if ('vibrate' in navigator) {
                            navigator.vibrate([100, 50, 100]);
                        }
                    }).catch(error => {
                        console.log('❌ Mobile autoplay failed, showing manual play button');
                        showMobileNotificationButton(soundFile);
                    });
                }
            } else {
                console.log('⚠️ No user interaction detected, showing mobile notification button');
                showMobileNotificationButton(soundFile);
            }
        } else {
            // Desktop handling - more straightforward
            console.log('🖥️ Desktop device detected');
            const playPromise = audio.play();
            
            if (playPromise !== undefined) {
                playPromise.then(() => {
                    console.log('✅ Desktop sound played successfully');
                }).catch(error => {
                    console.error('❌ Desktop sound play failed:', error);
                    showDesktopNotificationFallback(soundFile);
                });
            }
        }
    } catch (error) {
        console.error('💥 Failed to create audio element:', error);
        showNotificationFallback(sound);
    }
}

// Enhanced mobile-optimized notification button
function showMobileNotificationButton(soundFile) {
    // Remove any existing button
    const existingBtn = document.getElementById('mobileNotificationBtn');
    if (existingBtn) existingBtn.remove();
    
    // Create mobile-optimized button with better styling
    const button = document.createElement('button');
    button.id = 'mobileNotificationBtn';
    button.className = 'btn btn-warning position-fixed';
    button.style.cssText = `
        bottom: 20px;
        left: 50%;
        transform: translateX(-50%);
        z-index: 9999;
        padding: 15px 25px;
        font-size: 18px;
        font-weight: bold;
        border-radius: 30px;
        box-shadow: 0 8px 25px rgba(0,0,0,0.3);
        min-width: 280px;
        max-width: 90vw;
        text-align: center;
        animation: pulseGlow 2s infinite;
        border: 2px solid #ffc107;
        background: linear-gradient(45deg, #ffc107, #ff8c00);
        color: white;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    `;
    
    button.innerHTML = `
        <i class="fas fa-volume-up me-2"></i>
        🔔 Ny påminnelse - Trykk for lyd
        <br><small>Tap to play notification sound</small>
    `;
    
    button.onclick = function() {
        console.log('📱 Mobile user tapped notification button');
        const audio = new Audio(`/static/sounds/${soundFile}`);
        audio.volume = 0.9;
        
        // Set user interaction flag
        window.userInteracted = true;
        
        audio.play().then(() => {
            console.log('✅ Manual sound playback successful');
            this.style.background = 'linear-gradient(45deg, #28a745, #20c997)';
            this.innerHTML = `
                <i class="fas fa-check-circle me-2"></i>
                Lyd avspilt! 🎵
            `;
            
            // Vibrate if available
            if ('vibrate' in navigator) {
                navigator.vibrate([200, 100, 200]);
            }
            
            // Auto-remove after success
            setTimeout(() => {
                this.remove();
            }, 2000);
        }).catch(error => {
            console.error('❌ Manual sound playback failed:', error);
            this.style.background = 'linear-gradient(45deg, #dc3545, #c82333)';
            this.innerHTML = `
                <i class="fas fa-exclamation-triangle me-2"></i>
                Lyd feilet
            `;
        });
    };
    
    document.body.appendChild(button);
    
    // Add enhanced CSS animation
    const style = document.createElement('style');
    style.id = 'mobileNotificationStyle';
    style.textContent = `
        @keyframes pulseGlow {
            0% { 
                transform: translateX(-50%) scale(1);
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }
            50% { 
                transform: translateX(-50%) scale(1.05);
                box-shadow: 0 12px 35px rgba(255,193,7,0.4);
            }
            100% { 
                transform: translateX(-50%) scale(1);
                box-shadow: 0 8px 25px rgba(0,0,0,0.3);
            }
        }
        
        #mobileNotificationBtn:hover {
            background: linear-gradient(45deg, #e0a800, #e07600) !important;
            transform: translateX(-50%) scale(1.02);
        }
        
        #mobileNotificationBtn:active {
            transform: translateX(-50%) scale(0.98);
        }
    `;
    
    // Remove existing style if present
    const existingStyle = document.getElementById('mobileNotificationStyle');
    if (existingStyle) existingStyle.remove();
    
    document.head.appendChild(style);
    
    // Auto-remove after 60 seconds
    setTimeout(() => {
        if (button.parentNode) {
            button.style.animation = 'fadeOut 0.5s ease-out';
            setTimeout(() => button.remove(), 500);
        }
    }, 60000);
    
    // Enhanced vibration pattern to get attention
    if ('vibrate' in navigator) {
        navigator.vibrate([300, 100, 300, 100, 300]);
    }
    
    // Show toast notification as backup
    showToastNotification('🔔 Ny påminnelse mottatt! Trykk på knappen for å spille lyd.', 'warning', 5000);
}

// Desktop notification fallback
function showDesktopNotificationFallback(soundFile) {
    const button = document.createElement('button');
    button.className = 'btn btn-outline-warning position-fixed';
    button.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        padding: 10px 15px;
        border-radius: 20px;
    `;
    
    button.innerHTML = '<i class="fas fa-volume-up me-2"></i>Spill lyd';
    
    button.onclick = function() {
        const audio = new Audio(`/static/sounds/${soundFile}`);
        audio.play();
        this.remove();
    };
    
    document.body.appendChild(button);
    
    setTimeout(() => {
        if (button.parentNode) {
            button.remove();
        }
    }, 15000);
}

// General notification fallback
function showNotificationFallback(soundFile) {
    showToastNotification(`⏰ Ny påminnelse! (Lyd: ${soundFile})`, 'warning', 8000);
    
    // Vibrate if available
    if ('vibrate' in navigator) {
        navigator.vibrate([200, 100, 200, 100, 200]);
    }
}

// Check for any pending notification sounds
function checkPendingSounds() {
  if ('caches' in window) {
    caches.open('sound-notifications').then(cache => {
      cache.match('/pending-sounds').then(response => {
        if (response) {
          response.json().then(data => {
            // Check if the sound notification is recent (last 5 minutes)
            const now = Date.now();
            const fiveMinutesAgo = now - (5 * 60 * 1000);
            
            if (data.timestamp > fiveMinutesAgo) {
              console.log('Found pending sound notification:', data);
              playNotificationSound(data.sound);
            }
            
            // Clear the pending sound
            cache.delete('/pending-sounds');
          });
        }
      });
    });
  }
}

// Check for pending sounds on load
window.addEventListener('load', () => {
  setTimeout(checkPendingSounds, 1000);
});

// Enhanced Service Worker message handling
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', function(event) {
    console.log('📨 Received message from Service Worker:', event.data);
    
    if (event.data && event.data.type === 'PLAY_NOTIFICATION_SOUND') {
      console.log('🎵 Playing notification sound from service worker message:', event.data.sound);
      
      // Play the sound
      playNotificationSound(event.data.sound);
      
      // Show visual notification for mobile
      if (/Android|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent)) {
        showToastNotification('🔔 Ny påminnelse mottatt!', 'info', 4000);
        
        // Vibration feedback
        if ('vibrate' in navigator) {
          navigator.vibrate([200, 100, 200, 100, 200]);
        }
      }
      
      // Track notification attempt
      localStorage.setItem('last_notification_attempt', JSON.stringify({
        timestamp: Date.now(),
        sound: event.data.sound,
        fromServiceWorker: true
      }));
    }
  });
  
  // Enhanced Service Worker ready handling
  navigator.serviceWorker.ready.then(registration => {
    console.log('✅ Service Worker ready, registering client');
    
    if (registration.active) {
      // Tell service worker this client is ready
      registration.active.postMessage({
        type: 'CLIENT_READY',
        timestamp: Date.now()
      });
    }
    
    // Set up message channel for bidirectional communication
    const channel = new MessageChannel();
    channel.port1.onmessage = function(event) {
      console.log('📨 Received message via channel:', event.data);
      
      if (event.data && event.data.type === 'PLAY_NOTIFICATION_SOUND') {
        playNotificationSound(event.data.sound);
      }
    };
    
    // Send the port to service worker
    if (registration.active) {
      registration.active.postMessage({
        type: 'CLIENT_READY',
        port: channel.port2
      }, [channel.port2]);
    }
  });
}

// Connection status
function updateConnectionStatus() {
    const statusElement = document.getElementById('connectionStatus');
    if (statusElement) {
        if (navigator.onLine) {
            statusElement.innerHTML = '<i class="fas fa-wifi"></i> Online';
            statusElement.className = 'badge bg-success';
        } else {
            statusElement.innerHTML = '<i class="fas fa-wifi-slash"></i> Offline';
            statusElement.className = 'badge bg-warning';
        }
    }
}

// Reminder counts
function updateReminderCounts(data) {
    if (!data) {
        console.warn('No data provided to updateReminderCounts');
        return;
    }
    
    try {
        // Update counts in UI
        const myCount = document.getElementById('my-count');
        const sharedCount = document.getElementById('shared-count');
        const completedCount = document.getElementById('completed-count');
        const totalCount = document.getElementById('total-count');
        
        if (myCount) myCount.textContent = data.my_count || 0;
        if (sharedCount) sharedCount.textContent = data.shared_count || 0;
        if (completedCount) completedCount.textContent = data.completed_count || 0;
        if (totalCount) totalCount.textContent = data.total_count || 0;
        
        console.log('📊 Reminder counts updated:', data);
    } catch (error) {
        console.error('Error updating reminder counts:', error);
    }
}

// Fetch reminder counts from API
function fetchReminderCounts() {
    return fetch('/api/reminder-count', {
        method: 'GET',
        credentials: 'same-origin',
        headers: {
            'Content-Type': 'application/json',
        }
    })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            updateReminderCounts(data);
            return data;
        })
        .catch(error => {
            console.warn('Failed to fetch reminder counts:', error);
            // Return empty data so UI doesn't break
            return {
                my_count: 0,
                shared_count: 0,
                completed_count: 0,
                total_count: 0
            };
        });
}

// PWA Installation handled in pwa.js
// No duplicate deferredPrompt declarations or handlers

// Service Worker registrering
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => {
    // Wait a bit for other service worker registrations to complete
    setTimeout(() => {
      navigator.serviceWorker.register('/sw.js', { scope: '/' })
        .then((registration) => {
          console.log('Service Worker registrert:', registration.scope);
        })
        .catch((err) => {
          console.log('Service Worker registrering feilet:', err);
        });
    }, 1000);
  });
}

// Notification permission
function requestNotificationPermission() {
  if ('Notification' in window && 'serviceWorker' in navigator) {
    if (Notification.permission === 'default') {
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          console.log('Notification tillatelse gitt');
        }
      });
    }
  }
}

// Online/offline status
window.addEventListener('online', () => {
  console.log('Tilbake online');
  document.body.classList.remove('offline');
  showNotification('Tilbake online!', 'success');
});

window.addEventListener('offline', () => {
  console.log('Offline');
  document.body.classList.add('offline');
  showNotification('Du er offline. Noen funksjoner kan være begrenset.', 'warning');
});

// Local notifications
function showNotification(message, type = 'info') {
  const notification = document.createElement('div');
  notification.className = `alert alert-${type} alert-dismissible fade show position-fixed`;
  notification.style.top = '20px';
  notification.style.right = '20px';
  notification.style.zIndex = '9999';
  notification.innerHTML = `
    ${message}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
  `;
  
  document.body.appendChild(notification);
  
  setTimeout(() => {
    if (notification.parentNode) {
      notification.parentNode.removeChild(notification);
    }
  }, 5000);
}

// Auto-refresh for reminders
setInterval(() => {
  if (window.location.pathname === '/dashboard') {
    fetchReminderCounts();
  }
}, 60000); // Hver minutt

// Helper function to show toast notifications
function showToastNotification(message, type = 'info', duration = 3000) {
  // Create toast container if it doesn't exist
  let toastContainer = document.getElementById('toast-container');
  if (!toastContainer) {
    toastContainer = document.createElement('div');
    toastContainer.id = 'toast-container';
    toastContainer.className = 'position-fixed top-0 end-0 p-3';
    toastContainer.style.zIndex = '9999';
    document.body.appendChild(toastContainer);
  }
  
  // Generate a unique ID for this toast
  const toastId = 'toast-' + Date.now();
  
  // Create the toast element
  const toastEl = document.createElement('div');
  toastEl.id = toastId;
  toastEl.className = `toast toast-pwa align-items-center text-white bg-${type} border-0`;
  toastEl.setAttribute('role', 'alert');
  toastEl.setAttribute('aria-live', 'assertive');
  toastEl.setAttribute('aria-atomic', 'true');
  
  // Create toast content
  const toastContent = document.createElement('div');
  toastContent.className = 'd-flex';
  
  const toastBody = document.createElement('div');
  toastBody.className = 'toast-body';
  toastBody.textContent = message;
  
  const closeButton = document.createElement('button');
  closeButton.type = 'button';
  closeButton.className = 'btn-close btn-close-white me-2 m-auto';
  closeButton.setAttribute('data-bs-dismiss', 'toast');
  closeButton.setAttribute('aria-label', 'Lukk');
  
  // Assemble the toast
  toastContent.appendChild(toastBody);
  toastContent.appendChild(closeButton);
  toastEl.appendChild(toastContent);
  
  // Add to container
  toastContainer.appendChild(toastEl);
  
  // Initialize Bootstrap toast
  const toast = new bootstrap.Toast(toastEl, {
    animation: true,
    autohide: true,
    delay: duration
  });
  
  // Show the toast
  toast.show();
  
  // Set up auto-removal
  setTimeout(() => {
    if (toastEl && toastEl.parentNode) {
      toastEl.parentNode.removeChild(toastEl);
    }
  }, duration + 500);
  
  return toastId;
}

// Global variables for sound system
window.userInteracted = false;
window.audioContext = null;

// Track user interaction for mobile audio
document.addEventListener('click', () => { window.userInteracted = true; }, { once: true });
document.addEventListener('touchstart', () => { window.userInteracted = true; }, { once: true });

// Enhanced sound playback with comprehensive fallbacks
function playNotificationSound(soundName = 'pristine.mp3') {
    console.log(`🔊 Attempting to play sound: ${soundName}`);
    
    if (!window.userInteracted) {
        console.warn('⚠️ No user interaction detected, sound may not play on mobile');
    }
    
    try {
        // Create audio with multiple format fallbacks
        const audioFormats = [
            `/static/sounds/${soundName}`,
            `/static/sounds/${soundName.replace('.mp3', '.wav')}`,
            `/static/sounds/${soundName.replace('.mp3', '.ogg')}`,
            `/static/sounds/pristine.wav` // Ultimate fallback
        ];
        
        let audioLoaded = false;
        let attempts = 0;
        
        function tryNextFormat() {
            if (attempts >= audioFormats.length || audioLoaded) return;
            
            const audioPath = audioFormats[attempts];
            console.log(`🎵 Trying audio format ${attempts + 1}/${audioFormats.length}: ${audioPath}`);
            
            const audio = new Audio();
            audio.volume = 0.7;
            audio.preload = 'auto';
            
            // Set up success handler
            const playAudio = () => {
                if (!audioLoaded) {
                    audioLoaded = true;
                    console.log(`✅ Audio loaded successfully: ${audioPath}`);
                    
                    audio.play().then(() => {
                        console.log('✅ Audio played successfully');
                        showNotificationFeedback('🔊 Lyd avspilt', 'success');
                    }).catch(error => {
                        console.error(`❌ Audio play failed: ${error}`);
                        tryFallbackNotification();
                    });
                }
            };
            
            // Event listeners
            audio.addEventListener('canplaythrough', playAudio, { once: true });
            audio.addEventListener('loadeddata', playAudio, { once: true });
            
            audio.addEventListener('error', (error) => {
                console.warn(`⚠️ Audio load failed for ${audioPath}:`, error);
                attempts++;
                if (attempts < audioFormats.length) {
                    setTimeout(tryNextFormat, 100);
                } else {
                    console.error('❌ All audio formats failed');
                    tryFallbackNotification();
                }
            });
            
            // Set source and try to load
            audio.src = audioPath;
            audio.load();
            
            // Timeout fallback
            setTimeout(() => {
                if (!audioLoaded) {
                    attempts++;
                    if (attempts < audioFormats.length) {
                        tryNextFormat();
                    }
                }
            }, 2000);
        }
        
        // Start trying formats
        tryNextFormat();
        
    } catch (error) {
        console.error('❌ Critical audio error:', error);
        tryFallbackNotification();
    }
}

// Fallback notification methods
function tryFallbackNotification() {
    console.log('🔄 Trying fallback notification methods...');
    
    // Try browser notification sound
    if ('Notification' in window && Notification.permission === 'granted') {
        try {
            const notification = new Notification('', {
                body: '',
                silent: false,
                tag: 'sound-fallback',
                icon: '/static/images/icon-96x96.png'
            });
            
            setTimeout(() => notification.close(), 100);
            console.log('✅ System notification triggered');
            showNotificationFeedback('🔔 Systemlyd avspilt', 'info');
            return true;
        } catch (error) {
            console.warn('⚠️ System notification failed:', error);
        }
    }
    
    // Try vibration on mobile
    if ('vibrate' in navigator) {
        try {
            navigator.vibrate([200, 100, 200, 100, 400]);
            console.log('✅ Vibration triggered');
            showNotificationFeedback('📳 Vibrasjon aktivert', 'info');
            return true;
        } catch (error) {
            console.warn('⚠️ Vibration failed:', error);
        }
    }
    
    // Visual feedback only
    showNotificationFeedback('🔔 Notifikasjon mottatt (lyd ikke tilgjengelig)', 'warning');
    return false;
}

// Enhanced notification feedback
function showNotificationFeedback(message, type = 'info') {
    // Remove existing notifications
    const existing = document.querySelectorAll('.audio-feedback');
    existing.forEach(el => el.remove());
    
    const notification = document.createElement('div');
    notification.className = `audio-feedback alert alert-${type} position-fixed`;
    notification.style.cssText = `
        top: 20px;
        right: 20px;
        z-index: 9999;
        max-width: 300px;
        animation: slideInRight 0.3s ease-out;
        box-shadow: 0 4px 15px rgba(0,0,0,0.2);
    `;
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <span>${message}</span>
            <button type="button" class="btn-close ms-auto" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 3000);
}

// Test sound function with better feedback
function testSound(soundFile) {
    console.log(`🧪 Testing sound: ${soundFile}`);
    
    // Mark user interaction
    window.userInteracted = true;
    
    showNotificationFeedback(`🎵 Tester lyd: ${soundFile}`, 'info');
    
    try {
        playNotificationSound(soundFile);
    } catch (error) {
        console.error('❌ Test sound failed:', error);
        showNotificationFeedback(`❌ Kunne ikke teste ${soundFile}`, 'error');
    }
}

// Enhanced service worker message handling
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.addEventListener('message', event => {
        console.log('📨 Message from service worker:', event.data);
        
        if (event.data && event.data.type === 'PLAY_NOTIFICATION_SOUND') {
            const soundFile = event.data.sound || 'pristine.mp3';
            console.log(`🔊 Service worker requested sound: ${soundFile}`);
            
            // Check notification permission first
            if (Notification.permission !== 'granted') {
                console.warn('⚠️ Notification permission not granted, requesting...');
                requestNotificationPermission().then(permission => {
                    if (permission === 'granted') {
                        playNotificationSound(soundFile);
                    }
                });
            } else {
                playNotificationSound(soundFile);
            }
        }
    });
}

// Enhanced notification permission handling
function requestNotificationPermission() {
    console.log('🔔 Requesting notification permission...');
    
    if (!('Notification' in window)) {
        console.error('❌ This browser does not support notifications');
        showNotificationFeedback('❌ Nettleseren støtter ikke notifikasjoner', 'error');
        return Promise.resolve('denied');
    }
    
    if (Notification.permission === 'granted') {
        console.log('✅ Notification permission already granted');
        return Promise.resolve('granted');
    }
    
    if (Notification.permission === 'denied') {
        console.warn('⚠️ Notification permission denied');
        showNotificationFeedback('📱 Varslinger er valgfritt - appen fungerer uten dem også!', 'info');
        return Promise.resolve('denied');
    }
    
    // Request permission
    return Notification.requestPermission().then(permission => {
        console.log(`🔔 Notification permission result: ${permission}`);
        
        if (permission === 'granted') {
            showNotificationFeedback('✅ Notifikasjoner aktivert!', 'success');
        } else {
            showNotificationFeedback('❌ Notifikasjoner avvist', 'error');
        }
        
        return permission;
    }).catch(error => {
        console.error('❌ Error requesting notification permission:', error);
        showNotificationFeedback('❌ Feil ved forespørsel om notifikasjoner', 'error');
        return 'denied';
    });
}

// Enhanced push notification setup
async function setupPushNotifications() {
    console.log('🔔 Setting up push notifications...');
    
    try {
        // Check if service worker is supported
        if (!('serviceWorker' in navigator)) {
            throw new Error('Service Worker not supported');
        }
        
        // Check if push messaging is supported
        if (!('PushManager' in window)) {
            throw new Error('Push messaging not supported');
        }
        
        // DONT request permission automatically - only if user clicks the button
        if (Notification.permission !== 'granted') {
            console.log('ℹ️ Notification permission not granted - user must click button');
            return false;
        }
        
        // Register service worker
        const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/'
        });
        console.log('✅ Service Worker registered');
        
        // Wait for service worker to be ready
        await navigator.serviceWorker.ready;
        console.log('✅ Service Worker ready');
        
        // Get VAPID public key
        const vapidResponse = await fetch('/api/vapid-public-key');
        if (!vapidResponse.ok) {
            throw new Error('Failed to get VAPID public key');
        }
        const vapidData = await vapidResponse.json();
        
        // Validate VAPID key
        if (!vapidData.public_key || vapidData.public_key.length < 64) {
            throw new Error('Invalid VAPID public key received from server');
        }
        
        // Convert VAPID key to proper format
        console.log('🔑 Converting VAPID key:', vapidData.public_key.substring(0, 20) + '...');
        const applicationServerKey = urlBase64ToUint8Array(vapidData.public_key);
        console.log('🔑 Converted key length:', applicationServerKey.length);
        
        // Subscribe to push notifications
        const subscription = await registration.pushManager.subscribe({
            userVisibleOnly: true,
            applicationServerKey: applicationServerKey
        });
        
        // Send subscription to server
        const subscribeResponse = await fetch('/api/subscribe-push', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(subscription)
        });
        
        if (!subscribeResponse.ok) {
            throw new Error('Failed to subscribe to push notifications');
        }
        
        console.log('✅ Push notifications setup complete');
        return true;
        
    } catch (error) {
        console.error('❌ Push notification setup failed:', error);
        
        // Show user-friendly error message
        let errorMessage = 'Kunne ikke sette opp push-notifikasjoner';
        if (error.message.includes('permission') || error.message.includes('denied')) {
            errorMessage = 'Varslinger er valgfritt - appen fungerer uten dem også!';
        } else if (error.message.includes('not supported')) {
            errorMessage = 'Nettleseren støtter ikke push-notifikasjoner (ikke nødvendig)';
        } else if (error.message.includes('InvalidAccessError') || error.message.includes('applicationServerKey')) {
            errorMessage = 'Push-varslinger er midlertidig utilgjengelige, men appen fungerer normalt';
        } else if (error.message.includes('Failed to get VAPID')) {
            errorMessage = 'Varslinger er ikke konfigurert på serveren (valgfritt)';
        }
        
        // Don't show this error too frequently
        if (!window.lastNotificationError || Date.now() - window.lastNotificationError > 30000) {
            showNotificationFeedback(`💡 ${errorMessage}`, 'info');
            window.lastNotificationError = Date.now();
        }
        return false;
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 App.js DOM loaded, initializing...');
    
    // Only setup push notifications if user has explicitly granted permission
    if (Notification.permission === 'granted') {
        console.log('🔔 User has granted notification permission, setting up push notifications...');
        setupPushNotifications();
    } else {
        console.log('ℹ️ Push notifications not set up - user must grant permission first');
    }
    
    // Add CSS for animations
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideInRight {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        @keyframes slideOutRight {
            from { transform: translateX(0); opacity: 1; }
            to { transform: translateX(100%); opacity: 0; }
        }
    `;
    document.head.appendChild(style);
});

// Add a function to test all sounds
function testAllSounds() {
    const sounds = ['pristine.mp3', 'alert.mp3', 'ding.mp3', 'chime.mp3'];
    let index = 0;
    
    function testNext() {
        if (index < sounds.length) {
            testSound(sounds[index]);
            index++;
            setTimeout(testNext, 3000); // Wait 3 seconds between tests
        }
    }
    
    testNext();
}

// Make functions globally available
window.playNotificationSound = playNotificationSound;
window.testSound = testSound;
window.testAllSounds = testAllSounds;
window.requestNotificationPermission = requestNotificationPermission;
window.setupPushNotifications = setupPushNotifications;