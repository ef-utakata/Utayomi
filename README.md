# Utayomi
短歌の一覧を指定したLLMに入力し、評を生成するシステムです。  
* 設計・作成:
    * ef_utakata(https://x.com/ef_utakata)

## 現在の開発方針

2025 年 6 月時点、本リポジトリは **Gemini API を用いた「選評モード」** を
メインターゲットとして開発・保守を行っています。

* ローカル LLM（gguf / transformers など）を使った
  *全評モード*（短歌ごとのコメント生成）と
  *歌会モード*（複数モデルの評を要約するモード）は、
  安定版 0.8 系を最後に **いったん開発を休止** しています。
* それらのスクリプト・設定は残っていますが、動作確認や
  新機能追加は当面予定していません。利用される場合は
  「動けばラッキー」程度のサポートレベルになります。

最新の機能追加・バグ修正はすべて
**Gemini を使用した選評モード（`selection.py` + `--tts`）** に
集中している点をご承知おきください。

## 更新履歴
* 2024年6月22日: 0.1.0 公開
* 2024年6月29日: 0.2.0 公開
    * 対応モデルにLlama-3-elyza-jp-8bを追加
    * OumuamuaをGGUFモデルに変更
    * 複数モデルの入力の自動統合
* 2024年6月30日: 0.3.0 公開
    * 歌会モード（複数LLMの出力をGeminiにファシリテーションさせるモード）追加
* 2024年7月15日: 0.4.0 公開
    * 歌会モードのmarkdown出力に対応  
* 2024年7月25日: 0.5.0 公開
    * 対応モデルの追加, llama-cliで動作するモデルの実行に対応
* 2024年11月24日: 0.6.0 公開
    * LLMによる選評実施のスクリプトを追加、対応モデルやプロンプト設計を変更
* 2024年11月25日: 0.7.0 公開
    * 選評モードのCLIオプションを共通化（get_common_parser適用、--list/-V追加、-n/-a/-tオプション整理）
    * 選評出力に短歌の作者名を付与する機能を追加
    * READMEの選評モード使用例を更新
* 2025年5月20日: 0.8.0 公開
    * 前処理用Excel to CSV変換スクリプト(excel_to_csv.py)を追加
    * シートごとにCSVファイルを生成し、短歌内容・作者・作者コメント列の自動検出を実装
    * --encodingオプションでCSVの文字エンコーディングを指定可能

* 2025年5月31日: 1.0.0 公開
    * 選評モード: ラジオ番組風原稿生成＋Gemini TTS 音声出力 (--tts) を追加
    * 出力ファイル名を `{入力CSV名}_{-a値}_{-i値}.{拡張子}` へ統一
      - Markdown  `.md`
      - ラジオ原稿 `.radio_script.txt`
      - 音声ガイド `.wav` (API により変化あり)
    * PDF 出力を完全廃止
    * テンプレート `generate_script_prompt.md` に `{お題セクション}` プレースホルダを追加し
      `-t <お題>` 指定時に原稿へお題説明を自動挿入
    * 各種ドキュメント更新

* 2025年6月1日: 1.1.0 公開
    * TTS のデフォルトモデルを `gemini-2.5-pro-preview-tts` に変更
    * マルチスピーカー TTS に対応 (デフォルト: Speaker 1=Charon / Speaker 2=Gacrux)
      - `tts_generation_config.yaml` に `speech_generation.voices` を追加し
        YAML で簡単に話者・音色を差し替え可能
    * 旧 `google-generativeai` SDK を廃止し **`google-genai >=0.8.5`** へ移行
    * 単体テスト `tests/test_tts.py` を追加（API キーがある環境で音声生成を検証）

* 2025年6月19日: 1.1.2 公開
    * CSV前処理の堅牢性を向上: No列がない場合の自動追加、不足列の自動補完機能を追加
    * 選評出力での作者名Markdownリンク機能: Author_URL列がある場合、作者名をクリック可能リンクとして表示
    * gitignore設定の改善とコードベース整理

* 2025年6月19日: 1.1.3 公開
    * TTS生成時のGemini API互換性問題を修正（generation_config引数エラーの解決）
    * デバッグモード追加: `--debug`フラグでLLMからの生出力を中間ファイルとして保存
    * selection.pyの安定性とデバッグ性を向上

## 対応モデル
以下の形式のモデルに対応しています。
1. huggingface形式のモデル(transformerを使用)
2. gguf形式の量子化モデル(llama.cppまたはllama-cpp-pythonを使用)
3. openAI APIで利用できるモデル(GPT-4oなど)
4. cohere APIで利用できるモデル(Command r+)
5. google.generativeai APIで利用できるモデル(Gemini-1.5-proなど)

2024年7月25日時点で、以下のモデルを用いた入力短歌へのコメントの出力が可能です。


APIでアクセスするモデルを利用する場合は、それぞれのモデルの配布元からAPI keyを取得し、以下の環境変数に入力する必要があります。
* openAI: OPENAI_API_KEY
* cohere: COHERE_API_KEY
* Google: GOOGLE_API_KEY

pypeline.pyの実行前に、.bashrcに各値を入力するか、以下のコマンドでAPI keyを入力してください。  
notebook上で実行する場合は"API keyの入力"と記載のあるセルにkeyを入力してセルを実行すると一括入力されます。

```bash
export OPENAI_API_KEY="取得したAPI key"
export COHERE_API_KEY="取得したAPI key"
export GOOGLE_API_KEY="取得したAPI key"
```

短歌生成におけるモデルの指定や生成時の詳細な設定は、yaml形式のファイル(model_conf.yaml)で記述します。
引数-i でファイル内のどの設定を読み込むかを指定します。

以下のコマンドで、-i に入力可能な識別子一覧を表示できます。

```bash
python pipeline.py --list 
```

## 設定ファイルmodel_conf.yamlの記述方法
設定ファイル(model_conf.yaml)は利用可能なモデルを追加したり細かい設定を変更する場合などに開発者が編集しやすいようにするためのもので、
システムの利用のみの場合は特に編集する必要はありません。

## 前処理スクリプト: Excel to CSV

複数シートのExcelファイルを短歌選評システム用のCSVファイルに変換します。各シートごとにNo,Content,Author,Author_comment列を抽出し、シート名をファイル名としたCSVファイルを出力します。

```bash
python excel_to_csv.py input.xlsx output_directory [--encoding utf-8]
```

- `--encoding`: 出力CSVファイルの文字エンコーディング（デフォルト: utf-8）

生成されるCSVファイルには以下の列が含まれ、selection.pyやpipeline.pyの入力として利用できます。
* No: 通し番号(1から順番)
* Content: 短歌
* Author: 作者名
* Author_comment: 作者コメント

## 入力ファイルの記述方法
入力フォーマット:csv(UTF-8)ファイル(以下のフォーマットに従って記述されているもの)

### 基本形式
* 先頭行(header): No,Content,Author,Author_comment,Human_comment
    * **No**: 通し番号(1から順番) ※ない場合は自動で追加されます
    * **Content**: 短歌（必須）
    * **Author**: 作者名 ※ない場合は空文字列で補完されます
    * **Author_comment**: 作者コメント ※ない場合は空文字列で補完されます
    * **Human_comment**: AI評を確認してコメントを付与する場合に使う列(オプション)

### 拡張形式（選評モード用）
* 追加可能な列:
    * **Author_URL**: 作者のSNS/WebサイトURL（選評出力時に作者名がクリック可能リンクになります）
    * **Title**: 連作のタイトル（連作作品の場合）
    * **Eiso_count**: 連作の首数（連作作品の場合）
    * **Editor_memo**: 編集者メモ
    * **Create DateTime**: 作成日時
    * **LICENSE**: ライセンス情報

### サンプルデータ

**デモ用データ（input/demo/）:**
* `ef_test_free.csv`: 自由詠の例
* `ef_test_theme.csv`: 題詠（お題：「海」）の例
* `ef_test_theme_sea_human_comment.csv`: AI評に対するコメントを入力した例

### 独自データの利用

プロジェクト固有の短歌データがある場合は、`input/demo/`の形式を参考にCSVファイルを作成してください。

これらをシステム上の対応モデルに入力して生成したコメントは、output/demoディレクトリ内にあります。

## 出力ファイルの記述形式
出力フォーマット:csv(UTF-8)
* 先頭行(header):No,Tanka,Author,Author_comment,LLM identifier
* No: 通し番号(1から順番)
* Tanka: 短歌
* Author: 作者名
* Author_comment: 作者コメント
* LLM identifier: LLMによるコメント

## 全評モード
入力された短歌の一覧について、指定したLLMを用いてコメントを生成します。
短歌に添えられたコメントがある場合はコメントを読み込み、またお題がある場合はお題を踏まえてコメントを生成します。
```sh
python pipeline.py \
    -m first \ # 全評モード(defaultで指定されているので入力の必要はなし)
    -c ./model_conf.yaml \ # 読み込むモデルの設定ファイル
    -i Calm3-22B \ # 使用するモデルのidentifier
    -t お題 \ # 題詠・テーマ詠の場合(指定しなければ自由詠)
    ./output/demo/ \ # 結果の出力先ディレクトリ
    ./output/demo/ef_test_free_result.csv # 各LLMからの表を記載したcsvファイル
```


## 歌会モード
複数のLLMからのコメントをGeminiまたはEZO-Qwen2.5-72Bに入力し、共通点や相違点についての要約を出力するモードです。  
引数mに"utakai"を指定、iをGeminiまたはEZO-Qwen2.5-72Bに設定し、入力ファイルを各LLMからのコメントが記述されたCSVを指定すると実行されます。
以下のスクリプトを実行すると、出力先のディレクトリに各LLMからのコメントの要約をmarkdown形式のテキストとpdfファイルで出力します。

```sh
# 歌会モードで各コメントを要約
python pipeline.py \
    -m utakai \  # モード指定
    -c ./model_conf.yaml \ # 読み込むモデルの設定ファイル
    -i EZO-Qwen2.5-72B \ # 要約に使用するモデルのidentifier
    ./output/demo/ \ # 結果の出力先ディレクトリ
    ./output/demo/ef_test_free_result.csv # 各LLMからの表を記載したcsvファイル
```

## 選評モード
入力された短歌一覧を一度にLLMに入力し、指定した数の歌を選んでコメントを出力するスクリプトです。
2024年11月24日現在、入力コンテキスト長の長いモデル(Gemini, Mistral-Nemo-Japanese)でのみ実行可能です。
出力ファイル一式は **入力 CSV 名・応募区分(-a)・モデル識別子(-i)** を組み合わせた
共通 basename で保存されます。

例: `input/April22.csv`、`-a 4月自選`、`-i Gemini` の場合

```
output/
├─ April22_4月自選_Gemini.md                # 選評 Markdown
├─ April22_4月自選_Gemini.radio_script.txt  # ラジオ番組風原稿
└─ April22_4月自選_Gemini.wav               # 音声ガイド (拡張子は API に依存)
```

`--tts` を付けない場合は Markdown のみ生成されます。付けると上記 1→2 の流れ
（原稿生成 → TTS）が追加で実行されます。PDF 出力は廃止されました。

以下のコマンドで、-i に入力可能な設定識別子一覧を表示できます。

```bash
python selection.py --list
```

バージョン情報を表示するには、以下を実行します。

```bash
python selection.py -V
```

```sh
# 選評モードで短歌を選ぶ例 (Markdown のみ)
python selection.py \
    -c ./model_selection_conf.yaml \ # 選評モード用のモデル設定ファイル
    -i Mistral-Nemo-Japanese \ # 選評に使用するモデルのidentifier
    -t お題名 \ # お題指定(省略時は自由詠)
    -a 毎月短歌nn：yyyy部門 \ # 選評対象の企画の名称(出力結果に記載するもの)
    -n 8 \ # 選ぶ短歌の数
    ./output/demo/ \ # 結果の出力先ディレクトリ
    ./output/demo/ef_test_free_result.csv # 選評対象の短歌一覧CSVファイル
```

### TTS 付きで原稿・音声も生成する例

```bash
python selection.py \
    -c ./model_selection_conf.yaml \
    -i Gemini \                 # 原稿生成・TTS には Gemini を推奨
    -n 8 \
    --tts \                     # 音声化を有効化
    --tts-config ./tts_generation_config.yaml \  # 原稿用設定 (デフォルトは同パス)
    ./output/demo/ \
    ./output/demo/ef_test_free_result.csv
```

### デバッグモード（開発・トラブルシューティング用）

```bash
python selection.py \
    -c ./model_selection_conf.yaml \
    -i Gemini \
    -n 5 \
    --debug \                   # LLMからの生出力も中間ファイルとして保存
    ./output/demo/ \
    ./output/demo/ef_test_free_result.csv
```


