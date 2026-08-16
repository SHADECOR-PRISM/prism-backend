from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime
from uuid import UUID
from typing import List
from app.api.deps import get_current_user
from app.crud.crud_container import get_user_container, get_all_containers  
from app.crud.crud_container_detail import get_container_detail_by_id, get_admin_container_detail_by_id, get_bulk_admin_container_details
from app.crud.crud_accounting import create_application, update_application, update_application_approval  
from app.crud.crud_analytics import get_analytics_summary
from app.schemas.accounting import (
    Container, 
    ApplicationCreateRequest, 
    ApplicationCreateResponse,
    ContainerDetailResponse,
    ApplicationUpdateRequest,     
    ApplicationUpdateResponse,
    ApplicationApprovalRequest,
    AnalyticsSummaryResponse,
    BulkContainerDetailsRequest   
)
from app.models.models import Users
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
# 【PUT】既存申請の更新・追記・削除用エンドポイント 
# ==========================================
@router.put("/accounting/requests", response_model=ApplicationUpdateResponse)
def update_existing_application(
    request_data: ApplicationUpdateRequest,
    current_user: Users = Depends(get_current_user)
):
    try:
        success, message = update_application(payload=request_data)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return ApplicationUpdateResponse(
            success=True,
            message=message
        )

    except HTTPException:
        # 明示的な 400 や 404 等のエラーはスルー
        raise
    except Exception as e:
        print(f"update_existing_application Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"申請の更新処理に失敗しました: {str(e)}"
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



# ==========================================
# 【GET】全ユーザーコンテナ一覧取得エンドポイント (管理者用 approvalページ) 
# ==========================================
@router.get("/admin/container/all", response_model=list[Container])
def get_container_all(
    start: datetime, 
    end: datetime, 
    offset: int, 
    current_user: Users = Depends(get_current_user)
):
    try:
        start_naive = start.replace(tzinfo=None) if start.tzinfo else start
        end_naive = end.replace(tzinfo=None) if end.tzinfo else end

        # 全ユーザーのコンテナ一覧を CRUD 経由で取得
        containers = get_all_containers(start_naive, end_naive, offset)

        result = []
        for container in containers:
            applied_at_raw = container.get("applied_at")
            if isinstance(applied_at_raw, datetime):
                formatted_date = applied_at_raw.strftime("%Y-%m-%dT%H:%M:%S")
            elif isinstance(applied_at_raw, str) and applied_at_raw:
                formatted_date = parse_iso_date_to_string(applied_at_raw)
            else:
                formatted_date = ""

            result.append({
                "id": container.get("id"),
                "user_id": container.get("user_id", ""), 
                "project_name": container.get("project_name", "未設定"),
                "category": container.get("category"),
                "applied_at": formatted_date,
                "status": container.get("status"),
                "total_amount": container.get("total_amount", 0)
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"get_container_all Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"全一覧データの取得に失敗しました: {str(e)}"
        )



# ==========================================
# 【GET】管理者用 コンテナ詳細取得エンドポイント
# ==========================================
@router.get("/admin/container/{container_id}", response_model=ContainerDetailResponse)
def get_admin_container_detail(
    container_id: UUID,
    current_user: Users = Depends(get_current_user)
):
    try:
        # 所有者チェックを行わない管理者用 CRUD を呼び出し
        result = get_admin_container_detail_by_id(container_id=str(container_id))

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="指定された申請コンテナが見つかりません"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"get_admin_container_detail Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"詳細データの取得処理に失敗しました: {str(e)}"
        )


# ==========================================
# 【PUT】管理者用 承認ステータス更新エンドポイント
# ==========================================
@router.put("/admin/accounting/requests/approval", response_model=ApplicationUpdateResponse)
def update_application_approval_endpoint(
    request_data: ApplicationApprovalRequest,
    current_user: Users = Depends(get_current_user)
):
    try:
        success, message = update_application_approval(
            admin_user_db_id=str(current_user.id),
            payload=request_data
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )

        return ApplicationUpdateResponse(
            success=True,
            message=message
        )

    except HTTPException:
        raise
    except Exception as e:
        print(f"update_application_approval_endpoint Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"承認ステータスの更新処理に失敗しました: {str(e)}"
        )


# ==========================================
# 【GET】管理者用: 特定ユーザーのコンテナ一覧取得 (printCheckApprovalページ用)
# ==========================================
@router.get("/admin/container/user/{target_user_id}", response_model=list[Container])
def get_admin_container_by_user(
    target_user_id: UUID,
    start: datetime, 
    end: datetime, 
    offset: int, 
    current_user: Users = Depends(get_current_user)
):
    try:
        start_naive = start.replace(tzinfo=None) if start.tzinfo else start
        end_naive = end.replace(tzinfo=None) if end.tzinfo else end

        # 既存の get_user_container に target_user_id (UUID文字列) を渡して取得
        containers = get_user_container(str(target_user_id), start_naive, end_naive, offset)

        result = []
        for container in containers:
            applied_at_raw = container.get("applied_at")
            if isinstance(applied_at_raw, datetime):
                formatted_date = applied_at_raw.strftime("%Y-%m-%dT%H:%M:%S")
            elif isinstance(applied_at_raw, str) and applied_at_raw:
                formatted_date = parse_iso_date_to_string(applied_at_raw)
            else:
                formatted_date = ""

            result.append({
                "id": container.get("id"),
                "user_id": container.get("user_id", ""),
                "project_name": container.get("project_name", "未設定"),
                "category": container.get("category"),
                "applied_at": formatted_date,
                "status": container.get("status"),
                "total_amount": container.get("total_amount", 0)
            })

        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"get_admin_container_by_user Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"ユーザー別申請一覧データの取得に失敗しました: {str(e)}"
        )
    


# ==========================================
# 【GET】管理者用: アナリティクス集計データ取得エンドポイント
# ==========================================
@router.get("/admin/analytics/summary", response_model=AnalyticsSummaryResponse)
def get_admin_analytics_summary(
    start: datetime,
    end: datetime,
    current_user: Users = Depends(get_current_user)
):
    try:
        # str() で明示的に文字列値として比較
        if str(current_user.role) != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理者権限が必要です"
            )

        start_naive = start.replace(tzinfo=None) if start.tzinfo else start
        end_naive = end.replace(tzinfo=None) if end.tzinfo else end

        if start_naive > end_naive:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="開始日時は終了日時以前である必要があります"
            )

        # 集計 CRUD の呼び出し
        result = get_analytics_summary(start_dt=start_naive, end_dt=end_naive)
        return result

    except HTTPException:
        raise
    except Exception as e:
        print(f"get_admin_analytics_summary Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"アナリティクス集計データの取得に失敗しました: {str(e)}"
        )
    


# ==========================================
# 【POST】管理者用: 複数コンテナ明細一括取得エンドポイント
# ==========================================
@router.post("/admin/containers/bulk-details", response_model=List[ContainerDetailResponse])
def get_admin_containers_bulk_details(
    payload: BulkContainerDetailsRequest,
    current_user: Users = Depends(get_current_user)
):
    try:
        # 管理者権限チェック
        if str(current_user.role) != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="管理者権限が必要です"
            )

        str_ids = [str(cid) for cid in payload.container_ids]
        details = get_bulk_admin_container_details(str_ids)
        return details

    except HTTPException:
        raise
    except Exception as e:
        print(f"get_admin_containers_bulk_details Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"明細の一括取得に失敗しました: {str(e)}"
        )