from typing import Dict, Any, Optional, cast
from app.db.session import supabase
from app.core.date_formatter import parse_iso_date_to_string


def get_container_detail_by_id(
    container_id: str, 
    user_db_id: str, 
    user_public_id: str
) -> Optional[Dict[str, Any]]:
    """
    logDetail ページに必要なデータセットを取得する。
    テーブル名: application_header / transportation_detail / expense_detail (すべて単数形)
    """
    # 1. ヘッダー情報とプロジェクト名を結合取得 (application_header)
    response = (
        supabase.table("application_header")
        .select("*, projects(name)")
        .eq("id", container_id)
        .eq("user_id", user_db_id)  # 所有者チェック
        .execute()
    )

    if not response.data or not isinstance(response.data, list):
        return None

    header = cast(Dict[str, Any], response.data[0])

    # 2. プロジェクト名の抽出
    project_data = header.get("projects")
    project_name = "未設定"
    if isinstance(project_data, dict):
        project_name = project_data.get("name", "未設定")

    # 3. 申請日時の安全なフォーマット整形
    formatted_date = parse_iso_date_to_string(header.get("applied_at"))

    # 4. カテゴリに応じた明細レコードの取得 (単数形テーブル名指定)
    category = str(header.get("category") or "")
    transport_details = []
    expense_details = []

    if category == "交通費":
        details_res = (
            supabase.table("transportation_detail")
            .select("*")
            .eq("header_id", container_id)
            .execute()
        )
        if details_res.data and isinstance(details_res.data, list):
            transport_details = [cast(Dict[str, Any], item) for item in details_res.data]

    elif category == "経費":
        details_res = (
            supabase.table("expense_detail")
            .select("*")
            .eq("header_id", container_id)
            .execute()
        )
        if details_res.data and isinstance(details_res.data, list):
            expense_details = [cast(Dict[str, Any], item) for item in details_res.data]

    # 5. レスポンス用データ構造にまとめて返却
    return {
        "id": str(header.get("id")),
        "user_id": user_public_id,
        "project_name": project_name,
        "category": category,
        "applied_at": formatted_date,
        "status": str(header.get("status") or "pending"),
        "total_amount": header.get("total_amount", 0),
        "transportation_details": transport_details,
        "expense_details": expense_details,
    }




def get_admin_container_detail_by_id(
    container_id: str
) -> Optional[Dict[str, Any]]:
    """
    管理者用: 所有者チェック（user_id一致判定）を行わずに任意のコンテナ詳細を取得する。
    """
    # 1. ヘッダー情報、プロジェクト名、申請者ユーザー情報を結合取得
    response = (
        supabase.table("application_header")
        .select("*, projects(name), users:user_id(user_id)")
        .eq("id", container_id)
        .execute()
    )

    if not response.data or not isinstance(response.data, list):
        return None

    header = cast(Dict[str, Any], response.data[0])

    # 2. プロジェクト名・ユーザーIDの抽出
    project_data = header.get("projects")
    project_name = project_data.get("name", "未設定") if isinstance(project_data, dict) else "未設定"

    user_data = header.get("users")
    user_public_id = user_data.get("user_id", "") if isinstance(user_data, dict) else ""

    # 3. 日付フォーマット整形
    formatted_date = parse_iso_date_to_string(header.get("applied_at"))

    # 4. 明細取得
    category = str(header.get("category") or "")
    transport_details = []
    expense_details = []

    if category == "交通費":
        details_res = (
            supabase.table("transportation_detail")
            .select("*")
            .eq("header_id", container_id)
            .execute()
        )
        if details_res.data and isinstance(details_res.data, list):
            transport_details = [cast(Dict[str, Any], item) for item in details_res.data]

    elif category == "経費":
        details_res = (
            supabase.table("expense_detail")
            .select("*")
            .eq("header_id", container_id)
            .execute()
        )
        if details_res.data and isinstance(details_res.data, list):
            expense_details = [cast(Dict[str, Any], item) for item in details_res.data]

    return {
        "id": str(header.get("id")),
        "user_id": user_public_id,
        "project_name": project_name,
        "category": category,
        "applied_at": formatted_date,
        "status": str(header.get("status") or "pending"),
        "total_amount": header.get("total_amount", 0),
        "transportation_details": transport_details,
        "expense_details": expense_details,
    }