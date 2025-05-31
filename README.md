# Utayomi
短歌の一覧を指定したLLMに入力し、評を生成するシステムです。  
* 設計・作成:
    * ef_utakata(https://x.com/ef_utakata)

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

* 2025年5月31日: 0.9.0 公開
    * 選評モードにラジオ番組風原稿生成＋Gemini TTS 音声出力フロー(--tts)を追加
    * 選評モードのPDF出力を廃止し Markdown のみへ変更
    * generate_script_prompt.md, tts_generation_config.yaml を追加

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
* 先頭行(header): No,Content,Author,Author_comment,Human_comment
    * No: 通し番号(1から順番)
    * Content: 短歌
    * Author: 作者名
    * Author_comment: 作者コメント
    * Human_comment: AI評を確認してコメントを付与する場合に使う列(オプション)

自作短歌を用いた入力例はinput/demoディレクトリ内にあります。

* input/ef_test_free.csv: 自由詠
* input/ef_test_theme.csv: 題詠（お題：「海」）
* input/ef_test_theme_sea_human_comment.csv: 自由詠、AI評に対するコメントを入力した例

これらをシステム上の対応モデルに入力して生成したコメントは、output/demoディレクトリ内にあります。

* input/ef_test_free_Ninja-v2-7b.csv:
    * 自由詠(歌会モードで出力された列を含む)

* input/ef_test_theme_Ninja-v2-7b.csv:
    * 題詠（お題：「海」）

* input/ef_test_theme_sea_human_comment_Ninja-v2-7b.csv:
    * AI評に対するコメントを入力したもの

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
出力結果は Markdown (`*.selection.md`) で保存されます。`--tts` フラグを付けると、
1. Markdown をもとに Gemini が **ラジオ番組風の原稿** を生成 (`*.radio_script.txt`)
2. その原稿を Gemini TTS で音声化し WAV / Ogg 等の音声ファイル (`*.selection.wav` など)

までを自動で行います。選評モードでの PDF 生成は廃止されました。

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


