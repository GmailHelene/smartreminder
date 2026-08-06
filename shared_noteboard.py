"""
Shared Noteboard for Smart Påminner Pro
Delte tavler hvor brukere kan samarbeide
"""

import uuid
import json
from datetime import datetime
from pathlib import Path

class SharedNoteboard:
    """Delt tavle klasse"""
    
    def __init__(self, board_id, title, description, created_by, access_code=None):
        self.board_id = board_id
        self.title = title
        self.description = description
        self.created_by = created_by
        self.access_code = access_code or self._generate_access_code()
        self.created_at = datetime.now().isoformat()
        self.members = [created_by]
        self.notes = []
        self.settings = {
            'public': False,
            'allow_anonymous': False,
            'moderation': False
        }
    
    def _generate_access_code(self):
        """Generer tilgangskode for tavlen"""
        return str(uuid.uuid4())[:8].upper()
    
    def add_note(self, content, author, note_type='text', color='yellow'):
        """Legg til en ny notis på tavlen"""
        # Calculate position to avoid overlap
        notes_count = len(self.notes)
        grid_cols = 4  # Number of columns in grid
        
        # Calculate grid position
        col = notes_count % grid_cols
        row = notes_count // grid_cols
        
        # Position with spacing (220px wide + 30px margin)
        x = 50 + (col * 250)
        y = 50 + (row * 230)
        
        note = {
            'id': str(uuid.uuid4()),
            'content': content,
            'author': author,
            'type': note_type,  # text, checklist, image, link
            'color': color,
            'position': {'x': x, 'y': y},
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'tags': [],
            'completed': False if note_type == 'checklist' else None
        }
        self.notes.append(note)
        return note
    
    def update_note(self, note_id, content=None, position=None, color=None):
        """Oppdater en eksisterende notis"""
        for note in self.notes:
            if note['id'] == note_id:
                if content is not None:
                    note['content'] = content
                if position is not None:
                    note['position'] = position
                if color is not None:
                    note['color'] = color
                note['updated_at'] = datetime.now().isoformat()
                return note
        return None
    
    def delete_note(self, note_id, user_email):
        """Slett en notis (kun oppretteren eller admin)"""
        for i, note in enumerate(self.notes):
            if note['id'] == note_id:
                if note['author'] == user_email or user_email == self.created_by:
                    del self.notes[i]
                    return True
        return False
    
    def add_member(self, email):
        """Legg til medlem på tavlen"""
        if email not in self.members:
            self.members.append(email)
    
    def remove_member(self, email):
        """Fjern medlem fra tavlen"""
        if email in self.members and email != self.created_by:
            self.members.remove(email)

