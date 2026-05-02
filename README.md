
# PRISM - Backend

**Project Resource & Inventory System Manager**

PRISM は、プロジェクト運営で発生するリソース管理、金銭管理、および付随するあらゆる事務作業を効率化・統合するために設計されたバックオフィス支援プラットフォームです。プロジェクト運営における業務フローを最適化し、透明性の高い業務遂行を実現します。

### Important
本リポジトリは、PRISM システムの**バックエンド（サーバーサイド）**ソースコードを管理しています。

### 🚀 技術スタック

堅牢な型安全性と高性能な API レスポンスを実現するため、以下の技術を採用しています。
- **Language:** Python (v3.12)
- **Framework:** FastAPI
- **ORM/Model:** SQLModel (SQLAlchemy + Pydantic)
- **Database/Auth:** Supabase (PostgreSQL)
- **Infrastructure:** Docker / Docker Compose
- **Migration:** Alembic

### 🤝 コミットメッセージ規則

本プロジェクトでは、以下の形式でコミットメッセージを記述します。
`type: description`
- **feat:** 新機能の追加
- **fix:** バグの修正
- **docs:** ドキュメントのみの変更
- **style:** コードの動作に影響しない修正 (ホワイトスペース、フォーマット等)
- **refactor:** バグ修正や機能追加を含まないコードの整理
- **perf:** パフォーマンス向上のための変更
- **chore:** ビルドプロセスやドキュメント生成などの補助ツール、ライブラリの変更

### 🛠 セットアップ手順

本プロジェクトは Docker を利用して開発環境が抽象化されています。ホストマシンへの Python のインストールは不要です。Docker のインストールのみ完了させてください。VS Code + Dev Containers での開発を推奨しています。

#### 0. 事前準備
- Docker Desktop（または Docker Engine）がインストールされ、起動していること。
- VS Code 拡張機能 **Dev Containers** がインストールされていること。

#### 1. リポジトリのクローン
```bash
git clone [https://github.com/SHADECOR-PRISM/prism-backend.git](https://github.com/SHADECOR-PRISM/prism-backend.git)
cd prism-backend
```

#### 2. コンテナの構築とパッケージインストール
1. プロジェクトのルートディレクトリを VS Code で開きます。
2. 画面右下に「コンテナで作成して再度開く（Reopen in Container）」という通知が表示されるので、それをクリックします。表示されない場合は、`F1` キー（または `Cmd+Shift+P`）を押し、「Dev Containers: Reopen in Container」を実行してください。
3. 初回起動時はコンテナのビルドとパッケージインストールが自動で行われるため、数分かかります。

> **Tip**
> **パッケージや環境の更新について**
> - ライブラリを追加した場合: `requirements.txt` を編集後、コンテナ内のターミナルで `pip install -r requirements.txt` を実行してください。
> - 設定を変更した場合: `Dockerfile` や `devcontainer.json` を変更した場合は、コマンドパレットから「Dev Containers: Rebuild Container」を実行して環境を更新してください。

#### 3. 開発サーバーへのアクセス
起動後は、Swagger UI（API ドキュメント）で動作確認が行えます。
[http://localhost:8000/docs](http://localhost:8000/docs)

### 📂 ディレクトリ構成

```text
prism-backend/
├── .devcontainer      # Dev container設定用ファイル
├── docker/            # 実行環境設定（Dockerfile等）
├── app/               # アプリケーション本体
│   ├── api/           # エンドポイント定義
│   ├── core/          # 全体設定（config.py等）
│   ├── crud/          # DB操作ロジック
│   ├── db/            # DB接続・セッション管理
│   ├── models/        # SQLModel定義
│   ├── schemas/       # Pydantic型定義
│   └── main.py        # FastAPI起動エントリーポイント
├── docker-compose.yml # 環境オーケストレーション
├── .env               # 環境変数（ローカル開発用）
└── README.md          # 本ドキュメント
```

### 💡 開発ガイド

#### 1. ブランチ運用とPR
- `main` ブランチへの直接プッシュは禁止されています。
- 新しい作業を始める際は、必ず `feat/feature-name` や `fix/bug-name` といった名前でブランチを切ってください。
- プルリクエスト（PR）作成時は、最小限の機能単位で作成し、レビュアーを指定してください。

#### 2. 環境変数の扱い
- Supabase の URL や API キーなどの機密情報は `.env` ファイルで管理します。
- `.env.example` をコピーして `.env` を作成してください。
- **`.env` は GitHub にコミットしないでください（`.gitignore` で除外済みです）。**

#### 3. テストファイルの構築について
- .gitignoreに `app/` 内部の任意の場所に配置されたtestフォルダを排除するように設定しています。
- テストファイルを作成する場合testフォルダ内部に配置してください。

© 2026 SHADECOR / PRISM Project Team
```