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
