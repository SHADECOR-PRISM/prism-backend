from fastapi import APIRouter, HTTPException, Response, Cookie
from typing import Optional

from app.crud.crud_auth import sign_in, sign_out, refresh_session
from app.schemas.auth import Token
import app.core.config as config

router = APIRouter()

@router.post("/login", response_model=Token)
def login(userData: dict, response: Response):
  user_id = str(userData.get("userId"))
  password = str(userData.get("password"))

  email = user_id + config.ADD_EMAIL_ADRESS
  
  try:
    auth_response = sign_in(email, password)
  except Exception:
    raise HTTPException(status_code = 401, detail = "failed")
  
  if not auth_response.session:
    raise HTTPException(status_code = 401, detail = "session failed")
  
  response.set_cookie(
    key="refresh_token",
    value=auth_response.session.refresh_token,
    httponly=True,
    secure=False,  #本番環境ではTrue TODO
    samesite="lax", 
    max_age=60*60
  )

  return {
    "access_token": auth_response.session.access_token,
    "expires_in": auth_response.session.expires_in,
    "token_type": "bearer"
  }

@router.post("/refresh", response_model=Token)
def auth_refresh(response: Response, refresh_token: Optional[str] = Cookie(None)):
  if not refresh_token:
    raise HTTPException(status_code=401, detail="Refresh token missing")
  
  try:
    auth_response = refresh_session(refresh_token)
  except:
    raise HTTPException(status_code=401, detail="Invalid refresh token")

  if not auth_response.session:
    raise HTTPException(status_code=401, detail="Refresh session failed")
  
  response.set_cookie(
    key="refresh_token",
    value=auth_response.session.refresh_token,
    httponly=True,
    secure=False,  #本番環境ではTrue TODO
    samesite="lax", 
    max_age=60*60
  )
  
  return {
    "access_token": auth_response.session.access_token,
    "expires_in": auth_response.session.expires_in,
    "token_type": "bearer"
  }


  

@router.post("/logout")
def logout(response: Response):
  response.delete_cookie("refresh_token")
  sign_out()
  return None

