from datetime import datetime, timedelta, timezone
import secrets
from typing import Optional
import base64
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.user import LoginAttempt, User
from src.service.user.schemas import GoogleOAuthPayload, UserCreate,UserProfileUpdate
from src.utils.email_service import EmailService
from src.utils.exceptions import AuthenticationException, EmailAlreadyInUseException, RateLimitException, UserNotFoundException
from src.utils.security.password import hash_password
from src.utils.security.token import create_access_token, verify_google_oauth_token
from src.utils.config import settings
class UserService:
    def __init__(self,db:Session):
        self.db=db
        self.email_service=EmailService()


        """CREATING NEW USER"""
    def create_user(self,user_data:UserCreate)->User:
        #Check is user exist
        existing_user=self.db.query(User).filter(User.email==user_data.email).first()
        if existing_user:
            raise AuthenticationException("User already Exist")
        
        #Hash password
        password=hash_password(user_data.password)

        # Create new User
        new_user=User(
            email=user_data.email,
            password=password,
            username=user_data.username
        )
        self.db.add(new_user)
        self.db.commit()
        self.db.refresh(new_user)
        
        return new_user
    
    """UPDATE USER"""
    def update_user(self,user_id:UUID,user_data:UserProfileUpdate)->User:
        """Update user profile ."""
        user=self.db.query(User).filter(User.id==user_id).first()
        if not user:
            raise UserNotFoundException("User not found")
        # Update email if provided and changed
        if user_data.email is not None and user_data.email != user.email:
            existing_user=self.db.query(User).filter(
                User.email==user_data.email,
                User.id != user_id
            ).first()
            if existing_user:
                raise EmailAlreadyInUseException("Email already in use")
            user.email = user_data.email

            # Update full name is provided
            if user_data.username is not None:
                user.username = user_data.username
            
        # Update timestamp
        user.updated_at = datetime.now(timezone.utc)
        # Commit changes
        self.db.commit()
        self.db.refresh(user)
        return user
    
    """ GENERATE TOKEN """
    def generate_tokens(self, user: User):
        access_token = create_access_token(user.id)
        return {
            "access_token": access_token,
            "token_type": "bearer"
        }
    
    """ GOGGLE AUTHENTICATION"""
    def google_oauth_login(self, oauth_payload: GoogleOAuthPayload) -> User:
        # Verify Google OAuth token
        google_user_info = verify_google_oauth_token(oauth_payload.token)
        
        # Check if user exists
        user = self.db.query(User).filter(User.google_id == google_user_info['sub']).first()
        
        if not user:
            # Create new user if not exists
            user = User(
                email=google_user_info['email'],
                google_id=google_user_info['sub'],
                username=google_user_info.get('name'),
        
            )
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    """RECORD LOGIN"""
    def _record_login_attempt(self, user: User, success: bool):
        """
        Record login attempt for security tracking
        """
        login_attempt = LoginAttempt(
            user_id=user.id,
            success=success,
            timestamp=datetime.now(timezone.utc)
        )
        self.db.add(login_attempt)
        self.db.commit()

    """CHECK LOGIN"""
    def _check_login_attempts(self, user: User):
        """
        Check and prevent brute force login attempts
        """
        # Get login attempts in the last X minutes
        current_time = datetime.now(timezone.utc)
        recent_attempts = self.db.query(LoginAttempt).filter(
            LoginAttempt.user_id == user.id,
            LoginAttempt.timestamp > current_time - timedelta(minutes=settings.LOGIN_ATTEMPT_WINDOW)
        ).count()

        if recent_attempts >= settings.MAX_LOGIN_ATTEMPTS:
            raise RateLimitException("Too many login attempts. Please try again later.")    


    