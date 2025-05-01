# src/utils/security/token.py
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional
from jose import jwt
from google.oauth2 import id_token
from google.auth.transport import requests
import logging
from src.utils.exceptions import AuthenticationException
from src.utils.config import settings

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_access_token(user_id:int,expires_delta:Optional[timedelta]=None)->str:
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM

    if expires_delta is None:
        expires_delta=timedelta(days=2)

    to_encode={
        "sub":str(user_id),
        "exp": datetime.now(timezone.utc)+  expires_delta
    }
    encoded_jwt=jwt.encode(to_encode,SECRET_KEY,algorithm=ALGORITHM)
    return encoded_jwt

def verify_access_token(token:str)->Dict[str,Any]:
    try:
        logger.info(f"Attempting to verify token: {token[:10]}...")
        payload=jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        logger.info("Token Sucessfully decoded")
        return payload
    except jwt.JwtError as e:
        logger.error(f"JWT Error during token verification: {e}")
        logger.error(f"Token details - Secret Key Length: {len(settings.SECRET_KEY)}, Algorithm: {settings.ALGORITHM}")
        raise AuthenticationException("Could not validate credentials")
def verify_google_oauth_token(token: str) -> Dict[str, str]:
    try:
        id_info = id_token.verify_oauth2_token(
            token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        if id_info['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            raise ValueError('Wrong issuer.')
        
        return id_info
    except ValueError:
        raise AuthenticationException("Invalid Google OAuth token")

def create_password_reset_jwt(user_id: int) -> str:
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM
    expires_delta = timedelta(minutes=settings.PASSWORD_RESET_TOKEN_EXPIRE)
    
    to_encode = {
        "sub": "password_reset",
        "user_id": user_id,
        "exp": datetime.now(timezone.utc) + expires_delta
    }
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_password_reset_token(token: str) -> Dict[str, Any]:
    try:
        payload = jwt.decode(
            token, 
            settings.SECRET_KEY, 
            algorithms=settings.ALGORITHM
        )
        
        if payload.get('sub') != 'password_reset':
            raise AuthenticationException("Invalid token type")
        
        return payload
    except jwt.JWTError:
        raise AuthenticationException("Invalid or expired reset token")

    
