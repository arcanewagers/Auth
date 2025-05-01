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
class UserNotFoundException(Exception):
    """Custom exception for User  errors"""
    pass
class EmailAlreadyInUseException(Exception):
    """Custom exception for Email errors"""
    pass
class RateLimitException(ArcaneBaseException):
    """Raised when rate limit is exceeded"""
    def __init__(self, message: str = "Rate limit exceeded"):
        self.message = message
        super().__init__(self.message)


def custom_http_exception_handler(request: Request, exc: HTTPException):
    """
    Custom handler for HTTP exceptions
    """
    logging.error(f"HTTP Error: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": "error",
            "message": exc.detail
        }
    )

def custom_validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Custom handler for validation errors
    """
    errors = exc.errors()
    error_details = [
        {
            "loc": error["loc"],
            "msg": error["msg"],
            "type": error["type"]
        } for error in errors
    ]
    
    logging.error(f"Validation Error: {error_details}")
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "error",
            "message": "Validation error",
            "errors": error_details
        }
    )