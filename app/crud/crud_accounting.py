from uuid import uuid4
from datetime import datetime
from typing import Dict, Any, Tuple
from app.db.session import supabase
from app.schemas.accounting import ApplicationCreateRequest, ApplicationUpdateRequest, ApplicationApprovalRequest


def _calculate_header_status(statuses: list) -> str:
    """
    明細ステータスの一覧から、親コンテナ（application_header）の
    ステータスを判定する共通ロジック。
    - 全て approved -> approved
    - 1つでも rejected があり pending がない -> rejected (または部分却下)
    - pending が残っている -> pending
    """
    if all(s == "approved" for s in statuses):
        return "approved"
    elif any(s == "rejected" for s in statuses) and not any(s == "pending" for s in statuses):
        return "rejected"
    else:
        return "pending"


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
def update_application(payload: ApplicationUpdateRequest, user_db_id: str) -> Tuple[bool, str, int]:
    """
    既存申請の更新・追記・削除および全削除を行う CRUD 関数
    
    Returns:
        Tuple[bool, str, int]: (処理成功フラグ, レスポンスメッセージ, HTTPステータスコード)
    """
    container_id_str = str(payload.container_id)
    now_iso = datetime.utcnow().isoformat()

    # 1. コンテナヘッダー (application_header) の存在確認およびステータスチェック
    header_res = (
        supabase.table("application_header")
        .select("id, user_id, status, category, version")
        .eq("id", container_id_str)
        .execute()
    )

    if not header_res.data or not isinstance(header_res.data, list) or len(header_res.data) == 0:
        return False, "指定された申請が見つかりません。", 404

    header_data = header_res.data[0]

    # ★ Pylanceの型エラーを防ぐため、dict型であることを検証
    if not isinstance(header_data, dict):
        return False, "データの取得形式が不正です。", 500

    if str(header_data.get("user_id") or "") != user_db_id:
        return False, "他人の申請は更新できません。", 403

    current_version = int(header_data.get("version") or 1)
    if payload.version != current_version:
        return False, "他ユーザーが先に更新しました。最新データを再取得してください。", 409

    # pending: 追加・編集・削除可 / rejected: 削除・既存明細の編集（再申請）可、新規追加のみ不可 / それ以外: 変更不可
    status_val = header_data.get("status")
    has_new_details = any(item.id is None for item in payload.updated_details)

    if status_val == "rejected":
        if has_new_details:
            return False, "却下済みの申請に新規の明細を追加することはできません。", 400
        # 明細の削除・既存明細の編集（再申請）は許可する
    elif status_val != "pending":
        return False, "承認済みまたは処理済みの申請は変更できません。", 400

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

        return True, "申請および関連明細を正常に削除しました。", 200

    # ----------------------------------------------------
    # 3. 削除指定された既存明細 (deleted_detail_ids) の削除
    # ----------------------------------------------------
    if payload.deleted_detail_ids:
        deleted_ids_str = [str(uid) for uid in payload.deleted_detail_ids]
        # header_id も条件に含め、他コンテナに属する明細IDが紛れ込んでいても削除されないようにする
        supabase.table(detail_table).delete().eq(
            "header_id", container_id_str
        ).in_(
            "id", deleted_ids_str
        ).execute()

    # ----------------------------------------------------
    # 4. 明細カードの更新 (UPDATE) または 新規追加 (INSERT)
    #    却下済みコンテナでも既存明細の編集（再申請）を許可するが、
    #    明細ごとにDB上の現在ステータスを見て、承認済み明細への誤操作を防ぐ
    #    ※ updated_details には変更のあった明細のみが含まれる前提のため、
    #      合計金額・ステータスの再計算はこのループの後にDB上の残存明細から行う（ここでは計算しない）
    # ----------------------------------------------------
    existing_ids = [str(item.id) for item in payload.updated_details if item.id is not None]
    current_status_by_id: Dict[str, str] = {}
    if existing_ids:
        current_rows_res = (
            supabase.table(detail_table)
            .select("id, status")
            .eq("header_id", container_id_str)
            .in_("id", existing_ids)
            .execute()
        )
        for row in (current_rows_res.data or []):
            if isinstance(row, dict):
                current_status_by_id[str(row.get("id"))] = row.get("status")

    for item in payload.updated_details:
        # 既存明細が現在 approved の場合、このエンドポイント経由の編集は許可しない
        # （UI側の canEditCard でも approved は編集不可の想定だが、API側でも二重に防御する）
        if item.id is not None and current_status_by_id.get(str(item.id)) == "approved":
            return False, "承認済みの明細は編集できません。", 400

        # 共通カラムデータの構築。新規追加・pending明細の編集・rejected明細の再申請の
        # いずれも最終的に pending になる（approvedのケースは直前のガードで return 済み）
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
            # comment はここでは一切触れない（既存の値をDB上でそのまま保持する）
            # header_id も条件に含め、他コンテナに属する明細IDが紛れ込んでいても更新されないようにする
            supabase.table(detail_table).update(record_data).eq(
                "id", str(item.id)
            ).eq(
                "header_id", container_id_str
            ).execute()
        else:
            # 新規追加明細の登録 (INSERT) - UUIDとcreated_atを新規生成
            record_data.update({
                "id": str(uuid4()),
                "created_at": now_iso,
            })
            supabase.table(detail_table).insert(record_data).execute()

    # ----------------------------------------------------
    # 5. 明細の最新状態（status / amount）をDB上の残存明細から取得し、
    #    ヘッダーの status / total_amount / version を更新
    # ----------------------------------------------------
    all_details_res = (
        supabase.table(detail_table)
        .select("status, amount")
        .eq("header_id", container_id_str)
        .execute()
    )
    remaining_rows = [
        row for row in (all_details_res.data or []) if isinstance(row, dict)
    ]
    statuses = [row.get("status") for row in remaining_rows]
    calculated_total_amount = sum(int(row.get("amount") or 0) for row in remaining_rows)
    new_header_status = _calculate_header_status(statuses) if statuses else "pending"

    header_update_res = (
        supabase.table("application_header")
        .update({
            "total_amount": calculated_total_amount,
            "status": new_header_status,
            "version": payload.version + 1,
        })
        .eq("id", container_id_str)
        .eq("version", payload.version)
        .execute()
    )

    if not isinstance(header_update_res.data, list) or len(header_update_res.data) == 0:
        return False, "他ユーザーが先に更新しました。最新データを再取得してください。", 409

    return True, "申請内容を正常に更新しました。", 200



