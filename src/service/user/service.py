from datetime import datetime, timedelta, timezone
import secrets
from typing import Optional
import base64
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException
from src.models.user import LoginAttempt, User
from src.service.user.entites import UserStatus
from src.service.user.schemas import GoogleOAuthPayload, UserCreate,UserProfileUpdate,UserLogin
from src.utils.email_service import EmailService
from src.utils.exceptions import AuthenticationException, EmailAlreadyInUseException, RateLimitException, UserNotFoundException
from src.utils.security.password import hash_password, verify_password
from src.utils.security.token import create_access_token, create_password_reset_jwt, verify_google_oauth_token, verify_password_reset_token
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
    """USER LOGIN"""
    def login(self,login_data:UserLogin)->User:
        user=self.db.query(User).filter(User.email==login_data.email).first()

        if not user:
            raise AuthenticationException("invalid credentials")
        
        # Check login attempt limits
        self._check_login_attempts(user)
        
        if not verify_password(login_data.password, user.password):
            # Record failed attempt
            self._record_login_attempt(user, success=False)
            raise AuthenticationException("Invalid credentials")
        
        # Record successful login
        self._record_login_attempt(user, success=True)
        
        if user.status != UserStatus.ACTIVE:
            raise AuthenticationException("User account is not active")
        
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

class PasswordResetService:
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()

    def create_password_reset_token(self, email: str) -> str:
        user = self.db.query(User).filter(User.email == email).first()
        if not user:
            raise AuthenticationException("User not found")

        # Generate a JWT specifically for password reset
        reset_token = create_password_reset_jwt(user.id)
        
        # Store token details in the database
        user.password_reset_token = reset_token
        user.password_reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        self.db.commit()

        self.email_service.send_password_reset_email(user.email, reset_token)
        return reset_token
    def reset_password(self, reset_token: str, new_password: str):
        try:
            # Verify the password reset JWT
            payload = verify_password_reset_token(reset_token)
            
            user = self.db.query(User).filter(User.id == payload['user_id']).first()
            if not user:
                raise AuthenticationException("User not found")

            # Additional checks can be added here, like checking if the token is still valid in the database

            # Validate new password complexity
            if len(new_password) < 8:
                raise AuthenticationException("Password must be at least 8 characters long")

            # Hash new password
            hashed_password = hash_password(new_password)
            
            # Update user's password and clear reset token
            user.password = hashed_password
            user.password_reset_token = None
            user.password_reset_expires = None
            
            self.db.commit()

            # Optionally, send a notification email
            self.email_service.send_email(
                user.email, 
                "Password Changed", 
                "Your password has been successfully reset."
            )

        except Exception as e:
            raise AuthenticationException("Invalid or expired reset token")
    
    

    