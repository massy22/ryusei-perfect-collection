# Project Meteor: セットアップ手順

## GitHub Secrets の設定

GitHubリポジトリの設定画面 (`Settings` > `Secrets and variables` > `Actions`) で、以下のSecretsを登録してください。

| 名前 | 説明 | 例 / 備考 |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Google Gemini (Generative AI) のAPIキー | AI Studioから取得 |
| `GOOGLE_SEARCH_API_KEY` | Google Custom Search JSON API のAPIキー | GCP Console (Custom Search API) |
| `SEARCH_ENGINE_ID` | カスタム検索エンジンのID (cx) | Programmable Search Engine の設定 |
| `FTP_SERVER` | デプロイ先のFTPサーバー (XREA) | 例: `ftp.example.org` |
| `FTP_USERNAME` | FTPユーザー名 | |
| `FTP_PASSWORD` | FTPパスワード | |

## ローカル開発環境での実行

1. **ライブラリのインストール**:
   ```bash
   pip install -r requirements.txt
   ```

2. **収集スクリプトの実行 (モックモード)**:
   ```bash
   python tools/collector.py
   ```
   *APIキーが設定されていない場合、ダミーデータを使用して動作します。*

3. **Hugoサーバーの起動**:
   ```bash
   hugo server -D
   ```

## ディレクトリ構成
- `content/`: ボットによって生成されたMarkdown記事
- `tools/`: Pythonスクリプト
- `.github/workflows/`: CI/CD設定ファイル
