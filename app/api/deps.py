from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
import httpx
import time
from app.crud.crud_users import get_user
from app.models.models import Users

__all__ = ["get_current_user"]

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl="/login")

NETWORK_ERRORS = (
    httpx.HTTPError,
)


def get_current_user(token: str = Depends(reusable_oauth2)) -> Users:
    """
    ログイン中のユーザーを取得する依存関数。
    - ネットワーク通信障害 (NETWORK_ERRORS): 最大3回自動リトライ
    - トークン無効 / ユーザー未存在 (None): 即時 401 Unauthorized を返却
    """
    max_retries = 3

    for attempt in range(max_retries):
        try:
            user = get_user(token)

            # トークン無効またはユーザーが存在しない場合（リトライせず即時 401）
            if user is None:
                raise HTTPException(
                    status_code=401, 
                    detail="無効な認証トークンです。"
                )

            return user

        except NETWORK_ERRORS as e:
            # ネットワーク接続切れ・コネクション破綻時のみリトライ実行
            print(f"[get_current_user Retry {attempt + 1}/{max_retries}] Network Error: {e}")
            
            if attempt == max_retries - 1:
                raise HTTPException(
                    status_code=401, 
                    detail="認証サーバーとの通信に失敗しました。時間をおいて再試行してください。"
                )
            
            time.sleep(0.1)

        except HTTPException:
            # 意図的に投げた 401 エラーはそのまま上位（FastAPI）に流す
            raise

    # Pylance に対して「全ループ終了時は必ず例外が発生し None は返らない」ことを保障
    raise HTTPException(
        status_code=401,
        detail="認証処理を実行できませんでした。"
    )