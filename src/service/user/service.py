from datetime import datetime, timedelta, timezone
import secrets
from typing import Optional
import base64
from sqlalchemy import UUID
from sqlalchemy.orm import Session
from fastapi import HTTPException

class UserService:
    def __init__(self,db:Session):
        self.db=db
        