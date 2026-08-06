"""
Password Reset Functionality for SmartReminder
Handles password reset tokens and email sending
"""

import secrets
import hashlib
from datetime import datetime, timedelta
import logging
from push_service import send_password_reset_notification, send_password_reset_confirmation

logger = logging.getLogger(__name__)

def generate_reset_token():
    """Generate a secure reset token"""
    return secrets.token_urlsafe(32)

def create_password_reset_request(user_email, dm=None):
    """Create a password reset request for user"""
    if not dm:
        return False
        
    try:
        # Check if user exists (case-insensitive)
        users_data = dm.load_data('users')
        _target = str(user_email or '').strip().lower()
        user_exists = False
        for user_id, user_data in users_data.items():
            if str(user_data.get('email', '')).strip().lower() == _target:
                user_exists = True
                break
        
        if not user_exists:
            logger.warning(f"Password reset requested for non-existent user: {user_email}")
            return False
        
        # Generate reset token
        reset_token = generate_reset_token()
        
        # Store reset request
        reset_requests = dm.load_data('password_reset_requests')
        reset_requests[reset_token] = {
            'user_email': user_email,
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat(),
            'used': False
        }
        dm.save_data('password_reset_requests', reset_requests)
        
        # Best-effort push notification (email with the link is sent by the caller)
        try:
            send_password_reset_notification(user_email, reset_token, dm)
        except Exception as push_err:
            logger.warning(f"Push reset-notification failed for {user_email}: {push_err}")

        logger.info(f"Password reset request created for {user_email}")
        return reset_token
        
    except Exception as e:
        logger.error(f"Error creating password reset request for {user_email}: {e}")
        return False

def validate_reset_token(token, dm=None):
    """Validate a password reset token"""
    if not dm or not token:
        return None
        
    try:
        reset_requests = dm.load_data('password_reset_requests')
        request = reset_requests.get(token)
        
        if not request:
            return None
            
        # Check if token is expired
        expires_at = datetime.fromisoformat(request['expires_at'])
        if datetime.now() > expires_at:
            return None
            
        # Check if token is already used
        if request.get('used', False):
            return None
            
        return request['user_email']
        
    except Exception as e:
        logger.error(f"Error validating reset token: {e}")
        return None

def reset_user_password(token, new_password, dm=None):
    """Reset user password using valid token"""
    if not dm:
        return False
        
    try:
        user_email = validate_reset_token(token, dm)
        if not user_email:
            return False
            
        # Update user password.
        # NB: users-dictet er nøklet på user_id (UUID), ikke e-post — finn riktig bruker.
        users_data = dm.load_data('users')
        target_user_id = None
        _t = str(user_email or '').strip().lower()
        for uid, udata in users_data.items():
            if isinstance(udata, dict) and str(udata.get('email', '')).strip().lower() == _t:
                target_user_id = uid
                break

        if target_user_id is not None:
            # Bruk werkzeug (saltet pbkdf2) og skriv til 'password_hash' — samme felt som login leser.
            from werkzeug.security import generate_password_hash
            users_data[target_user_id]['password_hash'] = generate_password_hash(new_password)
            # Fjern evt. gammelt, usikkert 'password'-felt hvis det finnes.
            users_data[target_user_id].pop('password', None)
            dm.save_data('users', users_data)

            # Mark token as used
            reset_requests = dm.load_data('password_reset_requests')
            if token in reset_requests:
                reset_requests[token]['used'] = True
                dm.save_data('password_reset_requests', reset_requests)

            # Send confirmation
            send_password_reset_confirmation(user_email, dm)

            logger.info(f"Password reset successful for {user_email}")
            return True

        return False
        
    except Exception as e:
        logger.error(f"Error resetting password: {e}")
        return False

def cleanup_expired_tokens(dm=None):
    """Remove expired password reset tokens"""
    if not dm:
        return
        
    try:
        reset_requests = dm.load_data('password_reset_requests')
        current_time = datetime.now()
        
        expired_tokens = []
        for token, request in reset_requests.items():
            expires_at = datetime.fromisoformat(request['expires_at'])
            if current_time > expires_at:
                expired_tokens.append(token)
        
        for token in expired_tokens:
            del reset_requests[token]
            
        if expired_tokens:
            dm.save_data('password_reset_requests', reset_requests)
            logger.info(f"Cleaned up {len(expired_tokens)} expired reset tokens")
            
    except Exception as e:
        logger.error(f"Error cleaning up expired tokens: {e}")
