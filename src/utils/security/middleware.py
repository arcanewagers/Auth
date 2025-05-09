
from starlette.middleware.base import RequestResponseEndpoint, BaseHTTPMiddleware
from starlette.responses import JSONResponse
from starlette.types import ASGIApp
import time
import logging
import traceback
import re
from fastapi import Request, HTTPException

from src.utils.security.token import verify_access_token

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)
class CustomMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope, receive, send):
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            logger.error(f"Unhandled middleware error: {e}")
            logger.error(traceback.format_exc())
            # Fallback error response
            await send({
                'type': 'http.response.start',
                'status': 500,
                'headers': [(b'content-type', b'application/json')]
            })
            await send({
                'type': 'http.response.body',
                'body': b'{"detail": "Internal Server Error"}'
            })

async def logging_middleware(request: Request, call_next: RequestResponseEndpoint):
    start_time = time.time()
    
    try:
        logger.info(f"Request: {request.method} {request.url}")
        response = await call_next(request)
        
        process_time = time.time() - start_time
        logger.info(f"Response time: {process_time:.4f} seconds")
        
        return response
    except Exception as e:
        logger.error(f"Logging middleware error: {e}")
        raise
async def authentication_middleware(request: Request, call_next: RequestResponseEndpoint):
    """
    Middleware for authentication checks.
    Uses regex patterns to determine which paths should be excluded.
    """
    # Skip authentication for OPTIONS requests
    if request.method == "OPTIONS":
        return await call_next(request)
    
    # Define regex patterns for paths to exclude from authentication
    excluded_patterns = [
        re.compile(r"^/api/v1/auth/(login|signup|profile|forgot-password|reset-password|google-login)$"),
        re.compile(r"^/health$"),
        re.compile(r"^/docs$"),
        re.compile(r"^/openapi\.json$")
    ]
    
    path = request.url.path
    logger.debug(f"Checking path for exclusion: {path}")
    
    if any(pattern.match(path) for pattern in excluded_patterns):
        logger.info(f"Authentication skipped for path: {path}")
        return await call_next(request)
    
    # Check for Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.error(f"Authorization header missing for path: {path}")
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Validate token (adjust this implementation to your auth system)
    try:
        token = auth_header.split(" ")[-1] if "Bearer" in auth_header else auth_header
        decoded_token = verify_access_token(token)
        if decoded_token is None:
            logger.error(f"Invalid or expired token for path: {path}")
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        request.state.user = decoded_token
    except HTTPException:
        raise  # Re-raise HTTPException
    except Exception as e:
        logger.error(f"Unexpected token validation error for path {path}: {str(e)}")
        raise HTTPException(status_code=401, detail="Authentication failed")
    
    try:
        return await call_next(request)
    except Exception as e:
        logger.error(f"Authentication middleware error: {e}")
        raise
