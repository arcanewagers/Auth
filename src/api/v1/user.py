#src\api\v1\user.py
from datetime import datetime,timezone
from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException
from sqlalchemy.orm import Session
from src.api.dependencies import get_current_user, get_db
from src.models.user import User
from src.service.user.schemas import GoogleOAuthPayload, PasswordChangeRequest, PasswordResetConfirm, PasswordResetRequest, UserCreate, UserResponse,UserLogin
from src.service.user.service import PasswordResetService, UserService
from src.utils.exceptions import AuthenticationException, RateLimitException
from src.utils.security.password import hash_password, verify_password

router=APIRouter()

@router.post("/signup",response_model=UserResponse)
def signup(user: UserCreate,background_tasks: BackgroundTasks,db: Session = Depends(get_db)):
    try:
        user_service=UserService(db)
        created_user=user_service.create_user(user)
        # Send verification email in background 
        background_tasks.add_task( 
            # auth_service.send_verification_email,  
            created_user.email 
        ) 
        # Generate tokens for the newly created user
        tokens = user_service.generate_tokens(created_user)
        # Return both user details and tokens
        return{
            "user":created_user,
            "access_token":tokens["access_token"],
        }
    except Exception as e:
        raise HTTPException(status_code=400,detail=str(e))
    
@router.post("/login",response_model=UserResponse)
def login(login_data:UserLogin,db:Session=Depends(get_db)):
    try:
        user_service=UserService(db)
        user=user_service.login(login_data)
        tokens=user_service.generate_tokens(user)
                # Return both user details and tokens
        return {
            "user": user,
            "access_token": tokens["access_token"],
        }
    except RateLimitException as e: 
        raise HTTPException(status_code=429, detail=str(e)) 
    except AuthenticationException as e: 
        raise HTTPException(status_code=401, detail=str(e))
@router.post("/google-login", response_model=UserResponse) 
def google_login(payload: GoogleOAuthPayload, db: Session = Depends(get_db)): 
    try: 
        user_service = UserService(db) 
        user = user_service.google_oauth_login(payload) 
        tokens = user_service.generate_tokens(user) 
        
        # Return both user details and tokens
        return {
            "user": user,
            "access_token": tokens["access_token"],
        }
    except HTTPException as e: 
        raise e 
    except Exception as e: 
        raise HTTPException(status_code=500, detail="Internal Server Error") 

@router.get("/profile", response_model=UserResponse) 
def get_current_user_info(current_user: User = Depends(get_current_user)): 
    return current_user

@router.post("/forgot-password") 
def forgot_password( 
    request: PasswordResetRequest,  
    db: Session = Depends(get_db) 
): 
    try: 
        reset_service = PasswordResetService(db) 
        reset_service.create_password_reset_token(request.email) 
        return {"message": "Password reset link sent to your email"} 
    except AuthenticationException as e: 
        raise HTTPException(status_code=400, detail=str(e)) 
 
@router.post("/reset-password") 
def reset_password( 
    reset_data: PasswordResetConfirm,  
    db: Session = Depends(get_db) 
): 
    try: 
        reset_service = PasswordResetService(db) 
        reset_service.reset_password(reset_data.reset_token, reset_data.new_password) 
        return {"message": "Password successfully reset"} 
    except AuthenticationException as e: 
        raise HTTPException(status_code=400, detail=str(e))