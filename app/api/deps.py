from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.crud.crud_users import get_user

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="api/login")

def get_current_user(token: str = Depends(reusable_oauth2)):
    user_response = get_user(token)

    if not user_response:
        raise HTTPException(status_code = 401, detail = "User response failed")
    
    return user_response