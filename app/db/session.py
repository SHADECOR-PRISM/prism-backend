from supabase import create_client, Client
from supabase.lib.client_options import SyncClientOptions
import app.core.config as config

# 通信タイムアウトおよび接続設定オプション
options = SyncClientOptions(
    postgrest_client_timeout=10,  # タイムアウト時間(秒)
    storage_client_timeout=10,
)

# 既存の config.SUPABASE_KEY (Secret Key) を使用して初期化
supabase: Client = create_client(
    supabase_url=config.SUPABASE_URL,
    supabase_key=config.SUPABASE_KEY,
    options=options
)