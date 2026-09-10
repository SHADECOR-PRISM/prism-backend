from fastapi import APIRouter, HTTPException, Response, Cookie, Header
from typing import NoReturn, Optional

from app.crud.crud_auth import (
  sign_in,
  sign_out,
  refresh_session,
  check_lockout,
  record_failure,
  reset_attempts,
  MAX_FAILED_ATTEMPTS,
)
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


@router.post("/login", response_model=Token, operation_id="login")
def login(userData: dict, response: Response):
  user_id = str(userData.get("userId"))
  password = str(userData.get("password"))

  # 存在しないuser_idでも同じ経路でロック判定する（ユーザー列挙対策）
  locked_until = check_lockout(user_id)
  if locked_until:
    raise HTTPException(
      status_code=423,
      detail={"message": "locked", "locked_until": locked_until.isoformat()},
    )

  email = user_id + config.ADD_EMAIL_ADRESS

  try:
    auth_response = sign_in(email, password)
  except NETWORK_ERRORS as e:
    _raise_if_network_error(e)
  except Exception:
    failed_count = record_failure(user_id)
    remaining = max(MAX_FAILED_ATTEMPTS - failed_count, 0)
    raise HTTPException(status_code=401, detail={"message": "failed", "remaining_attempts": remaining})

  if not auth_response.session:
    failed_count = record_failure(user_id)
    remaining = max(MAX_FAILED_ATTEMPTS - failed_count, 0)
    raise HTTPException(status_code=401, detail={"message": "session failed", "remaining_attempts": remaining})

  access_token = auth_response.session.access_token
  role_val = _role_from_access_token(access_token)

  reset_attempts(user_id)

  response.set_cookie(
    key="refresh_token",
    value=auth_response.session.refresh_token,
    httponly=True,
    secure=config.COOKIE_SECURE,
    samesite=config.COOKIE_SAMESITE,
    max_age=60*60
  )

  return {
    "access_token": access_token,
    "expires_in": auth_response.session.expires_in,
    "token_type": "bearer",
    "role": role_val
  }

@router.post("/refresh", response_model=Token, operation_id="authRefresh")
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
    secure=config.COOKIE_SECURE,
    samesite=config.COOKIE_SAMESITE,
    max_age=60*60
  )
  
  return {
    "access_token": access_token,
    "expires_in": auth_response.session.expires_in,
    "token_type": "bearer",
    "role": role_val
  }

@router.post("/logout", operation_id="logout")
def logout(response: Response, authorization: Optional[str] = Header(None)):
  access_token = authorization.split(" ", 1)[1] if authorization and authorization.startswith("Bearer ") else None
  response.delete_cookie("refresh_token", secure=config.COOKIE_SECURE, samesite=config.COOKIE_SAMESITE)
  sign_out(access_token)
  return None