class NoteboardManager:
    """Håndterer alle delte tavler"""
    
    def __init__(self, data_manager):
        self.dm = data_manager
        self.boards_file = 'shared_noteboards'
        self._ensure_data_file()
    
    def _ensure_data_file(self):
        """Sørg for at data-fil eksisterer"""
        try:
            data = self.dm.load_data(self.boards_file)
            # Ensure data is a dict, not a list
            if not isinstance(data, dict):
                self.dm.save_data(self.boards_file, {})
        except:
            self.dm.save_data(self.boards_file, {})
    
    def create_board(self, title, description, created_by):
        """Opprett ny delt tavle"""
        board_id = str(uuid.uuid4())
        board = SharedNoteboard(board_id, title, description, created_by)
        
        boards = self.dm.load_data(self.boards_file)
        # Ensure boards is a dict
        if not isinstance(boards, dict):
            boards = {}
            
        boards[board_id] = {
            'board_id': board.board_id,
            'title': board.title,
            'description': board.description,
            'created_by': board.created_by,
            'access_code': board.access_code,
            'created_at': board.created_at,
            'members': board.members,
            'notes': board.notes,
            'settings': board.settings
        }
        self.dm.save_data(self.boards_file, boards)
        
        return board
    
    def get_board_by_id(self, board_id):
        """Hent tavle ved ID"""
        try:
            boards = self.dm.load_data(self.boards_file)
            if not isinstance(boards, dict):
                print(f"Warning: boards data is not a dict: {type(boards)}")
                return None
            
            if board_id not in boards:
                print(f"Board {board_id} not found in boards: {list(boards.keys())}")
                return None
                
            board_data = boards[board_id]
            board = SharedNoteboard(
                board_data['board_id'],
                board_data['title'],
                board_data['description'],
                board_data['created_by'],
                board_data.get('access_code')
            )
            board.created_at = board_data.get('created_at', datetime.now().isoformat())
            board.members = board_data.get('members', [])
            board.notes = board_data.get('notes', [])
            board.settings = board_data.get('settings', {})
            
            print(f"Successfully loaded board {board_id} with {len(board.notes)} notes")
            return board
        except Exception as e:
            print(f"Error loading board {board_id}: {e}")
            return None
    
    def get_board_by_access_code(self, access_code):
        """Hent tavle ved tilgangskode"""
        boards = self.dm.load_data(self.boards_file)
        for board_data in boards.values():
            if board_data['access_code'] == access_code:
                return self.get_board_by_id(board_data['board_id'])
        return None
    
    def get_user_boards(self, user_email):
        """Hent alle tavler brukeren har tilgang til"""
        boards = self.dm.load_data(self.boards_file)
        # Ensure boards is a dict
        if not isinstance(boards, dict):
            return []
        user_boards = []
        for board_data in boards.values():
            if user_email in board_data.get('members', []):
                board = self.get_board_by_id(board_data['board_id'])
                if board:
                    user_boards.append(board)
        return user_boards
    
    def save_board(self, board):
        """Lagre tavle"""
        boards = self.dm.load_data(self.boards_file)
        boards[board.board_id] = {
            'board_id': board.board_id,
            'title': board.title,
            'description': board.description,
            'created_by': board.created_by,
            'access_code': board.access_code,
            'created_at': board.created_at,
            'members': board.members,
            'notes': board.notes,
            'settings': board.settings
        }
        self.dm.save_data(self.boards_file, boards)
    
    def delete_board(self, board_id, user_email):
        """Slett tavle (kun oppretteren)"""
        board = self.get_board_by_id(board_id)
        if board and board.created_by == user_email:
            boards = self.dm.load_data(self.boards_file)
            if board_id in boards:
                del boards[board_id]
                self.dm.save_data(self.boards_file, boards)
                return True
        return False
    
    def join_board(self, access_code, user_email):
        """Bli med på en tavle ved tilgangskode"""
        board = self.get_board_by_access_code(access_code)
        if board:
            board.add_member(user_email)
            self.save_board(board)
            return board
        return None
    
    def notify_board_update(self, board_id, update_type, updated_by, note_content=None):
        """Send email and push notifications to board members about updates"""
        try:
            from email_service import send_email
            board = self.get_board_by_id(board_id)
            if not board:
                return False
            
            # Get all members except the one who made the update
            recipients = [member for member in board.members if member != updated_by]
            
            if not recipients:
                return True  # No one to notify
            
            # Prepare email content
            subject = f"Oppdatering på tavlen '{board.title}'"
            
            # Send push notifications first (faster)
            try:
                from push_service import send_push_notification
                for recipient in recipients:
                    send_push_notification(
                        user_email=recipient,
                        title=f"📋 {board.title}",
                        body=f"{update_type} av {updated_by.split('@')[0]}",
                        data={
                            'board_id': board_id,
                            'board_title': board.title,
                            'update_type': update_type
                        },
                        dm=self.dm
                    )
            except Exception as e:
                print(f"Failed to send push notifications: {e}")
            
            # Send email notifications
            for recipient in recipients:
                try:
                    email_data = {
                        'recipient': recipient,
                        'subject': subject,
                        'template': 'emails/noteboard_update.html',
                        'context': {
                            'board': board,
                            'update_type': update_type,
                            'updated_by': updated_by,
                            'note_content': note_content,
                            'update_time': datetime.now(),
                            'app_url': 'https://smartremind-production.up.railway.app',
                            'board_url': f'https://smartremind-production.up.railway.app/board/{board.board_id}'
                        }
                    }
                    send_email(email_data)
                except Exception as e:
                    print(f"Failed to send notification to {recipient}: {e}")
                    continue
            
            return True
        except Exception as e:
            print(f"Error sending board update notifications: {e}")
            return False
