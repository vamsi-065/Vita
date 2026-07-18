from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.v1.endpoints.auth import get_current_user
from app.models.profile import Profile
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ProfileUpdate(BaseModel):
    phone_number: Optional[str] = None

class ProfileResponse(BaseModel):
    id: str
    email: Optional[str]
    phone_number: Optional[str]
    telegram_chat_id: Optional[str]

    class Config:
        orm_mode = True

@router.get("", response_model=ProfileResponse)
def get_profile(current_user: dict = Depends(get_current_user), db: Session = Depends(get_db)):
    user_id = current_user.get("id")
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        # Create profile if it doesn't exist
        profile = Profile(
            id=user_id,
            email=current_user.get("email")
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
        
    return profile

@router.put("", response_model=ProfileResponse)
def update_profile(
    profile_data: ProfileUpdate, 
    current_user: dict = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    user_id = current_user.get("id")
    profile = db.query(Profile).filter(Profile.id == user_id).first()
    
    if not profile:
        profile = Profile(
            id=user_id,
            email=current_user.get("email")
        )
        db.add(profile)
        
    if profile_data.phone_number is not None:
        profile.phone_number = profile_data.phone_number
        
    try:
        db.commit()
        db.refresh(profile)
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail="Error updating profile. Phone number may already be in use.")
        
    return profile