def update_application_approval(
    admin_user_db_id: str,
    payload: ApplicationApprovalRequest
) -> Tuple[bool, str, int]:
    """
    管理者用: 明細カードの承認ステータスを更新し、コンテナ全体のステータスを連動更新する。
    """
    container_id_str = str(payload.container_id)
    now_iso = datetime.utcnow().isoformat()

    # 1. コンテナヘッダーの存在確認
    header_res = (
        supabase.table("application_header")
        .select("id, category, version")
        .eq("id", container_id_str)
        .execute()
    )

    if not header_res.data or not isinstance(header_res.data, list) or len(header_res.data) == 0:
        return False, "指定された申請が見つかりません。", 404

    header_data = header_res.data[0]
    if not isinstance(header_data, dict):
        return False, "データの取得形式が不正です。", 500

    current_version = int(header_data.get("version") or 1)
    if payload.version != current_version:
        return False, "他ユーザーが先に更新しました。最新データを再取得してください。", 409

    category_name = header_data.get("category")
    is_transport = category_name == "交通費"
    detail_table = "transportation_detail" if is_transport else "expense_detail"

    # 2. 各明細カードの status・comment を更新
    # header_id も条件に含め、他コンテナに属する明細IDが紛れ込んでいても更新されないようにする
    for item in payload.details:
        supabase.table(detail_table).update({
            "status": item.status,
            "comment": item.comment,
        }).eq("id", str(item.id)).eq("header_id", container_id_str).execute()

    # 3. コンテナに紐づく全明細のステータスを取得して親（ヘッダー）のステータスを自動判定
    all_details_res = (
        supabase.table(detail_table)
        .select("status")
        .eq("header_id", container_id_str)
        .execute()
    )

    statuses = [
        row.get("status")
        for row in (all_details_res.data or [])
        if isinstance(row, dict)
    ]

    header_status = _calculate_header_status(statuses)

    # 4. コンテナヘッダーのステータス・承認者・承認日時を更新
    header_update_payload: Dict[str, Any] = {
        "status": header_status,
        "approved_by": admin_user_db_id if header_status != "pending" else None,
        "approved_at": now_iso if header_status != "pending" else None,
    }

    header_update_payload["version"] = payload.version + 1

    header_update_res = (
        supabase.table("application_header")
        .update(header_update_payload)
        .eq("id", container_id_str)
        .eq("version", payload.version)
        .execute()
    )

    if not isinstance(header_update_res.data, list) or len(header_update_res.data) == 0:
        return False, "他ユーザーが先に更新しました。最新データを再取得してください。", 409

    return True, "承認ステータスを正常に更新しました。", 200