from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from app.api.deps import get_current_user
from app.crud.crud_container import get_user_container
from app.crud.crud_projects import get_project
from app.schemas.accounting import (
    Container, 
    ApplicationCreateRequest, 
    ApplicationCreateResponse
)
from app.models.models import Users
from app.crud.crud_accounting import create_application

router = APIRouter()

# ==========================================
# 既存コード（読み出し用GETエンドポイント）
# ==========================================
@router.get("/container/me", response_model = list[Container])
async def get_container_me(start: datetime, end: datetime, offset: int, current_user: Users = Depends(get_current_user)):
    containers = get_user_container(current_user.id, start, end, offset)

    return [{
        "id": container.id,
        "user_id": current_user.user_id,
        "project_name": get_project(container.project_id).name,
        "category": container.category,
        "applied_at": datetime.fromisoformat(container.applied_at).strftime("%Y/%m/%d"),
        "status": container.status,
        "total_amount": container.total_amount
    } for container in containers]


# ==========================================
# 【新規追加】新規申請登録用POSTエンドポイント
# ==========================================
@router.post("/accounting/requests", response_model=ApplicationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_new_application(
    request_data: ApplicationCreateRequest,
    current_user: Users = Depends(get_current_user)
):
    # 交通費または一般経費の新規申請を一括登録
    try:
        result = create_application(
            user_db_id=str(current_user.id),
            request_data=request_data
        )
        return result

    except ValueError as e:
        # 明細未追加などの入力バリデーションエラー
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        # DB接続や予期せぬサーバーエラー
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"申請の登録処理に失敗しました: {str(e)}"
        )