/**
 * Sound Features - Håndterer lydavspilling og -tester for SmartReminder
 * Inkluderer:
 * - Avspilling av varslingslyder
 * - Tester for lydvarsler
 * - Audio API kompatibilitetskontroller
 */

// Konstanter for lydvarsler
const SOUNDS = {
    ALERT: '/static/sounds/alert.mp3',
    PRISTINE: '/static/sounds/pristine.mp3',
    DING: '/static/sounds/ding.mp3',
    CHIME: '/static/sounds/chime.mp3'
};

// Audio Context instans
let audioContext = null;

/**
 * Initaliserer AudioContext
 * Viktig: Dette må kalles fra en brukerutløst handling (f.eks. klikk)
 */
function initAudioContext() {
    if (audioContext) return audioContext;
    
    // Opprett AudioContext (med fallback for eldre nettlesere)
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
    return audioContext;
}

/**
 * Sjekker om nettleseren støtter lydavspilling
 * @returns {boolean} Om lyd støttes
 */
function isSoundSupported() {
    return 'AudioContext' in window || 'webkitAudioContext' in window;
}

/**
 * Spiller av en lyd fra URL med volum
 * @param {string} soundUrl - URL til lydfilen
 * @param {number} volume - Volum (0.0 til 1.0)
 * @returns {Promise} Promise som fullfører når lyden er spilt av
 */
async function playSound(soundUrl, volume = 1.0) {
    // Fallback til HTML5 Audio API hvis AudioContext ikke er støttet
    if (!isSoundSupported()) {
        return playSoundWithHtmlAudio(soundUrl, volume);
    }
    
    try {
        // Sikre at AudioContext er initialisert
        const context = initAudioContext();
        
        // Hent lydfilen
        const response = await fetch(soundUrl);
        if (!response.ok) throw new Error(`Kunne ikke laste lyd: ${soundUrl}`);
        
        // Dekod lyden
        const arrayBuffer = await response.arrayBuffer();
        const audioBuffer = await context.decodeAudioData(arrayBuffer);
        
        // Opprett lydkilde og volum
        const source = context.createBufferSource();
        const gainNode = context.createGain();
        
        // Koble sammen og sett volum
        source.buffer = audioBuffer;
        gainNode.gain.value = volume;
        
        source.connect(gainNode);
        gainNode.connect(context.destination);
        
        // Start avspilling
        source.start(0);
        
        // Returner promise som fullfører når lyden er ferdig
        return new Promise(resolve => {
            source.onended = resolve;
        });
    } catch (error) {
        console.error('Feil ved avspilling av lyd:', error);
        // Prøv fallback-metode ved feil
        return playSoundWithHtmlAudio(soundUrl, volume);
    }
}

/**
 * Fallback for å spille lyd med HTML5 Audio API
 * @param {string} soundUrl - URL til lydfilen
 * @param {number} volume - Volum (0.0 til 1.0)
 * @returns {Promise} Promise som fullfører når lyden er spilt av
 */
function playSoundWithHtmlAudio(soundUrl, volume = 1.0) {
    return new Promise((resolve, reject) => {
        const audio = new Audio(soundUrl);
        audio.volume = volume;
        
        audio.onended = resolve;
        audio.onerror = reject;
        
        // Håndter Safari/iOS restriksjon med brukerinteraksjon
        const playPromise = audio.play();
        
        if (playPromise !== undefined) {
            playPromise.catch(error => {
                console.warn('Kunne ikke spille lyd automatisk:', error);
                // Signaliser at brukeren må interagere
                document.dispatchEvent(new CustomEvent('sound-needs-interaction'));
            });
        }
    });
}

/**
 * Tester alle varslingslyder i sekvens
 * @returns {Promise} Promise som fullfører når alle lyder er spilt av
 */
async function testAllSounds() {
    console.log('🔊 Tester alle varslingslyder...');
    
    for (const [name, url] of Object.entries(SOUNDS)) {
        console.log(`Spiller av ${name}...`);
        try {
            await playSound(url);
            await new Promise(resolve => setTimeout(resolve, 1000));
        } catch (error) {
            console.error(`Feil ved avspilling av ${name}:`, error);
        }
    }
    
    console.log('🎵 Lydtest fullført');
}

// Eksporter funksjoner for bruk i andre filer
window.soundFeatures = {
    playSound,
    testAllSounds,
    SOUNDS,
    isSoundSupported
};

// Eksporter for testing med Node.js
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        playSound,
        testAllSounds,
        SOUNDS,
        isSoundSupported
    };
}
