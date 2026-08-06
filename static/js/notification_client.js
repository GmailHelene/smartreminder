// Simple client-side notification support
// Add to your main app.js file or include as a separate script

// Global sound context for iOS compatibility
let audioContext = null;

// Initialize notification system
function initNotificationSystem() {
  // Request permission for notifications if needed
  if ('Notification' in window) {
    if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
      Notification.requestPermission();
    }
  }
  
  // Initialize audio context on user interaction for iOS
  document.addEventListener('click', initAudioContext, { once: true });
  document.addEventListener('touchstart', initAudioContext, { once: true });
}

// Initialize audio context (needs user interaction first on iOS)
function initAudioContext() {
  if (audioContext === null) {
    try {
      window.AudioContext = window.AudioContext || window.webkitAudioContext;
      audioContext = new AudioContext();
      console.log('🔊 Audio context initialized');
    } catch (e) {
      console.warn('⚠️ AudioContext not supported', e);
    }
  }
}

// Check if sound is enabled based on focus mode
function isSoundEnabled() {
  // Check if focus mode manager is available
  if (window.focusModeManager) {
    const currentMode = window.focusModeManager.getCurrentMode();
    
    // Silent mode has sound disabled
    if (currentMode === 'silent') {
      return false;
    }
    
    // Check quiet hours for work mode
    if (currentMode === 'work') {
      const now = new Date();
      const hours = now.getHours();
      const minutes = now.getMinutes();
      const currentTime = hours * 60 + minutes;
      
      // Work hours: 8:00 - 17:00
      const workStart = 8 * 60;
      const workEnd = 17 * 60;
      
      // Only enable sounds during work hours
      return currentTime >= workStart && currentTime <= workEnd;
    }
  }
  
  // Default: sound enabled
  return true;
}

// Get notification sound based on focus mode
function getNotificationSound(defaultSound = 'pristine.mp3') {
  // Check if focus mode manager is available
  if (window.focusModeManager) {
    const currentModeData = window.focusModeManager.getCurrentModeData();
    return currentModeData.sound || defaultSound;
  }
  
  return defaultSound;
}

// Play notification sound
function playNotificationSound(sound) {
  // Check if sound should be played based on focus mode
  if (!isSoundEnabled()) {
    console.log('Sound disabled by focus mode settings');
    return;
  }
  
  // Use provided sound or get from focus mode
  const soundFile = sound || getNotificationSound();
  
  // iOS requires user interaction first
  if (audioContext === null) {
    initAudioContext();
  }
  
  // If audio context is available, use it
  if (audioContext) {
    const audio = new Audio(`/static/sounds/${soundFile}`);
    audio.play().catch(err => {
      console.warn('Could not play sound using AudioContext:', err);
      // Fallback to basic Audio
      const fallbackAudio = new Audio(`/static/sounds/${soundFile}`);
      fallbackAudio.play().catch(e => console.warn('Fallback sound failed:', e));
    });
  } else {
    // Basic Audio API fallback
    const audio = new Audio(`/static/sounds/${soundFile}`);
    audio.play().catch(err => console.warn('Could not play notification sound:', err));
  }
}

