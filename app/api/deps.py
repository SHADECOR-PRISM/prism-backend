from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from app.crud.crud_users import get_user
from app.models.models import Users
from app.core.supabase_retry import NETWORK_ERRORS

__all__ = ["get_current_user"]

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login")


def get_current_user(token: str = Depends(reusable_oauth2)) -> Users:
    """
    ログイン中のユーザーを取得する依存関数。
    - トークン無効 / ユーザー未存在: 401
    - Supabase との通信障害（リトライ後も失敗）: 503
    """
    try:
        user = get_user(token)

        if user is None:
            raise HTTPException(
                status_code=401,
                detail="無効な認証トークンです。",
            )

        return user

    except NETWORK_ERRORS as e:
        print(f"[get_current_user] Network Error after retry: {e}")
        raise HTTPException(
            status_code=503,
            detail="認証サーバーとの通信に失敗しました。時間をおいて再試行してください。",
        ) from e
