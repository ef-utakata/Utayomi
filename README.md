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
* 2024年6月29日: 0.3.0 公開
    * 歌会モード（複数LLMの出力をGeminiにファシリテーションさせるモード）追加

## ToDo
- [ ] 連作入力対応
- [x] 複数LLMの出力をファシリテーションするモード
- [ ] 再生成モード（指定番号を再生成）
- [ ] コンテナ化

## 対応モデル
以下の形式のモデルに対応しています。
1. huggingface形式のモデル(transformerを使用)
2. gguf形式の量子化モデル(llama-cpp-pythonを使用)
3. openAI APIで利用できるモデル(GPT-4oなど)
4. cohere APIで利用できるモデル(Command r+)
5. google.generativeai APIで利用できるモデル(Gemini-1.5-proなど)

2024年6月29日時点で、以下のモデルを用いた入力短歌へのコメントの出力が可能です。

* Umievo-itr012-Gleipnir-7B
    * https://huggingface.co/umiyuki/Umievo-itr012-Gleipnir-7B/tree/main

* Oumuamua-7b-instruct-v2
    * https://huggingface.co/nitky/Oumuamua-7b-instruct-v2

* Phi-3-mini, Phi-3-medium
    * https://huggingface.co/microsoft

* Ninja-v1-RP  
    * https://huggingface.co/Aratako/Ninja-v1-RP

* Ninja-V2-7B  
    * https://huggingface.co/Local-Novel-LLM-project/Ninja-V2-7B

* Llama-3-elyza-jp-8b
    * https://huggingface.co/elyza/Llama-3-ELYZA-JP-8B-GGUF

* Command-r-plus（API key必要）  
    * https://huggingface.co/CohereForAI/c4ai-command-r-plus

* Gemini(API key必要、1.5-pro, 1.5-flash, 1.0-pro, gemini-pro の4つを自動で切り替え)  
    * https://gemini.google.com/?hl=ja

* GPT-4o（API key必要）  
    * https://platform.openai.com/docs/overview

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

* input/ef_test_free_Ninja-v2-7b.csv: 自由詠
* input/ef_test_theme_Ninja-v2-7b.csv: 題詠（お題：「海」）の例
* input/ef_test_theme_sea_human_comment_Ninja-v2-7b.csv: 題詠の出力されたAI評に対するコメントを入力した例

## 出力ファイルの記述形式
出力フォーマット:csv(UTF-8)
* 先頭行(header):No,Tanka,Author,Author_comment,LLM identifier
* No: 通し番号(1から順番)
* Tanka: 短歌
* Author: 作者名
* Author_comment: 作者コメント
* LLM identifier: LLMによるコメント

## 歌会モード
複数のLLMからのコメントをGeminiに入力し、共通点や相違点についての要約を出力するモードです。  
引数mに"utakai"を指定、iをGeminiに設定し、入力ファイルを各LLMからのコメントが記述されたCSVを指定すると実行されます。
notebook中に実行例を記載しています。  

