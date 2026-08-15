from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from app.api.deps import get_current_user
from app.schemas.user import UserProfile, AdminUserItem
from app.models.models import Users
from app.crud.crud_users import get_all_users

router = APIRouter()


@router.get("/users/me", response_model=UserProfile)
def get_me(current_user: Users = Depends(get_current_user)):
    """
    ログイン中のユーザープロフィール情報を取得するエンドポイント
    """
    try:
        raw_role = getattr(current_user, "role", "general")
        role_str = str(raw_role) if raw_role is not None else "general"

        return {
            "user_id": current_user.user_id,
            "user_name": current_user.name,
            "account_type": role_str.capitalize(),  # 'Admin' または 'General'
            "current_date": datetime.now().strftime("%Y/%m/%d")
        }
    except Exception as e:
        print(f"get_me Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー情報の取得に失敗しました: {str(e)}"
        )
    

@router.get("/admin/users", response_model=list[AdminUserItem])
def get_admin_users(current_user: Users = Depends(get_current_user)):
    """
    【管理者用】登録ユーザー一覧を取得するエンドポイント
    """
    raw_role = getattr(current_user, "role", "general")
    if str(raw_role).lower() != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="管理者権限が必要です"
        )

    try:
        users = get_all_users()
        return users
    except Exception as e:
        print(f"get_admin_users Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー一覧の取得に失敗しました: {str(e)}"
        )