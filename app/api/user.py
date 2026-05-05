from fastapi import APIRouter, Depends
from datetime import datetime
from app.api.deps import get_current_user
from app.schemas.user import UserProfile
from app.models.models import Users

router = APIRouter()

@router.get("/users/me", response_model=UserProfile)
async def get_me(current_user: Users = Depends(get_current_user)):
    return {
        "user_id": current_user.user_id,
        "user_name": current_user.name,
        "account_type": current_user.role.capitalize(), 
        "current_date": datetime.now().strftime("%Y/%m/%d")
    }