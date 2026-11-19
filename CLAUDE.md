# CLAUDE.md（prism-backend）

PRISM（Project Resource & Inventory System Manager）のバックエンド。FastAPI + Supabase（PostgreSQL / Auth）。Python 3.11（`docker/Dockerfile`）。フロントエンドは別リポジトリ `prism-frontend`。実際の依存は `requirements.txt` を正とする（README の技術スタック記載とは一致しない部分がある）。

## ブランチ運用（必須）

- 枝は必ず `main` → `develop` → `feat/...`（`fix/...` `chore/...` `docs/...` など）の順に伸ばす。作業ブランチは **`develop` から切る**。
- 修正は必ず `develop` にマージし、`develop` から `main` にマージする。作業ブランチを直接 `main` にマージしない。`main` への直接 push も禁止。
- ブランチは機能単位で分け、PR は最小限の機能単位で作る。
- コミットメッセージは `type: description`（`feat` / `fix` / `docs` / `style` / `refactor` / `perf` / `chore`）。

## 起動・確認

- 開発サーバー: `uvicorn app.main:app --reload --host 0.0.0.0 --port 8000`（docker-compose のコマンドと同じ）。Swagger UI は `http://localhost:8000/docs`。
- 依存を足したら `requirements.txt` にバージョン固定で記載する。
- テストコードは現在ない。置く場合は `app/` 配下の `test/` フォルダ内に置く（`.gitignore` で除外されるため、コミット対象にしたい場合は相談する）。

## 構成（`app/`）

- `api/` — エンドポイント。`crud/` — DB 操作（Supabase クライアント経由）。`schemas/` — Pydantic。`models/` — SQLAlchemy モデル。`core/` — 設定・Discord 通知・例外・リトライ。
- 管理者向けは `/admin/...` で、各ハンドラ内で `role == "admin"` を確認する。一般ユーザーは自分のデータのみ操作できるよう所有者チェックを行う。

## 認証・Supabase の注意点

- ログインは `user_id + ADD_EMAIL_ADRESS`（ダミードメイン）をメールとして Supabase Auth に渡す設計。ログイン試行回数のロックは `login_attempts` テーブルで管理する。
- Supabase クライアントは2種類を使い分けている。DB 操作は共有の service_role クライアント、パスワード検証・トークン更新は使い捨ての認証専用クライアント（`get_auth_client()`）。**共有クライアントで `sign_in` しない**（以後その共有クライアント全体がそのユーザー権限になるため。詳細は `docs/legacy/session-key/`）。
- service_role キーは RLS をバイパスする。キーや `.env` をログ・コミットに出さない。

## 環境変数（`app/core/config.py`）

`SUPABASE_URL` / `SUPABASE_KEY_PUBLIC` / `SUPABASE_KEY_SECRET` / `ADD_EMAIL_ADRESS` / `FRONTEND_URL` / `COOKIE_SECURE` / `COOKIE_SAMESITE` / `ENABLE_API_DOCS` / `DISCORD_WEBHOOK_URL` / `DISCORD_THREAD_ID` / `DISCORD_ROLE_ID`。Discord 系は未設定なら通知のみスキップされる。`.env` はコミットしない。本番の値は Cloud Run の環境変数で設定する。

## API 変更時の手順

エンドポイントやスキーマを変えたら `python scripts/export_openapi.py` で `openapi.json` を再生成し、フロントエンドの `app/openapi/schema.json` にコピーして `npm run orval` を実行してもらう（フロントの CLAUDE.md を参照）。

## ドキュメント

ソースを変更したら、対応する `docs/dev-guide/`（親ディレクトリの `docs/`）のドキュメントも手動で更新する。

## 機密情報の取り扱い（公開リポジトリ）

このリポジトリは **public** で、就職活動・オープンソースとして公開する。次のものを、コード・コメント・ドキュメント・コミットメッセージ・PR / Issue に**絶対に書かない**。

- API キー・トークン・パスワード・秘密鍵（Supabase の Publishable / Secret Key、JWT、Cloudflare / GCP の認証情報など）
- Discord の Webhook URL・スレッド ID・ロール ID
- 本番サービスの実 URL・プロジェクト ID / 番号（Cloud Run、Cloudflare Pages、Supabase のプロジェクト URL など）
- 実在するユーザーの氏名・メールアドレス・ユーザー ID、DB のダンプや実データ、ダミーのメール用ドメインの実際の値

守ること:

- 設定値は `.env`（`.gitignore` で除外）か、本番のホスティング側の環境変数・シークレットにだけ置く。説明が必要なときは `<SUPABASE_URL>` のようなプレースホルダーで書く。
- コミット前に `git diff --staged` を読み、上記が混ざっていないか確認する。`.env*` や鍵ファイルを `git add -f` で追加しない。
- 内部向けの情報（デプロイ手順・運用資料など）は、private の `prism-docs` に置き、このリポジトリには書かない。
- コミットのメールアドレスは、GitHub の no-reply アドレスを使う。
- 誤ってコミット・push した場合は、キーを**先に失効・再発行**してから相談する（履歴から消しても、公開された時点で漏えいとみなす）。
