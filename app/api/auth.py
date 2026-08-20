from fastapi import APIRouter, HTTPException, Response, Cookie
from typing import NoReturn, Optional

from app.crud.crud_auth import sign_in, sign_out, refresh_session
from app.crud.crud_users import get_user
from app.schemas.auth import Token
from app.core.supabase_retry import NETWORK_ERRORS
import app.core.config as config

router = APIRouter()

NETWORK_UNAVAILABLE_DETAIL = "認証サーバーとの通信に失敗しました。時間をおいて再試行してください。"


def _raise_if_network_error(exc: BaseException) -> NoReturn:
  raise HTTPException(status_code=503, detail=NETWORK_UNAVAILABLE_DETAIL) from exc


def _role_from_access_token(access_token: str) -> str:
  try:
    user_obj = get_user(access_token)
  except NETWORK_ERRORS as e:
    _raise_if_network_error(e)

  if user_obj is None or not hasattr(user_obj, "role"):
    raise HTTPException(status_code=403, detail="User profile or role not found")

  role_val = str(user_obj.role) if user_obj.role is not None else ""
  if not role_val:
    raise HTTPException(status_code=403, detail="User profile or role not found")

  return role_val


@router.post("/login", response_model=Token)
def login(userData: dict, response: Response):
  user_id = str(userData.get("userId"))
  password = str(userData.get("password"))

  email = user_id + config.ADD_EMAIL_ADRESS
  
  try:
    auth_response = sign_in(email, password)
  except NETWORK_ERRORS as e:
    _raise_if_network_error(e)
  except Exception:
    raise HTTPException(status_code = 401, detail = "failed")
  
  if not auth_response.session:
    raise HTTPException(status_code = 401, detail = "session failed")
  
  access_token = auth_response.session.access_token
  role_val = _role_from_access_token(access_token)

  response.set_cookie(
    key="refresh_token",
    value=auth_response.session.refresh_token,
    httponly=True,
    secure=False,  # 本番環境ではTrue TODO
    samesite="lax", 
    max_age=60*60
  )

  return {
    "access_token": access_token,
    "expires_in": auth_response.session.expires_in,
    "token_type": "bearer",
    "role": role_val
  }

@router.post("/refresh", response_model=Token)
def auth_refresh(response: Response, refresh_token: Optional[str] = Cookie(None)):
  if not refresh_token:
    raise HTTPException(status_code=401, detail="Refresh token missing")
  
  try:
    auth_response = refresh_session(refresh_token)
  except NETWORK_ERRORS as e:
    _raise_if_network_error(e)
  except Exception:
    raise HTTPException(status_code=401, detail="Invalid refresh token")

  if not auth_response.session:
    raise HTTPException(status_code=401, detail="Refresh session failed")
  
  access_token = auth_response.session.access_token
  role_val = _role_from_access_token(access_token)

  response.set_cookie(
    key="refresh_token",
    value=auth_response.session.refresh_token,
    httponly=True,
    secure=False,  # 本番環境ではTrue TODO
    samesite="lax", 
    max_age=60*60
  )
  
  return {
    "access_token": access_token,
    "expires_in": auth_response.session.expires_in,
    "token_type": "bearer",
    "role": role_val
  }

@router.post("/logout")
def logout(response: Response):
  response.delete_cookie("refresh_token")
  sign_out()
  return None
