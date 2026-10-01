from dotenv import load_dotenv
load_dotenv()

import os

#supabase
SUPABASE_URL = str(os.getenv('SUPABASE_URL'))
# 認証操作（ログイン検証・トークン更新）専用。ブラウザ用と同等の公開キー
SUPABASE_KEY_PUBLIC = str(os.getenv('SUPABASE_KEY_PUBLIC'))
# DB操作全般用の特権キー（service_role）。RLSを完全にバイパスする
SUPABASE_KEY_SECRET = str(os.getenv('SUPABASE_KEY_SECRET'))
ADD_EMAIL_ADRESS = str(os.getenv('ADD_EMAIL_ADRESS'))

# Cookie属性（本番のみCloud Run環境変数で上書きする。未設定時は開発環境のデフォルト挙動を維持）
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"
COOKIE_SAMESITE = os.getenv("COOKIE_SAMESITE", "lax")

# APIドキュメント（/docs, /redoc, /openapi.json）の公開可否（本番のみCloud Run環境変数でfalseに上書きする。未設定時は開発環境のデフォルト挙動＝公開を維持）
ENABLE_API_DOCS = os.getenv("ENABLE_API_DOCS", "true").lower() == "true"

# local development
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
FETCH_LIMIT = 10


# Discord通知（Webhook）。未設定（None/空文字）の場合は通知を安全にスキップする。
# ※上記の str(os.getenv()) 形式だと未設定時に文字列 "None" になり判定できないため、意図的に str() を付けない
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
DISCORD_THREAD_ID = os.getenv("DISCORD_THREAD_ID")
DISCORD_ROLE_ID = os.getenv("DISCORD_ROLE_ID")
