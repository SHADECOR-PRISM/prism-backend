from datetime import datetime, timedelta, timezone
from typing import Optional

from app.db.session import supabase, get_auth_client

# ログイン試行回数制限（ブルートフォース対策）
# 設計方針の詳細は docs/login-attempts.md 6章を参照
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 10
ATTEMPT_DECAY_MINUTES = 30


def _now() -> datetime:
  return datetime.now(timezone.utc)


def _get_attempt_row(login_id: str) -> Optional[dict]:
  response = (
    supabase.table("login_attempts")
    .select("*")
    .eq("login_id", login_id)
    .maybe_single()
    .execute()
  )
  return response.data if response else None


def check_lockout(login_id: str) -> Optional[datetime]:
  """
  ロック中なら解除時刻(locked_until)を返す。ロックされていなければNone。
  前回試行からATTEMPT_DECAY_MINUTES以上経過していればカウントを自然減衰させる。
  login_attemptsテーブル自体に問題がある場合（未作成・通信障害・キー設定ミス等、
  Postgrestのエラーに限らずあらゆる例外を含む）は、ブルートフォース対策の不備より
  ログイン機能停止の方が実害が大きいため、ロックなし扱い（フェイルオープン）として
  通常のログイン処理を継続させる。
  """
  try:
    row = _get_attempt_row(login_id)
  except Exception as e:
    print(f"[check_lockout] login_attempts参照エラー（フェイルオープン）: {e}")
    return None

  if not row:
    return None

  last_attempt_at = datetime.fromisoformat(row["last_attempt_at"])
  if _now() - last_attempt_at > timedelta(minutes=ATTEMPT_DECAY_MINUTES):
    try:
      supabase.table("login_attempts").update({
        "failed_count": 0,
        "locked_until": None,
      }).eq("login_id", login_id).execute()
    except Exception as e:
      print(f"[check_lockout] login_attempts自然減衰の更新エラー: {e}")
    return None

  locked_until_raw = row.get("locked_until")
  if not locked_until_raw:
    return None

  locked_until = datetime.fromisoformat(locked_until_raw)
  return locked_until if locked_until > _now() else None


def record_failure(login_id: str) -> int:
  """
  ログイン失敗を記録し、更新後のfailed_countを返す。
  MAX_FAILED_ATTEMPTSに達した場合はlocked_untilをセットする。
  存在しないuser_idでも同じ経路で呼び出すこと（ユーザー列挙対策）。
  記録に失敗しても401自体は返したいため、エラー時は記録を諦めてfailed_count=0を返す。
  """
  try:
    row = _get_attempt_row(login_id)
    failed_count = (row["failed_count"] if row else 0) + 1

    payload = {
      "login_id": login_id,
      "failed_count": failed_count,
      "last_attempt_at": _now().isoformat(),
    }
    if failed_count >= MAX_FAILED_ATTEMPTS:
      payload["locked_until"] = (_now() + timedelta(minutes=LOCKOUT_MINUTES)).isoformat()

    supabase.table("login_attempts").upsert(payload, on_conflict="login_id").execute()
    return failed_count
  except Exception as e:
    print(f"[record_failure] login_attempts記録エラー（フェイルオープン）: {e}")
    return 0


def reset_attempts(login_id: str) -> None:
  try:
    supabase.table("login_attempts").delete().eq("login_id", login_id).execute()
  except Exception as e:
    print(f"[reset_attempts] login_attempts削除エラー: {e}")


#サインイン認証
def sign_in(email: str, password: str):
  # 認証専用の使い捨てクライアントでパスワードを検証する。
  # 共有supabaseクライアント(DB操作用)でsign_inすると、以後そのクライアント全体が
  # このユーザーの権限に書き換わってしまうため、意図的に分離している
  # （詳細: docs/shared-supabase-client-auth-race.md）。
  auth_client = get_auth_client()
  response = auth_client.auth.sign_in_with_password({
    "email": email,
    "password": password
  })

  if response is None:
    raise Exception

  return response

def refresh_session(refresh_token: str):
  auth_client = get_auth_client()
  response = auth_client.auth.refresh_session(refresh_token)

  if response is None:
    raise Exception

  return response

#サインアウト
def sign_out(access_token: Optional[str]) -> None:
  """
  クライアントが保持するセッション状態には依存せず、呼び出し元から明示的に渡された
  access_tokenをAdmin APIへ直接渡して失効させる。Admin APIはservice_role権限が必要な
  ため、DB操作用の共有supabaseクライアント（Secret Key固定）を使う。
  access_tokenが無い場合（期限切れ等）は失効対象が無いため何もしない。
  失効リクエスト自体が失敗しても（トークンが既に無効・通信障害等）、
  ログアウト操作自体（Cookie削除）は成功させたいため、ここで例外を握りつぶす。
  """
  if not access_token:
    return
  try:
    supabase.auth.admin.sign_out(access_token, "global")
  except Exception as e:
    print(f"[sign_out] トークン失効エラー（Cookie削除は継続）: {e}")
