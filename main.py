# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from src.utils.config import settings

from src.database.config import init_database, test_database_connection
from src.routers import user
from src.utils.exceptions import AuthenticationException, RateLimitException, custom_http_exception_handler, custom_validation_exception_handler
from src.utils.security.middleware import authentication_middleware, logging_middleware

logger = logging.getLogger(__name__)

def create_application()->FastAPI:
    """Application factory function"""
    # Create FastAPI app instance
    app = FastAPI(
        title="Arcane Wagers ",
        description="Gaming platform",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc"
    )
    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"],
        max_age=600,
    )
        # Custom middleware
        # In main.py
    app.add_middleware(BaseHTTPMiddleware, dispatch=logging_middleware)
    #app.add_middleware(BaseHTTPMiddleware, dispatch=rate_limit_middleware)
    app.add_middleware(BaseHTTPMiddleware, dispatch=authentication_middleware)
    #app.add_middleware(PasswordChangeMiddleware)

    # Exception handlers
    app.add_exception_handler(HTTPException, custom_http_exception_handler)
    app.add_exception_handler(RequestValidationError, custom_validation_exception_handler)
    app.add_exception_handler(AuthenticationException, custom_http_exception_handler)
    app.add_exception_handler(RateLimitException, custom_http_exception_handler)

    # Include routers
    app.include_router(user.router, prefix="/api/v1/auth", tags=["Authentication"])

    @app.get("/health")
    async def health_check():
        """Health check endpoint with database connection status"""
        db_status = "healthy" if test_database_connection() else "unhealthy"
        return {
            "status": "healthy",
            "database": db_status
        }

    return app
# Create application
app = create_application()

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        # Initialize database
        init_database()
        
        # Test database connection
        if not test_database_connection():
            logger.error("Failed to connect to database during startup")
            raise Exception("Database connection failed")
            
        logger.info("Application startup complete")
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    try:
        # Add any cleanup tasks here
        logger.info("Application shutdown complete")
    except Exception as e:
        logger.error(f"Application shutdown failed: {e}")
        raise

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )



