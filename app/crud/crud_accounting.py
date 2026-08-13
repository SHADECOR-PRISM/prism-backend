from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Tuple
from app.db.session import supabase
from app.schemas.accounting import ApplicationCreateRequest, ApplicationUpdateRequest

# ==========================================
# 1. 新規申請登録 (既存の関数)
# ==========================================
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


# ==========================================
# 2. 既存申請の更新・追記・明細削除および全削除 (追加関数)
# ==========================================
def update_application(payload: ApplicationUpdateRequest) -> Tuple[bool, str]:
    """
    既存申請の更新・追記・削除および全削除を行う CRUD 関数
    
    Returns:
        Tuple[bool, str]: (処理成功フラグ, レスポンスメッセージ)
    """
    container_id_str = str(payload.container_id)
    now_iso = datetime.utcnow().isoformat()

    # 1. コンテナヘッダー (application_header) の存在確認およびステータスチェック
    header_res = (
        supabase.table("application_header")
        .select("id, status, category")
        .eq("id", container_id_str)
        .execute()
    )

    if not header_res.data or not isinstance(header_res.data, list) or len(header_res.data) == 0:
        return False, "指定された申請が見つかりません。"

    header_data = header_res.data[0]

    # ★ Pylanceの型エラーを防ぐため、dict型であることを検証
    if not isinstance(header_data, dict):
        return False, "データの取得形式が不正です。"

    # pending（申請中・未承認）以外のステータスは編集不可
    status_val = header_data.get("status")
    if status_val != "pending":
        return False, "承認済みまたは処理済みの申請は変更できません。"

    category_name = header_data.get("category")
    is_transport = category_name == "交通費"
    # テーブル名の指定（単数形テーブル名に統一）
    detail_table = "transportation_detail" if is_transport else "expense_detail"

    # ----------------------------------------------------
    # 2. 全削除 (is_all_deleted == True) の場合
    # ----------------------------------------------------
    if payload.is_all_deleted:
        # 関連明細カードの全削除
        supabase.table(detail_table).delete().eq(
            "header_id", container_id_str
        ).execute()

        # コンテナヘッダー自体の削除
        supabase.table("application_header").delete().eq(
            "id", container_id_str
        ).execute()

        return True, "申請および関連明細を正常に削除しました。"

    # ----------------------------------------------------
    # 3. 削除指定された既存明細 (deleted_detail_ids) の削除
    # ----------------------------------------------------
    if payload.deleted_detail_ids:
        deleted_ids_str = [str(uid) for uid in payload.deleted_detail_ids]
        supabase.table(detail_table).delete().in_(
            "id", deleted_ids_str
        ).execute()

    # ----------------------------------------------------
    # 4. 明細カードの更新 (UPDATE) または 新規追加 (INSERT)
    # ----------------------------------------------------
    calculated_total_amount = 0

    for item in payload.updated_details:
        calculated_total_amount += item.amount

        # 共通カラムデータの構築
        record_data = {
            "header_id": container_id_str,
            "usage_date": item.usage_date.isoformat(),
            "category": item.category,
            "amount": item.amount,
            "status": "pending",
        }

        # カテゴリ固有データのマッピング
        if is_transport:
            record_data.update({
                "departure": item.departure,
                "arrival": item.arrival,
                "is_round_trip": item.is_round_trip if item.is_round_trip is not None else True,
            })
        else:
            record_data.update({
                "remark": item.remark,
            })

        if item.id is not None:
            # 既存明細の更新 (UPDATE)
            supabase.table(detail_table).update(record_data).eq(
                "id", str(item.id)
            ).execute()
        else:
            # 新規追加明細の登録 (INSERT) - UUIDとcreated_atを新規生成
            record_data.update({
                "id": str(uuid4()),
                "created_at": now_iso,
            })
            supabase.table(detail_table).insert(record_data).execute()

    # ----------------------------------------------------
    # 5. ヘッダー側の合計金額 (total_amount) を最新に更新
    # ----------------------------------------------------
    supabase.table("application_header").update(
        {"total_amount": calculated_total_amount}
    ).eq("id", container_id_str).execute()

    return True, "申請内容を正常に更新しました。"