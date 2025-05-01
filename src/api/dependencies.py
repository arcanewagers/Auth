from uuid import UUID
from fastapi import Depends, HTTPException,status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from src.database.base import SessionLocal
from src.models.user import User
from src.utils.exceptions import AuthenticationException
from src.utils.security.token import verify_access_token, verify_google_oauth_token


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    
    try:
        # Try JWT first
        token_data = verify_access_token(token)
        
        # Convert string to UUID if necessary
        try:
            user_id = token_data['sub'] if isinstance(token_data['sub'], UUID) else UUID(token_data['sub'])
            user = db.query(User).filter(User.id == user_id).first()
        except (ValueError, TypeError):
            raise credentials_exception
            
        if not user:
            raise credentials_exception
        
        return user
        
    except AuthenticationException:
        # If JWT fails, try Google OAuth
        try:
            google_token_data = verify_google_oauth_token(token)
            user = db.query(User).filter(User.email == google_token_data['email']).first()
            
            if not user:
                raise credentials_exception
            
            return user
            
        except AuthenticationException:
            raise credentials_exception