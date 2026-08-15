from pydantic import BaseModel
from typing import Literal, Optional
from uuid import UUID

# 個別ユーザ情報取得用スキーマ
class UserProfile(BaseModel):
    user_id: str
    user_name: str
    account_type: Literal["Admin", "General"]
    current_date: str

# 管理者用 ユーザー一覧取得レスポンススキーマ
class AdminUserItem(BaseModel):
    id: UUID
    user_id: str
    name: Optional[str] = ""
    role: str