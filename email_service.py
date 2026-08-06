"""
E-post service for Smart Påminner Pro
Håndterer alle typer e-post notifikasjoner
"""

from flask import render_template, url_for, current_app
from flask_mail import Message
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Sentral e-post service for alle notifikasjoner"""
    
    def __init__(self, mail, data_manager):
        self.mail = mail
        self.dm = data_manager
    
    def _send_email(self, to, subject, template, **kwargs):
        """Intern metode for å sende e-post"""
        try:
            # Ensure 'to' is a list
            recipients = [to] if isinstance(to, str) else to
            
            msg = Message(
                subject=subject,
                recipients=recipients,
                html=render_template(template, **kwargs),
                sender=current_app.config.get('MAIL_DEFAULT_SENDER')
            )
            
            self.mail.send(msg)
            
            # Log successful email
            self._log_email(recipients[0], subject, 'sent', template)
            logger.info(f"E-post sendt til {recipients[0]}: {subject}")
            return True
            
        except Exception as e:
            # Log failed email
            self._log_email(to, subject, 'failed', template, str(e))
            logger.error(f"Feil ved sending av e-post til {to}: {e}")
            return False
    
    def _log_email(self, recipient, subject, status, template, error=None):
        """Logg e-post aktivitet"""
        try:
            email_log = self.dm.load_data('email_log')
            log_entry = {
                'recipient': recipient,
                'subject': subject,
                'template': template,
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'error': error
            }
            email_log.append(log_entry)
            self.dm.save_data('email_log', email_log)
        except Exception as e:
            logger.error(f"Feil ved logging av e-post: {e}")
    
    def send_reminder_notification(self, reminder, recipient_email):
        """Send påminnelse-notifikasjon"""
        subject = f"🔔 Påminnelse: {reminder['title']}"
        
        return self._send_email(
            to=recipient_email,
            subject=subject,
            template='emails/reminder_notification.html',
            reminder=reminder,
            recipient=recipient_email
        )
    
    def send_shared_reminder_notification(self, reminder, shared_by, recipient_email):
        """Send notifikasjon om delt påminnelse"""
        subject = f"👥 Ny delt påminnelse fra {shared_by}: {reminder['title']}"
        
        return self._send_email(
            to=recipient_email,
            subject=subject,
            template='emails/shared_reminder.html',
            reminder=reminder,
            shared_by=shared_by,
            recipient=recipient_email
        )
    
    def send_noteboard_invitation(self, board, invited_by, recipient_email):
        """Send invitasjon til delt tavle"""
        subject = f"📋 Invitasjon til delt tavle: {board.title}"
        
        # Create join URL
        with current_app.app_context():
            join_url = url_for('join_board', code=board.access_code, _external=True)
        
        return self._send_email(
            to=recipient_email,
            subject=subject,
            template='emails/noteboard_invitation.html',
            board=board,
            invited_by=invited_by,
            recipient_email=recipient_email,
            join_url=join_url
        )
    
    def send_noteboard_update(self, board, update_type, updated_by, recipient_emails, note=None):
        """Send oppdatering om tavle-endringer"""
        subject = f"📋 Oppdatering på tavle: {board.title}"
        
        # Create board URL
        with current_app.app_context():
            board_url = url_for('view_board', board_id=board.board_id, _external=True)
        
        success_count = 0
        for recipient_email in recipient_emails:
            if recipient_email != updated_by:  # Don't send to the person who made the update
                if self._send_email(
                    to=recipient_email,
                    subject=subject,
                    template='emails/noteboard_update.html',
                    board=board,
                    update_type=update_type,
                    updated_by=updated_by,
                    update_time=datetime.now(),
                    recipient_email=recipient_email,
                    board_url=board_url,
                    note=note
                ):
                    success_count += 1
        
        return success_count
    
    def send_test_email(self, recipient_email):
        """Send test-e-post for å verifisere konfigurasjon"""
        subject = "✉️ Test e-post fra Smart Påminner Pro"
        
        return self._send_email(
            to=recipient_email,
            subject=subject,
            template='emails/email_test.html',
            recipient=recipient_email,
            sender=current_app.config.get('MAIL_DEFAULT_SENDER'),
            timestamp=datetime.now(),
            mail_server=current_app.config.get('MAIL_SERVER')
        )
    
    def get_email_statistics(self):
        """Hent e-post statistikk"""
        try:
            email_log = self.dm.load_data('email_log')
            
            total_sent = len([e for e in email_log if e['status'] == 'sent'])
            total_failed = len([e for e in email_log if e['status'] == 'failed'])
            
            # Count by template type
            template_stats = {}
            for entry in email_log:
                template = entry.get('template', 'unknown')
                if template not in template_stats:
                    template_stats[template] = {'sent': 0, 'failed': 0}
                template_stats[template][entry['status']] += 1
            
            return {
                'total_sent': total_sent,
                'total_failed': total_failed,
                'success_rate': (total_sent / (total_sent + total_failed) * 100) if (total_sent + total_failed) > 0 else 0,
                'by_template': template_stats,
                'recent_emails': email_log[-10:]  # Last 10 emails
            }
        
        except Exception as e:
            logger.error(f"Feil ved henting av e-post statistikk: {e}")
            return {
                'total_sent': 0,
                'total_failed': 0,
                'success_rate': 0,
                'by_template': {},
                'recent_emails': []
            }
