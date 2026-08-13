from typing import cast, Dict, Any, Optional
from postgrest.exceptions import APIError
from supabase_auth.errors import AuthApiError

from app.db.session import supabase
from app.models.models import Users


def get_user(token: str) -> Optional[Users]:
    """
    トークンを用いてユーザー情報を取得する。
    - 無効なトークン / ユーザー不在 (AuthApiError / APIError): None を返却
    - 通信障害 / ネットワーク切断: 上位 (deps.py) へスルーしてリトライさせる
    """
    try:
        # 1. Supabase Auth で JWT トークン検証
        auth_response = supabase.auth.get_user(token)
        if not auth_response or not getattr(auth_response, "user", None):
            return None

        # 2. DB (usersテーブル) からユーザー情報取得
        users_response = (
            supabase.table("users")
            .select("*")
            .eq("id", auth_response.user.id)
            .single()
            .execute()
        )

        if not users_response or not getattr(users_response, "data", None):
            return None

        return Users(**cast(Dict[str, Any], users_response.data))

    except (AuthApiError, APIError) as e:
        # Supabase APIレベルの認証失敗・データ未存在エラーのみを捕捉して None 化
        print(f"[get_user] Supabase API Error: {e}")
        return None