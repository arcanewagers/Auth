#src\api\v1\user.py
from datetime import datetime,timezone
from fastapi import APIRouter,BackgroundTasks,Depends,HTTPException
from sqlalchemy.orm import Session
from src.api.dependencies import get_db
from src.service.user.schemas import UserCreate, UserResponse
from src.service.user.service import UserService

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