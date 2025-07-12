# 環境設定ガイド - Utayomi v1.3.1

## 概要

Utayomi v1.3.1では、APIキー管理が大幅に改善され、`.env`ファイルによる安全で便利な設定が可能になりました。特に、TTS機能用の課金設定APIキーの分離により、より安全で柔軟な運用が可能です。

## APIキー設定方法

### 1. .envファイルを使用した設定（推奨）

#### 初回セットアップ
```bash
# テンプレートファイルをコピー
cp .env.example .env

# .envファイルを編集
nano .env  # または vi .env、code .env など
```

#### .envファイルの設定例
```env
# Google Gemini API Key (推奨 - 無料枠あり)
# https://aistudio.google.com/app/apikey で取得
GOOGLE_API_KEY=your-actual-google-api-key-here

# OpenAI API Key (オプション)
# https://platform.openai.com/api-keys で取得
OPENAI_API_KEY=your-actual-openai-api-key-here

# Cohere API Key (オプション)
# https://dashboard.cohere.ai/api-keys で取得
COHERE_API_KEY=your-actual-cohere-api-key-here
```

### 2. 環境変数として直接設定（代替方法）

#### 一時的な設定
```bash
export GOOGLE_API_KEY="your-google-api-key"
export OPENAI_API_KEY="your-openai-api-key"
export COHERE_API_KEY="your-cohere-api-key"
```

#### 永続的な設定（~/.bashrc）
```bash
echo 'export GOOGLE_API_KEY="your-google-api-key"' >> ~/.bashrc
echo 'export OPENAI_API_KEY="your-openai-api-key"' >> ~/.bashrc
echo 'export COHERE_API_KEY="your-cohere-api-key"' >> ~/.bashrc
source ~/.bashrc
```

#### conda環境での設定
```bash
conda activate tanka
conda env config vars set GOOGLE_API_KEY="your-google-api-key"
conda env config vars set OPENAI_API_KEY="your-openai-api-key"
conda env config vars set COHERE_API_KEY="your-cohere-api-key"

# 環境を再アクティベート（設定反映のため）
conda deactivate
conda activate tanka
```

## APIキー取得方法

### Google Gemini API（推奨）
1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. Googleアカウントでログイン
3. 「Create API Key」をクリック
4. 生成されたキーを`.env`ファイルの`GOOGLE_API_KEY`に設定

**推奨理由**: 
- 無料枠が豊富（月間15リクエスト/分、100万トークン/日）
- Gemini 1.5 Flash使用で高性能
- TTS機能も含む

### OpenAI API
1. [OpenAI Platform](https://platform.openai.com/api-keys) にアクセス
2. アカウント作成・ログイン
3. 「Create new secret key」をクリック
4. 生成されたキーを`.env`ファイルの`OPENAI_API_KEY`に設定

### Cohere API
1. [Cohere Dashboard](https://dashboard.cohere.ai/api-keys) にアクセス
2. アカウント作成・ログイン
3. API Keyを生成
4. 生成されたキーを`.env`ファイルの`COHERE_API_KEY`に設定

## セキュリティ

### .envファイルの保護
- `.env`ファイルは自動的に`.gitignore`に含まれます
- リモートリポジトリにアップロードされることはありません
- ローカル環境でのみ使用されます

### 注意事項
- APIキーは他人と共有しないでください
- 公開リポジトリにコミットしないでください
- 定期的にキーをローテーションすることを推奨します

## 動作確認

### 設定の確認
```bash
# 環境をアクティベート
conda activate tanka

# APIキーが正しく読み込まれるかテスト
python -c "from lib.env_loader import get_google_api_key; print('✅ Google API Key loaded successfully' if get_google_api_key() else '❌ Google API Key not found')"
```

### 基本動作テスト
```bash
# ライブラリデータで簡単なテスト実行
python selection.py \
    input/library/ja/literature/tanka/monthly/2025/06/selected.csv \
    output/ \
    -i Gemini \
    -n 3 \
    -a "設定テスト"
```

## トラブルシューティング

### よくある問題

#### 1. APIキーが読み込まれない
```bash
# .envファイルの存在確認
ls -la .env

# ファイル内容の確認（キーは表示されません）
python -c "from lib.env_loader import load_env_vars; load_env_vars()"
```

#### 2. 権限エラー
```bash
# .envファイルの権限確認
ls -la .env

# 必要に応じて権限変更
chmod 600 .env
```

#### 3. 無料枠の制限
- Gemini 1.5 Flash: 月間15リクエスト/分、100万トークン/日
- 制限に達した場合は時間をおいて再実行

#### 4. モデルが見つからない
```bash
# 利用可能なモデル一覧を確認
python selection.py --list dummy dummy
```

## 依存関係

### 必要なパッケージ
```bash
pip install python-dotenv>=1.0.0
```

### requirements.txtの更新
最新の`requirements.txt`には`python-dotenv`が含まれています：
```
python-dotenv>=1.0.0
```

## アップグレード手順

### v1.2.x からのアップグレード
1. 新しい依存関係をインストール:
   ```bash
   pip install python-dotenv
   ```

2. .envファイルを設定:
   ```bash
   cp .env.example .env
   # .envファイルを編集
   ```

3. 既存の環境変数設定は引き続き動作します（互換性保持）

これで、Utayomi v1.3.0の環境設定が完了です！