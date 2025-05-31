# Utayomi – `selection.py` リファクタリング & TTS 統合ロードマップ

更新目的
1. 選評結果 (`selection.py`) の **PDF 生成を廃止**し、Markdown テキストのみを出力とする。
2. 生成した Markdown から **音声ガイド (TTS)** を自動生成するフローを組み込み、CLI 一発で
   「選評 Markdown ＋ 音声ファイル」を得られるようにする。

---

## 1. 技術的ギャップの整理

| 項目 | 現状実装 | 変更後に必要な機能 |
|------|-----------|--------------------|
| PDF 生成 | `lib/submodules/tools.selection_markdown()` 内で `markdown→html→pdfkit` 変換 | 不要。処理呼び出し・依存ライブラリ(pdfkit, wkhtmltopdf) と関連コードを削除 |
| Markdown 出力 | `lib/submodules/tools.selection_markdown()` が `basename.md` を書き出す (basename は `{input}_{a}_{i}`) | 継続利用 |
| TTS 生成 | `lib/tts.py` が Gemini Multi-Speaker TTS を呼ぶ `generate_speech()` 実装あり | ・Markdown → ラジオ原稿 → TTS → `basename.wav/ogg` 保存<br>・`selection.py` から呼び出す |
| CLI インタフェース | `selection.py` は TTS 関連オプションを持たない | ・`--tts` (flag) : 有効時のみ TTS 実行<br>・`--voice-model`, `--speaker`, `--audio-format` など拡張オプション (後方互換を保ったまま) |
| ライブラリ依存 | pdfkit / wkhtmltopdf が必須 | Prisma: pdfkit を削除。google-genai は既に `tts_tool.py` で使用、requirements.txt へ追加が必要な場合あり |

---

## 2. 実装方針 (ロードマップ)

### Phase-0: 下準備
1. **依存整理** – pdfkit / wkhtmltopdf を requirements から外す。google-genai を確認/追加。
2. **共通 TTS ヘルパーをモジュール化** – `tts_tool.py` から純粋関数群を抽出し `lib/tts.py` として再配置。

### Phase-1: PDF 生成コードの除去
3. `lib/submodules/tools.selection_markdown()` から HTML ↔︎ PDF 変換ブロックを削除し、Markdown 保存のみ残す。
4. `selection.py` で同関数を呼ぶ後の PDF 関連ログも削除。

### Phase-2: TTS 統合
5. `selection.py` CLI に `--tts` 等のオプション追加 (デフォルト off)。
6. 選評 Markdown 作成後、`if args.tts:` ブロックで `lib.tts.generate_speech()` を呼び、音声ファイルを生成。
7. デフォルトの speakerVoiceConfig を内部に持たせ、必要に応じて yaml で差し替え可能設計。

### Phase-3: 仕上げ
8. README / `install.md` を更新し、新しい使い方と依存を記述。
9. 不要になった `tts_tool.py` を削除 or 非推奨表記。
10. テスト: 選評 1 ファイルを対象に Markdown と音声が正しく出力されることを確認。

---

## 3. タスク分解 (最小粒度 To-Do)

### A. モジュール整理
1. [x] `lib/tts.py` を新規作成し、`tts_tool.py` の以下関数を移植
   * `generate_speech`
   * `convert_to_wav`
   * `parse_audio_mime_type`
   * `save_binary_file`
2. [x] `tts_tool.py` から上記関数を除去またはファイル自体を削除。

### B. PDF 関連削除
3. [x] `lib/submodules/tools.py` → `selection_markdown()`
   * `markdown` → `html` → `pdfkit.from_string()` のブロック削除
   * `pdf_out_path` ログ削除
4. [ ] `requirements.txt` から `pdfkit` を削除。(※ utakai モードで PDF 生成を継続するため保留)

### C. CLI 拡張
5. [x] `selection.py` に `--tts` (store_true)、`--voice-model` (default: gemini-2.5-pro-preview-tts) などを追加。
6. [x] Markdown → ラジオ原稿生成 → TTS の 2 段処理を追加
7. [x] 原稿を `basename.radio_script.txt`、音声を `basename.[ext]` として保存。

### D. ドキュメント更新
8. [x] README.md → 選評モードの例を Markdown＋TTS へ更新。
9. [ ] `install.md` → 依存ライブラリ／環境変数 (GOOGLE_API_KEY) を明記。

### E. テスト & CI
10. [ ] 手動テスト: demo CSV で `--tts` オン・オフ実行。
11. [ ] Pre-commit & 既存テストが通ること確認。
12. [x] Gemini 呼び出し後の待機時間 (`wait_sec`, default 20s) を YAML で調整可能に

---

以上を実施すれば、`selection.py` 単体で「Markdown の選評」＋「音声ガイド」生成が可能になります。