// Show browser notification with sound
function showNotification(title, message, options = {}) {
  // Check if notification should be shown based on focus mode
  if (window.focusModeManager) {
    const currentMode = window.focusModeManager.getCurrentMode();
    const currentModeData = window.focusModeManager.getCurrentModeData();
    
    // Handle priority filter for silent mode
    if (currentMode === 'silent') {
      // Only show high priority notifications
      if (options.priority !== 'high' && options.data && options.data.priority !== 'high') {
        console.log('Notification suppressed due to silent mode:', title);
        return null;
      }
    }
    
    // Handle work mode category filtering
    if (currentMode === 'work') {
      // Only show work-related notifications during work hours
      const now = new Date();
      const hours = now.getHours();
      const isWeekend = now.getDay() === 0 || now.getDay() === 6;
      
      if ((hours < 8 || hours > 17 || isWeekend) && 
          (options.category !== 'work' && (!options.data || options.data.category !== 'work'))) {
        console.log('Work-unrelated notification suppressed outside work hours:', title);
        return null;
      }
    }
    
    // Update sound based on focus mode
    if (currentModeData.sound) {
      options.sound = currentModeData.sound;
    }
  }

  // Default options
  const defaultOptions = {
    icon: '/static/images/icon-192x192.png',
    badge: '/static/images/badge-96x96.png',
    sound: 'pristine.mp3',
    tag: 'smartreminder-notification',
    vibrate: [200, 100, 200],
    requireInteraction: true,
    data: { url: '/dashboard' }
  };
  
  // Merge with provided options
  const notificationOptions = { ...defaultOptions, ...options };
  
  // Play sound
  if (notificationOptions.sound) {
    playNotificationSound(notificationOptions.sound);
  }
  
  // Show notification if supported
  if ('Notification' in window) {
    if (Notification.permission === 'granted') {
      // Create and show the notification
      const notification = new Notification(title, {
        body: message,
        icon: notificationOptions.icon,
        badge: notificationOptions.badge,
        tag: notificationOptions.tag,
        vibrate: notificationOptions.vibrate,
        requireInteraction: notificationOptions.requireInteraction,
        data: notificationOptions.data
      });
      
      // Add click handler
      notification.addEventListener('click', function() {
        const url = notificationOptions.data.url || '/dashboard';
        window.open(url, '_blank');
        notification.close();
      });
      
      return notification;
    } 
    else if (Notification.permission !== 'denied') {
      // Request permission
      Notification.requestPermission().then(permission => {
        if (permission === 'granted') {
          // Try again after permission granted
          return showNotification(title, message, options);
        }
      });
    }
  }
  
  return null;
}

// Check for notifications (polling approach)
function checkForNotifications(userEmail, interval = 10000) {
  if (!userEmail) return;
  
  // Set up polling interval
  const checkInterval = setInterval(() => {
    fetch(`/api/notifications/check?user_email=${userEmail}`)
      .then(response => response.json())
      .then(data => {
        if (data.notifications && data.notifications.length > 0) {
          // Process each notification
          data.notifications.forEach(notification => {
            showNotification(
              notification.title,
              notification.message,
              {
                sound: notification.sound,
                data: { url: notification.url || '/dashboard' }
              }
            );
          });
          
          // Mark as read
          fetch('/api/notifications/mark-read', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              user_email: userEmail,
              ids: data.notifications.map(n => n.id)
            })
          });
        }
      })
      .catch(err => console.error('Error checking notifications:', err));
  }, interval);
  
  // Store for cleanup
  window.notificationCheckInterval = checkInterval;
  
  // Initial check immediately
  fetch(`/api/notifications/check?user_email=${userEmail}`)
    .then(response => response.json())
    .then(data => {
      if (data.notifications && data.notifications.length > 0) {
        data.notifications.forEach(notification => {
          showNotification(
            notification.title,
            notification.message,
            {
              sound: notification.sound,
              data: { url: notification.url || '/dashboard' }
            }
          );
        });
        
        // Mark as read
        fetch('/api/notifications/mark-read', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_email: userEmail,
            ids: data.notifications.map(n => n.id)
          })
        });
      }
    });
}

// Stop checking for notifications
function stopNotificationChecks() {
  if (window.notificationCheckInterval) {
    clearInterval(window.notificationCheckInterval);
    window.notificationCheckInterval = null;
  }
}

// Listen for Service Worker messages (for compatibility with existing code)
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.addEventListener('message', function(event) {
    const data = event.data;
    
    if (data && data.type === 'PLAY_NOTIFICATION_SOUND') {
      playNotificationSound(data.sound || 'pristine.mp3');
    }
  });
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initNotificationSystem);

// Export functions for global use
window.SmartReminderNotifications = {
  show: showNotification,
  playSound: playNotificationSound,
  startChecking: checkForNotifications,
  stopChecking: stopNotificationChecks
};
