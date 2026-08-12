from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from uuid import UUID
from app.api.deps import get_current_user
from app.crud.crud_container import get_user_container
from app.crud.crud_container_detail import get_container_detail_by_id 
from app.schemas.accounting import (
    Container, 
    ApplicationCreateRequest, 
    ApplicationCreateResponse,
    ContainerDetailResponse  
)
from app.models.models import Users
from app.crud.crud_accounting import create_application
from app.core.date_formatter import parse_iso_date_to_string

router = APIRouter()

# ==========================================
# 【GET】コンテナ一覧取得エンドポイント (logページ)
# ==========================================
@router.get("/container/me", response_model=list[Container])
def get_container_me(
    start: datetime, 
    end: datetime, 
    offset: int, 
    current_user: Users = Depends(get_current_user)
):
    try:
        start_naive = start.replace(tzinfo=None) if start.tzinfo else start
        end_naive = end.replace(tzinfo=None) if end.tzinfo else end

        # CRUD 側で Supabase の select("*, projects(name)") により一括取得（N+1解消）
        containers = get_user_container(str(current_user.id), start_naive, end_naive, offset)

        result = []
        for container in containers:
            # 日付フォーマットの型ガード (ステップ2)
            applied_at_raw = container.get("applied_at")
            if isinstance(applied_at_raw, datetime):
                formatted_date = applied_at_raw.strftime("%Y-%m-%dT%H:%M:%S")
            elif isinstance(applied_at_raw, str) and applied_at_raw:
                formatted_date = parse_iso_date_to_string(applied_at_raw)
            else:
                formatted_date = ""

            result.append({
                "id": container.get("id"),
                "user_id": current_user.user_id,
                "project_name": container.get("project_name", "未設定"),
                "category": container.get("category"),
                "applied_at": formatted_date,
                "status": container.get("status"),
                "total_amount": container.get("total_amount", 0)
            })

        return result

    except HTTPException:
        # 明示的なHTTPエラーはそのままスルー 
        raise
    except Exception as e:
        print(f"get_container_me Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"一覧データの取得に失敗しました: {str(e)}"
        )


# ==========================================
# 【POST】新規申請登録用エンドポイント
# ==========================================
@router.post("/accounting/requests", response_model=ApplicationCreateResponse, status_code=status.HTTP_201_CREATED)
def create_new_application(
    request_data: ApplicationCreateRequest,
    current_user: Users = Depends(get_current_user)
):
    try:
        result = create_application(
            user_db_id=str(current_user.id),
            request_data=request_data
        )
        return result

    except HTTPException:
        # 明示的な 404 等のエラーは上書きせずスルー 
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        print(f"create_new_application Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"申請の登録処理に失敗しました: {str(e)}"
        )


# ==========================================
# 【GET】コンテナ詳細取得エンドポイント (logDetailページ)
# ==========================================
@router.get("/container/{container_id}", response_model=ContainerDetailResponse)
def get_container_detail(
    container_id: UUID,
    current_user: Users = Depends(get_current_user)
):
    try:
        # ログインユーザーの user_db_id を渡して CRUD 側で所有者チェックを行う
        result = get_container_detail_by_id(
            container_id=str(container_id),
            user_db_id=str(current_user.id),
            user_public_id=str(current_user.user_id)  
        )

        if not result:
            # 他人の container_id を指定された場合、404 を返す
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された申請コンテナが見つかりません"
            )

        return result

    except HTTPException:
        # 明示的な 404 等のエラーは上書きせずスルー 
        raise
    except Exception as e:
        print(f"get_container_detail Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"詳細データの取得処理に失敗しました: {str(e)}"
        )