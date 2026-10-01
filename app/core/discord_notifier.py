"""
申請の新規登録・修正時に Discord (Webhook) へ通知するモジュール。

- レスポンスを返す前に同期的に送信する（Cloud Run の CPU 割り当てを変えずに確実に送るため）。
  DB取得・送信を含む通知処理全体の待ち時間の上限は TOTAL_TIMEOUT_SEC 秒。超えた場合は待たずに
  レスポンスを返す（処理は別スレッドで続行され、結果は破棄される）。
- 送信には標準ライブラリの urllib を使う。supabase_retry が httpx.Client.send を
  リトライ付きで差し替えているため、httpx の同期クライアントだと二重通知になり得る。
- どんなエラーが起きても例外を外へ出さない（PRISM本体の保存・レスポンスに影響させない）。
"""
import json
import urllib.request
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import app.core.config as config
from app.db.session import supabase

REQUEST_TIMEOUT_SEC = 3
TOTAL_TIMEOUT_SEC = 4
BOT_NAME = "会計申請通知bot"
JST = timezone(timedelta(hours=9))

# 通知処理を別スレッドで実行し、全体の待ち時間に上限を設けるためのプール
_executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="discord-notify")

COLOR_NEW = 0x3498DB
COLOR_UPDATED = 0xF39C12


def _format_datetime_jst(value: Any) -> str:
    """DBの日時（ISO文字列/datetime）を JST の 'YYYY/MM/DD HH:mm' に変換する。失敗時は空文字。"""
    if not value:
        return ""
    try:
        if isinstance(value, datetime):
            dt = value
        else:
            text = str(value).strip().replace(" ", "T")
            if text.endswith("Z"):
                text = text[:-1] + "+00:00"
            elif text.endswith("+00"):
                text = text[:-3] + "+00:00"
            dt = datetime.fromisoformat(text)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(JST).strftime("%Y/%m/%d %H:%M")
    except Exception:
        return ""


def _category_label(header: Dict[str, Any]) -> str:
    """申請種別の表示名。「交通費」以外はすべて「経費」とする。"""
    return "交通費" if header.get("category") == "交通費" else "経費"


def _fetch_header(header_id: str) -> Optional[Dict[str, Any]]:
    """
    申請ヘッダーとプロジェクト名を1回のクエリ（join）で取得する。
    存在しない（全削除済み等）場合は None。real_name 列が取得できない場合は name のみで再取得する。
    """
    def query(project_columns: str):
        return (
            supabase.table("application_header")
            .select(f"category, created_at, applied_at, projects({project_columns})")
            .eq("id", header_id)
            .execute()
        )

    try:
        res = query("name, real_name")
    except Exception as e:
        print(f"discord_notifier: real_name の取得に失敗したため name のみで再取得します: {e}")
        res = query("name")
    rows = res.data
    if not rows or not isinstance(rows, list) or not isinstance(rows[0], dict):
        return None
    return rows[0]


def _project_display_name(header: Dict[str, Any]) -> str:
    """プロジェクト正式名称（real_name）を返す。未設定・取得不可なら略称（name）で代替する。"""
    project = header.get("projects")
    if isinstance(project, list):
        project = project[0] if project else None
    if not isinstance(project, dict):
        return "未設定"
    return str(project.get("real_name") or project.get("name") or "未設定")


def _post_to_discord(embed: Dict[str, Any]) -> None:
    """環境変数が揃っていれば Discord へ送信する。未設定なら警告ログのみでスキップ。"""
    webhook_url = config.DISCORD_WEBHOOK_URL
    thread_id = config.DISCORD_THREAD_ID
    role_id = config.DISCORD_ROLE_ID
    if not webhook_url or not thread_id or not role_id:
        print("discord_notifier: DISCORD_WEBHOOK_URL / DISCORD_THREAD_ID / DISCORD_ROLE_ID が未設定のため通知をスキップします")
        return

    separator = "&" if "?" in webhook_url else "?"
    url = f"{webhook_url}{separator}thread_id={thread_id}"
    payload = {
        "username": BOT_NAME,
        "content": f"<@&{role_id}>",
        "allowed_mentions": {"roles": [str(role_id)]},
        "embeds": [embed],
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            # Discord は Python 既定の User-Agent を拒否することがあるため明示する
            "User-Agent": "PRISM-Backend",
        },
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SEC):
        pass


def _run_with_deadline(label: str, job) -> None:
    """通知処理を別スレッドで実行し、TOTAL_TIMEOUT_SEC 秒を超えたら待たずに戻る。例外は外へ出さない。"""
    try:
        future = _executor.submit(job)
        future.result(timeout=TOTAL_TIMEOUT_SEC)
    except FutureTimeoutError:
        print(f"discord_notifier: {label}の通知が{TOTAL_TIMEOUT_SEC}秒以内に完了しなかったため待たずに続行します")
    except Exception as e:
        print(f"discord_notifier: {label}の通知に失敗しました（処理は継続します）: {e}")


def notify_new_application(header_id: str, user_name: Optional[str]) -> None:
    """新規申請の登録成功後に呼ぶ。"""
    def job() -> None:
        header = _fetch_header(header_id)
        if header is None:
            print(f"discord_notifier: 申請ヘッダーが見つからないため通知をスキップします: {header_id}")
            return

        created_at = _format_datetime_jst(header.get("created_at") or header.get("applied_at"))
        embed = {
            "title": "新規申請がありました",
            "color": COLOR_NEW,
            "fields": [
                {"name": "申請者", "value": user_name or "不明", "inline": True},
                {"name": "申請種別", "value": _category_label(header), "inline": True},
                {"name": "プロジェクト", "value": _project_display_name(header), "inline": False},
                {"name": "申請日時", "value": created_at or "不明", "inline": False},
            ],
        }
        _post_to_discord(embed)

    _run_with_deadline("新規申請", job)


def notify_application_updated(header_id: str, user_name: Optional[str]) -> None:
    """既存申請（差し戻し後の再申請を含む）の修正成功後に呼ぶ。全削除でヘッダーが無い場合は通知しない。"""
    def job() -> None:
        header = _fetch_header(header_id)
        if header is None:
            return

        created_at = _format_datetime_jst(header.get("created_at") or header.get("applied_at"))
        embed = {
            "title": "申請が修正されました",
            "color": COLOR_UPDATED,
            "fields": [
                {"name": "修正者", "value": user_name or "不明", "inline": True},
                {"name": "申請種別", "value": _category_label(header), "inline": True},
                {"name": "プロジェクト", "value": _project_display_name(header), "inline": False},
                {"name": "初回作成日時", "value": created_at or "不明", "inline": False},
            ],
        }
        _post_to_discord(embed)

    _run_with_deadline("修正", job)
