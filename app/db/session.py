from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
import app.core.config as config
from app.core.supabase_retry import install_httpx_retry

install_httpx_retry()

# 通信タイムアウトおよび接続設定オプション
options = SyncClientOptions(
    postgrest_client_timeout=10,  # タイムアウト時間(秒)
    storage_client_timeout=10,
)

# DB操作全般（全CRUD共通）用のクライアント。Secret Key(service_role)で固定初期化する。
# このインスタンスで .auth.sign_in_with_password() / .auth.refresh_session() を絶対に呼ばないこと。
# 呼ぶとクライアント全体のAuthorizationヘッダーがそのユーザーのトークンに書き換わり、
# 以後の全リクエストがservice_role権限を失ってしまう
# （詳細: docs/shared-supabase-client-auth-race.md、docs/a.md）。
# 認証操作は get_auth_client() が返す使い捨てクライアントを使うこと。
supabase: Client = create_client(
    supabase_url=config.SUPABASE_URL,
    supabase_key=config.SUPABASE_KEY_SECRET,
    options=options
)


def get_auth_client() -> Client:
    """
    ログイン検証(sign_in_with_password)・トークン更新(refresh_session)専用の使い捨てクライアント。
    呼び出すたびに新規生成し、どこにも保持しないこと。
    Publishable Key(anon相当)で初期化する（Auth APIの呼び出しにservice_role権限は不要なため）。
    """
    return create_client(
        supabase_url=config.SUPABASE_URL,
        supabase_key=config.SUPABASE_KEY_PUBLIC,
        options=options,
    )