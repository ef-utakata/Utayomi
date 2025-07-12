# TTS機能の設定方法

## 概要
Utayomi v1.3.0以降では、課金設定のあるGoogle Gemini APIキーを使用してTTS（Text-to-Speech）機能を利用できます。

## 設定手順

### 1. 課金設定のあるAPIキーを取得
1. [Google AI Studio](https://aistudio.google.com/app/apikey) にアクセス
2. 課金設定のあるGoogleアカウントでログイン
3. 新しいAPIキーを作成
4. 課金設定が有効になっていることを確認

### 2. .envファイルに課金設定のあるAPIキーを追加
```env
# 無料利用可能（選評生成・ラジオ原稿生成用）
GOOGLE_API_KEY=your-free-google-api-key-here

# 課金設定あり（TTS音声生成用）
GOOGLE_API_KEY_PAID=your-paid-google-api-key-here
```

### 3. TTS機能の使用

#### 課金設定のあるAPIキーが設定されている場合
```bash
# 完全なTTS機能（選評→原稿→音声）
python selection.py \
    input/library/ja/literature/tanka/monthly/2025/06/selected.csv \
    output/ \
    -i Gemini-Flash \
    -n 3 \
    -a "テスト選評" \
    --tts

# 出力ファイル例
output/
├── selected_テスト選評_Gemini-Flash.md           # 選評Markdown
├── selected_テスト選評_Gemini-Flash.radio_script.txt  # ラジオ原稿
└── selected_テスト選評_Gemini-Flash.wav          # 音声ファイル
```

#### 課金設定のあるAPIキーが設定されていない場合
```bash
# ラジオ原稿生成まで（音声生成はスキップ）
python selection.py \
    input/library/ja/literature/tanka/monthly/2025/06/selected.csv \
    output/ \
    -i Gemini-Flash \
    -n 3 \
    -a "テスト選評" \
    --tts

# 出力ファイル例
output/
├── selected_テスト選評_Gemini-Flash.md           # 選評Markdown
└── selected_テスト選評_Gemini-Flash.radio_script.txt  # ラジオ原稿
# 音声ファイルは生成されません（警告メッセージが表示されます）
```

## 利用可能なTTSモデル

### 推奨モデル
- `gemini-2.5-pro-preview-tts` (デフォルト)
- `gemini-2.5-flash-preview-tts`

### 使用例
```bash
# Pro版TTS使用
python selection.py input.csv output/ -i Gemini --tts --voice-model gemini-2.5-pro-preview-tts

# Flash版TTS使用
python selection.py input.csv output/ -i Gemini --tts --voice-model gemini-2.5-flash-preview-tts
```

## 費用について
- TTS機能の使用には Google Cloud の課金が発生します
- 料金は使用量に基づいて計算されます
- 詳細は [Google AI Studio の料金表](https://ai.google.dev/pricing) を確認してください

## トラブルシューティング

### エラー: "You exceeded your current quota"
- 課金設定が有効になっていない可能性があります
- Google Cloud コンソールで課金設定を確認してください

### エラー: "GOOGLE_API_KEY_PAID is not set"
- .envファイルに課金設定のあるAPIキーが設定されていません
- 上記の設定手順を確認してください

### フォールバック動作
- `GOOGLE_API_KEY_PAID` が設定されていない場合、通常の `GOOGLE_API_KEY` を使用します
- 無料APIキーでTTS機能を使用した場合、エラーが発生する場合があります

## 注意事項
- TTS機能は課金が発生するため、テスト時は少数の短歌で実行することを推奨します
- 無料の選評生成機能は従来通り利用できます
- APIキーは適切に管理し、公開リポジトリにコミットしないでください