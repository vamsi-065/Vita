from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import timedelta
from jose import JWTError, jwt

from app.core.database import get_db
from app.core.security import verify_password, create_access_token, SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
from app.crud import user as crud_user
from app.schemas import user as schema_user

router = APIRouter()
security = HTTPBearer(auto_error=False)

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, email="open@business.os")
    if user is None:
        from app.schemas.user import UserCreate
        user_in = UserCreate(
            email="open@business.os",
            password="defaultpassword",
            full_name="Open User",
            business_name="AI Business OS"
        )
        user = crud_user.create_user(db=db, user=user_in)
    return user

@router.post("/signup", response_model=schema_user.AuthResponse, status_code=201)
def signup(user_in: schema_user.UserCreate, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = crud_user.create_user(db=db, user=user_in)
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.post("/login", response_model=schema_user.AuthResponse)
def login(form_data: schema_user.LoginRequest, db: Session = Depends(get_db)):
    user = crud_user.get_user_by_email(db, email=form_data.email)
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.id})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

@router.get("/me", response_model=schema_user.UserResponse)
def read_users_me(current_user: schema_user.UserResponse = Depends(get_current_user)):
    return current_user
