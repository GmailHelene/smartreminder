# filepath: /workspaces/smartreminder/focus_modes.py
"""
Focus Modes for Smart Påminner Pro
Ulike moduser for forskjellige brukerbehov
"""

from datetime import datetime, timedelta
import json
import os
import logging

logger = logging.getLogger(__name__)

class FocusMode:
    """Base class for focus modes"""
    
    def __init__(self, name, description, settings):
        self.name = name
        self.description = description
        self.settings = settings
    
    def apply_to_reminders(self, reminders):
        """Apply focus mode settings to reminders"""
        return reminders
    
    def get_notification_settings(self):
        """Get notification preferences for this mode"""
        return self.settings.get('notifications', {})
    
    def get_display_settings(self):
        """Get display preferences for this mode"""
        return self.settings.get('display', {})
    
    def to_dict(self):
        """Convert focus mode to dictionary for storage or API"""
        return {
            'name': self.name,
            'description': self.description,
            'settings': self.settings
        }

class NormalMode(FocusMode):
    """Normal modus - Standard brukeropplevelse"""
    
    def __init__(self):
        super().__init__(
            name="Normal",
            description="Standard brukeropplevelse med alle funksjoner",
            settings={
                'notifications': {
                    'email_enabled': True,
                    'sound_enabled': True,
                    'sound': 'pristine.mp3',
                    'priority_filter': ['Høy', 'Medium', 'Lav'],
                    'quiet_hours': None
                },
                'display': {
                    'simplified_view': False,
                    'large_text': False,
                    'high_contrast': False,
                    'reduced_colors': False,
                    'minimal_animations': False
                }
            }
        )

class SilentMode(FocusMode):
    """Stillemodus - Minimale forstyrrelser"""
    
    def __init__(self):
        super().__init__(
            name="Stillemodus",
            description="Reduserte notifikasjoner, kun høy prioritet",
            settings={
                'notifications': {
                    'email_enabled': False,
                    'sound_enabled': False,
                    'sound': 'silent.mp3',
                    'priority_filter': ['Høy'],
                    'quiet_hours': {'start': '22:00', 'end': '08:00'}
                },
                'display': {
                    'simplified_view': True,
                    'reduced_colors': True,
                    'minimal_animations': True,
                    'large_text': False,
                    'high_contrast': False
                }
            }
        )
    
    def apply_to_reminders(self, reminders):
        """Filter til kun høy prioritet påminnelser"""
        return [r for r in reminders if r.get('priority') == 'Høy']

class ADHDMode(FocusMode):
    """ADHD-modus - Optimalisert for konsentrasjon og fokus"""
    
    def __init__(self):
        super().__init__(
            name="ADHD-modus",
            description="Optimalisert for konsentrasjon og fokus",
            settings={
                'notifications': {
                    'email_enabled': True,
                    'sound_enabled': True,
                    'sound': 'alert.mp3',
                    'priority_filter': ['Høy', 'Medium'],
                    'quiet_hours': None
                },
                'display': {
                    'simplified_view': True,
                    'reduced_colors': True,
                    'minimal_animations': False,
                    'large_text': False,
                    'high_contrast': True
                }
            }
        )
    
    def apply_to_reminders(self, reminders):
        """Prioriter høy og medium prioritet, grupper etter kategori"""
        filtered = [r for r in reminders if r.get('priority') in ['Høy', 'Medium']]
        
        # Sorter etter prioritet og deretter etter kategori
        return sorted(filtered, key=lambda r: (
            0 if r.get('priority') == 'Høy' else 1,
            r.get('category', 'Ukategorisert')
        ))

class ElderlyMode(FocusMode):
    """Seniormodus - Tilpasset for eldre brukere"""
    
    def __init__(self):
        super().__init__(
            name="Seniormodus",
            description="Tilpasset for eldre brukere, større tekst og enkelt grensesnitt",
            settings={
                'notifications': {
                    'email_enabled': True,
                    'sound_enabled': True,
                    'sound': 'chime.mp3',
                    'priority_filter': ['Høy', 'Medium', 'Lav'],
                    'quiet_hours': {'start': '21:00', 'end': '08:00'}
                },
                'display': {
                    'simplified_view': True,
                    'reduced_colors': False,
                    'minimal_animations': True,
                    'large_text': True,
                    'high_contrast': True
                }
            }
        )
    
    def apply_to_reminders(self, reminders):
        """Ingen filtrering, men sikre at alle har tydelig prioritet"""
        for reminder in reminders:
            if 'priority' not in reminder:
                reminder['priority'] = 'Medium'
        return reminders

