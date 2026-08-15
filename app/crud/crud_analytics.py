from typing import Dict, Any, cast, List
from datetime import datetime
from app.db.session import supabase

def get_analytics_summary(start_dt: datetime, end_dt: datetime) -> Dict[str, Any]:
    """
    管理者用: 指定期間内の申請ステータス件数（未承認・承認済み・却下）および
    承認済み伝票のカテゴリ別支出合計を集計する。
    テーブル名: application_header (単数形)
    """
    start_iso = start_dt.isoformat()
    end_iso = end_dt.isoformat()

    # 1. 指定期間内の支出申請ヘッダー（type='expense'）を一括取得
    response = (
        supabase.table("application_header")
        .select("id, status, category, total_amount, type")
        .gte("applied_at", start_iso)
        .lte("applied_at", end_iso)
        .eq("type", "expense")
        .execute()
    )

    containers: List[Dict[str, Any]] = []
    if response.data and isinstance(response.data, list):
        containers = [cast(Dict[str, Any], item) for item in response.data]

    counts = {"approved": 0, "pending": 0, "rejected": 0}
    transport_total = 0
    general_total = 0

    # 2. ステータス件数および承認済み支出額の集計
    for item in containers:
        status_val = str(item.get("status") or "")
        category_val = str(item.get("category") or "")
        amount = int(item.get("total_amount") or 0)

        # ステータス別件数
        if status_val in counts:
            counts[status_val] += 1

        # 承認済み (approved) の伝票のみ金額を集計
        if status_val == "approved":
            if category_val == "交通費":
                transport_total += amount
            elif category_val == "経費":
                general_total += amount

    total_count = sum(counts.values())

    return {
        "status_counts": {
            "approved": counts["approved"],
            "pending": counts["pending"],
            "rejected": counts["rejected"],
            "total": total_count,
        },
        "expenses": {
            "transport": transport_total,
            "general": general_total,
            "total": transport_total + general_total,
        },
    }