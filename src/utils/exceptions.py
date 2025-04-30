import logging
from fastapi import HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

class ArcaneBaseException(Exception):
    """Base exception for all Arcane warger application errors"""
    pass
class AuthenticationException(ArcaneBaseException):
    "authentication related errors"
    def __init__(self, message:str="Authentication failed"):
        self.message=message
        super().__init__(self.message)