#src/models/user.py

from sqlalchemy import Column, DateTime, String, Boolean, Enum as SQLAEnum, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSON
import uuid
from datetime import datetime, timezone
from models.base_model import BaseModel
from src.service.user.entites import UserStatus

class User(BaseModel):
    """User model representing application users with all their attributes and relationships"""
    __tablename__="users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, nullable=False, index=True)
    password = Column(String)
    username = Column(String)
    is_active = Column(Boolean, default=True)
    status = Column(SQLAEnum(UserStatus), default=UserStatus.ACTIVE)
    last_login = Column(DateTime(timezone=True), nullable=True)
    requires_password_change = Column(Boolean, default=False)
    last_password_change = Column(DateTime(timezone=True), nullable=True)
    password_change_required_by = Column(DateTime(timezone=True), nullable=True)
    failed_login_attempts = Column(Integer, default=0)
    last_failed_login = Column(DateTime(timezone=True), nullable=True)
    profile_image_url = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), default=datetime.now)
    updated_at = Column(DateTime(timezone=True), default=datetime.now, onupdate=datetime.now)
    google_id = Column(String, unique=True, nullable=True)
    password_reset_token = Column(String, nullable=True)
    password_reset_expires = Column(DateTime(timezone=True), nullable=True)
    login_attempts=relationship("LoginAttempt",back_populates="user")
    

    def record_failed_login(self):
        """Record a failed login attempt"""
        self.failed_login_attempts += 1
        self.last_failed_login = datetime.now(timezone.utc)
        
    def reset_failed_logins(self):
        """Reset failed login counter"""
        self.failed_login_attempts = 0
        self.last_failed_login = None
    


class LoginAttempt(BaseModel):
    """Model for tracking user login attempts"""
    __tablename__ = "login_attempts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'), nullable=False)
    success = Column(Boolean, nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="login_attempts")