class DrivingSchoolMode(FocusMode):
    """Kjøreskolemodus - For kjørelærere og kjøreskoleelever"""
    
    def __init__(self):
        super().__init__(
            name="Kjøreskolemodus",
            description="Optimalisert for kjørelærere og kjøreskoleelever",
            settings={
                'notifications': {
                    'email_enabled': True,
                    'sound_enabled': True,
                    'sound': 'alert.mp3',
                    'priority_filter': ['Høy', 'Medium', 'Lav'],
                    'quiet_hours': None,
                    'enforce_confirmation': True,
                    'allow_sharing': True,
                    'share_with_high_priority': True
                },
                'display': {
                    'simplified_view': True,
                    'reduced_colors': False,
                    'minimal_animations': True,
                    'large_text': False,
                    'high_contrast': True,
                    'show_confirmation_buttons': True,
                    'show_location_info': True
                }
            }
        )
    
    def apply_to_reminders(self, reminders):
        """Sorter etter tid og dato, prioriter kjøretimer"""
        # Prioriter alle påminnelser med "kjøretime" i tittelen
        for reminder in reminders:
            if 'title' in reminder and 'kjøretime' in reminder['title'].lower():
                reminder['priority'] = 'Høy'
                
        # Sorter etter dato og tid
        return sorted(reminders, key=lambda r: r.get('datetime', ''))

class FocusModeManager:
    """Håndterer fokusmoduser og brukerinnstillinger"""
    
    MODES = {
        'normal': NormalMode(),
        'silent': SilentMode(),
        'adhd': ADHDMode(),
        'elderly': ElderlyMode(),
        'driving_school': DrivingSchoolMode()
    }
    
    USER_SETTINGS_PATH = 'data/user_focus_settings.json'
    
    @classmethod
    def get_all_modes(cls):
        """Hent alle tilgjengelige fokusmoduser"""
        return cls.MODES
    
    @classmethod
    def get_mode(cls, mode_name):
        """Hent en spesifikk fokusmodus"""
        return cls.MODES.get(mode_name, cls.MODES['normal'])
    
    @classmethod
    def get_user_mode(cls, user_email):
        """Hent brukerens valgte fokusmodus"""
        settings = cls._load_user_settings()
        mode_name = settings.get(user_email, 'normal')
        return cls.get_mode(mode_name)
    
    @classmethod
    def set_user_mode(cls, user_email, mode_name):
        """Sett brukerens fokusmodus"""
        if mode_name not in cls.MODES:
            raise ValueError(f"Ukjent fokusmodus: {mode_name}")
        
        settings = cls._load_user_settings()
        settings[user_email] = mode_name
        cls._save_user_settings(settings)
        
        logger.info(f"Fokusmodus for {user_email} satt til {mode_name}")
        return True
    
    @classmethod
    def _load_user_settings(cls):
        """Last brukerinnstillinger fra fil"""
        if not os.path.exists(cls.USER_SETTINGS_PATH):
            # Ensure the directory exists
            os.makedirs(os.path.dirname(cls.USER_SETTINGS_PATH), exist_ok=True)
            return {}
        
        try:
            with open(cls.USER_SETTINGS_PATH, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Kunne ikke laste brukerinnstillinger: {e}")
            return {}
    
    @classmethod
    def _save_user_settings(cls, settings):
        """Lagre brukerinnstillinger til fil"""
        try:
            # Ensure the directory exists
            os.makedirs(os.path.dirname(cls.USER_SETTINGS_PATH), exist_ok=True)
            
            with open(cls.USER_SETTINGS_PATH, 'w') as f:
                json.dump(settings, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Kunne ikke lagre brukerinnstillinger: {e}")
            return False