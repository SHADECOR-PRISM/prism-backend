from fastapi import APIRouter, HTTPException
from app.crud.crud_auth import sign_in

import app.core.config as config

router = APIRouter()

@router.post("/login")
def login(userData: dict):
  user_id = str(userData.get("userId"))
  password = str(userData.get("password"))

  email = user_id + config.ADD_EMAIL_ADRESS
  
  try:
    response = sign_in(email, password)
  except Exception:
    raise HTTPException(status_code = 401, detail = "failed")
  
  if not response.session:
    raise HTTPException(status_code = 401, detail = "session failed")
  
  return {
    "access_token": response.session.access_token,
    "refresh_token": response.session.refresh_token,
    "expires_in": response.session.expires_in,
    "token_type": "bearer"
  }

