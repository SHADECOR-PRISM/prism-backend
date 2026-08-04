from uuid import uuid4
from datetime import datetime
from typing import Dict, Any
from app.db.session import supabase
from app.schemas.accounting import ApplicationCreateRequest

# 1回の申請（ヘッダー + 明細一覧）をSupabaseに一括登録するCRUD関数
def create_application(user_db_id: str, request_data: ApplicationCreateRequest) -> Dict[str, Any]:
    
    # 1. 交通費明細または一般経費明細のどちらが届いているか確認
    transport_details = request_data.transport_details or []
    expense_details = request_data.expense_details or []
    
    all_details = transport_details if transport_details else expense_details
    if not all_details:
        raise ValueError("明細データが1件以上必要です")

    # 2. 明細の金額から合計金額（total_amount）を算出
    total_amount = sum(detail.amount for detail in all_details)

    # 3. application_header への挿入データ作成
    header_id = str(uuid4())
    now_iso = datetime.utcnow().isoformat()

    header_payload = {
        "id": header_id,
        "user_id": str(user_db_id),
        "project_id": str(request_data.header.project_id),
        "type": request_data.header.type,
        "category": request_data.header.category,
        "applied_at": now_iso,
        "status": "pending",
        "total_amount": total_amount,
        "created_at": now_iso,
    }

    # Supabase にヘッダーを挿入（テーブル名: application_header）
    supabase.table("application_header").insert(header_payload).execute()

    # 4. 明細（transportation_detail または expense_detail）の挿入
    if transport_details:
        details_payload = [
            {
                "id": str(uuid4()),
                "header_id": header_id,
                "usage_date": detail.usage_date.isoformat(),
                "category": detail.category,
                "departure": detail.departure,
                "arrival": detail.arrival,
                "is_round_trip": detail.is_round_trip,
                "amount": detail.amount,
                "status": "pending",
                "created_at": now_iso,
            }
            for detail in transport_details
        ]
        # テーブル名: transportation_detail
        supabase.table("transportation_detail").insert(details_payload).execute()

    elif expense_details:
        details_payload = [
            {
                "id": str(uuid4()),
                "header_id": header_id,
                "usage_date": detail.usage_date.isoformat(),
                "category": detail.category,
                "remark": detail.remark,
                "amount": detail.amount,
                "status": "pending",
                "created_at": now_iso,
            }
            for detail in expense_details
        ]
        # テーブル名: expense_detail
        supabase.table("expense_detail").insert(details_payload).execute()

    # 5. レスポンス用データを返却
    return {
        "header_id": header_id,
        "message": "申請が正常に登録されました",
        "total_amount": total_amount
    }