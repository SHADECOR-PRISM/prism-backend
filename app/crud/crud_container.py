from typing import Dict, Any, List, cast
from datetime import datetime
from app.db.session import supabase


def get_user_container(
    user_db_id: str, 
    start: datetime, 
    end: datetime, 
    offset: int, 
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    log ページ（コンテナ一覧）に必要なデータセットを取得する。
    テーブル名: application_header (単数形)
    """
    start_str = start.isoformat()
    end_str = end.isoformat()

    # application_header (単数形) に修正
    response = (
        supabase.table("application_header")
        .select("*, projects(name)")
        .eq("user_id", user_db_id)
        .gte("applied_at", start_str)
        .lte("applied_at", end_str)
        .order("applied_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    if not response.data or not isinstance(response.data, list):
        return []

    results = []
    for row in response.data:
        item = cast(Dict[str, Any], row)
        
        # 結合された projects リレーションからプロジェクト名を取得
        project_data = item.get("projects")
        project_name = "未設定"
        if isinstance(project_data, dict):
            project_name = project_data.get("name", "未設定")

        results.append({
            "id": str(item.get("id")),
            "project_name": project_name,
            "category": str(item.get("category") or ""),
            "applied_at": item.get("applied_at"),
            "status": str(item.get("status") or "pending"),
            "total_amount": item.get("total_amount", 0),
        })

    return results



def get_all_containers(
    start: datetime, 
    end: datetime, 
    offset: int, 
    limit: int = 20
) -> List[Dict[str, Any]]:
    """
    admin approval ページ（全ユーザーのコンテナ一覧）に必要なデータセットを取得する。
    """
    start_str = start.isoformat()
    end_str = end.isoformat()

    # 💡 users:user_id(user_id) を追加して users テーブルの user_id (例: usr00001) を取得
    response = (
        supabase.table("application_header")
        .select("*, projects(name), users:user_id(user_id)")
        .gte("applied_at", start_str)
        .lte("applied_at", end_str)
        .order("applied_at", desc=True)
        .range(offset, offset + limit - 1)
        .execute()
    )

    if not response.data or not isinstance(response.data, list):
        return []

    results = []
    for row in response.data:
        item = cast(Dict[str, Any], row)
        
        # プロジェクト名を取得
        project_data = item.get("projects")
        project_name = "未設定"
        if isinstance(project_data, dict):
            project_name = project_data.get("name", "未設定")

        # 💡 users リレーションから公開ID (user_id) を取得
        user_data = item.get("users")
        public_user_id = ""
        if isinstance(user_data, dict):
            public_user_id = str(user_data.get("user_id") or "")

        results.append({
            "id": str(item.get("id")),
            "user_id": public_user_id,  # 💡 UUID ではなく 'usr00001' 等の形式が入る
            "project_name": project_name,
            "category": str(item.get("category") or ""),
            "applied_at": item.get("applied_at"),
            "status": str(item.get("status") or "pending"),
            "total_amount": item.get("total_amount", 0),
        })

    return results