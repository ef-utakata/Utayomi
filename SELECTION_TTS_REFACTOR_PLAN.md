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

### B. Google GenAI SDK への移行 (NEW)
3. [ ] 依存を **`google-generativeai` → `google-genai (>=0.8.5)`** に置換し、`requirements.txt` を更新。
4. [ ] `lib/tts.py` を新 SDK に完全準拠させる。
    * `import google.genai as genai` へ変更。
    * `client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))`。
    * `client.models.generate_content()` を使用。
    * `types.VoiceConfig`, `types.PrebuiltVoiceConfig`, `types.SpeakerVoiceConfig` 構造へ移行。
5. [ ] MIME type (`audio/L16;rate=24000`) など、新仕様に合わせて `convert_to_wav()` を確認。

### C. PDF 関連削除
6. [x] `lib/submodules/tools.selection_markdown()` から PDF 生成ブロック削除。
7. [ ] `requirements.txt` から `pdfkit` を削除。（utakai モードの仕様が固まるまで保留）

### D. CLI & 設定
8. [x] `selection.py` に `--tts`, `--voice-model` などを追加。
9. [x] ラジオ原稿 (`basename.radio_script.txt`) → TTS (`basename.[ext]`) の流れを実装。
10. [x] 出力ファイル名を `{input}_{a}_{i}` ベースで統一。
11. [x] `config/tts_generation_config.yaml` の `model_name` デフォルトを `gemini-2.5-flash-preview-05-20` に変更。
12. [ ] `selection.py` の `--voice-model` デフォルトも同モデルへ変更。

### E. ドキュメント更新
13. [x] README.md を最新フロー・命名規約に更新。
14. [ ] install.md に「旧 SDK 削除 / 新 SDK インストール」手順を追記。

### F. テスト & CI
15. [ ] `input/April22.csv` で `--tts` 実行し、音声ファイルが正常生成されることを確認。
16. [ ] pre-commit / 自動テストを通過させる。

### G. テスト自動化 (TTS モジュール)
17. [ ] `tests/` ディレクトリを新規作成し、以下を配置する。
    * `tests/dummy_script.txt` — 短いテキスト（例: "Hello world"）
    * `tests/test_tts.py` —
        - `pytest` ベースで `lib.tts.generate_speech()` を呼び出す
        - GOOGLE_API_KEY が未設定なら `pytest.skip()` でスキップ
        - 生成された音声ファイルの存在と WAV ヘッダー長を簡易検証
18. [ ] `requirements.txt` に `pytest` を追加。
19. [ ] CI / pre-commit に `pytest` 実行ジョブを追加して回帰を検知。
20. [ ] `lib/tts.py` の API 呼び出しを **config=…** 方式へ統一し、テストが通ることを確認。

---

最新 SDK へ移行完了後、`selection.py` 単体で「Markdown の選評」＋「音声ガイド」生成が安定して動作します。
