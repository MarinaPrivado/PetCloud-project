from datetime import datetime
import hashlib
from typing import Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.User import User
from config.database import SessionLocal

class AuthService:
    def __init__(self):
        self.db = SessionLocal()

    def _hash_password(self, password: str) -> str:
        """Hash a password for secure storage"""
        return hashlib.sha256(password.encode()).hexdigest()

    def register(self, name: str, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Register a new user
        Returns: (success, message, user)
        """
        try:
            hashed_password = self._hash_password(password)
            new_user = User(
                name=name,
                email=email,
                password=hashed_password
            )
            
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)
            
            return True, "Usuário registrado com sucesso!", new_user
            
        except IntegrityError:
            self.db.rollback()
            return False, "Email já cadastrado.", None
        except Exception as e:
            self.db.rollback()
            return False, f"Erro ao registrar usuário: {str(e)}", None

    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[User]]:
        """
        Authenticate a user
        Returns: (success, message, user)
        """
        try:
            hashed_password = self._hash_password(password)
            user = self.db.query(User).filter(User.email == email).first()
            
            if not user:
                return False, "Usuário não encontrado.", None
                
            if user.password != hashed_password:
                return False, "Senha incorreta.", None
                
            return True, "Login realizado com sucesso!", user
            
        except Exception as e:
            return False, f"Erro ao autenticar: {str(e)}", None

    def change_password(self, email: str, current_password: str, new_password: str) -> Tuple[bool, str]:
        """Change user password"""
        success, message, user = self.login(email, current_password)
        
        if not success:
            return False, "Senha atual incorreta."
            
        try:
            user.password = self._hash_password(new_password)
            self.db.commit()
            return True, "Senha alterada com sucesso!"
        except Exception as e:
            self.db.rollback()
            return False, f"Erro ao alterar senha: {str(e)}"
        # 1. Generate reset token
        # 2. Save token with expiration
        # 3. Send reset email
        # 4. Create endpoint to verify token and set new password

        temp_password = secrets.token_urlsafe(8)
        user.change_password(temp_password)
        
        return temp_password  # In production, don't return password, send via email

    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.users.get(email)

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        for user in self.users.values():
            if user.id == user_id:
                return user
        return None