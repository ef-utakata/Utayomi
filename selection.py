import argparse
import datetime
import yaml
import os
import shutil
import subprocess
from typing import Any, Optional

import pandas as pd
import colorama
from colorama import Fore, Back, Style

import torch
# 標準ライブラリ
import re

from transformers import AutoTokenizer, AutoModelForCausalLM

# 自作 TTS モジュール
from lib.tts import generate_speech, generate_radio_script

# libの自作モジュールをインポート
from lib.submodules.tools import *
from lib.submodules.model_load import *
from lib.tanka_critic import *
from lib.cli import get_common_parser, handle_version, handle_list, load_config
from lib.report_generator import generate_reproducibility_report

ver = """Utayomi-selection Version: 1.3.2
設計: ef_utakata
"""

parser = get_common_parser(
    description="""Utayomi: 入力された短歌についてLLMが選を行うシステムです。設計: ef_utakata """,
    default_config='./model_selection_conf.yaml'
)
parser.add_argument('-n', '--number', help='選ぶ短歌の数', default=5)
parser.add_argument('-a', '--application', help='応募企画・応募分野の名称', default="毎月短歌")
# TTS 連携オプション
parser.add_argument('--tts', action='store_true', help='選評MarkdownをTTSで音声化しファイル出力する')
parser.add_argument('--voice-model', default='gemini-2.5-pro-preview-tts', help='TTS に使用する Gemini モデル名（課金設定のあるAPIキーが必要）')
parser.add_argument('--tts-config', default='./tts_generation_config.yaml', help='原稿生成用の設定ファイル')
# デバッグオプション
parser.add_argument('--debug', action='store_true', help='デバッグモード: LLMからの生の出力も保存する')
# 連作オプション
parser.add_argument('--series', action='store_true', help='連作モード: 連作データとして処理する')

args = parser.parse_args()
handle_version(args, ver)
theme = args.theme
num = args.number

# --------------------------------------------------
# ファイル名に使用する共通 basename を生成
# {入力ファイルのbasename}_{引数aの値}_{引数iの値}
# --------------------------------------------------
input_basename = os.path.splitext(os.path.basename(args.input))[0]

# `application` はファイル名に使えない文字（スペース、スラッシュなど）が含まれる
# 可能性があるため簡易的に置換しておく
application_raw = args.application if args.application else "application"
application_sanitized = re.sub(r"[\s/\\]", "_", application_raw)

# モデル識別子は必須引数なので存在する前提
ident = args.identifier

common_basename = f"{input_basename}_{application_sanitized}_{ident}"
start_A = datetime.datetime.now()
output_dir = prepare_output_directory(args.output)
args.output = output_dir
yml = load_config(args.config, ident)
model_details_entry = yml.get(ident, {}) if isinstance(yml, dict) else {}

def stringify_model_details(details: Any) -> Optional[str]:
    """Convert model_path definitions into a human-readable string."""
    if details is None:
        return None
    if isinstance(details, dict):
        ordered_keys = sorted(details.keys())
        values = [str(details[key]) for key in ordered_keys]
        return ", ".join(values)
    if isinstance(details, (list, tuple, set)):
        return ", ".join(str(item) for item in details)
    return str(details)


def prepare_output_directory(path: str) -> str:
    """Ensure the output directory exists and is empty."""
    if not path:
        raise ValueError("Output directory path is empty.")

    abs_path = os.path.abspath(path)

    if os.path.exists(abs_path):
        if os.path.isdir(abs_path):
            shutil.rmtree(abs_path)
        else:
            os.remove(abs_path)

    os.makedirs(abs_path, exist_ok=True)
    print(Fore.YELLOW + f"[MESSAGE]: 出力ディレクトリ[{abs_path}]を初期化します..." + Fore.RESET)
    return abs_path

model_details = stringify_model_details(
    model_details_entry.get("model_path") if isinstance(model_details_entry, dict) else None
)
handle_list(args)

# load model configuration
yml = load_config(args.config, ident)

# 入力ファイルと出力先のパスを指定（途中生成がある場合はその部分から再開）
if args.series:
    # 連作モードの場合は、カラムを保持したままの生の読み込み
    df = pd.read_csv(args.input)
    
    # No列がない場合は自動で追加
    if 'No' not in df.columns:
        print(Fore.YELLOW + "[MESSAGE]: No列が見つかりません。自動で通し番号を追加します..." + Fore.RESET)
        df.insert(0, 'No', range(1, len(df) + 1))
    
    # Author列がない場合は空文字列で埋める
    if 'Author' not in df.columns:
        print(Fore.YELLOW + "[MESSAGE]: Author列が見つかりません。空文字列で埋めます..." + Fore.RESET)
        df['Author'] = ''
    
    # Author_comment列がない場合は空文字列で埋める
    if 'Author_comment' not in df.columns:
        print(Fore.YELLOW + "[MESSAGE]: Author_comment列が見つかりません。空文字列で埋めます..." + Fore.RESET)
        df['Author_comment'] = ''
    
    df = df.fillna("")
    df_temp_path = os.path.join(args.output, f"{common_basename}.temp.csv")
    df_merged = df
else:
    # 従来の単作モードの処理
    df, df_temp_path, df_merged = output_preprocess(args.input, 
                                                    args.output,
                                                    "first",
                                                    ident)

# 連作処理分岐
if args.series:
    # 連作モード
    from lib.series_processor import SeriesProcessor
    from lib.tanka_critic import gemini_series_select
    
    # 連作モードでも列名の正規化を適用
    from lib.submodules.tools import normalize_column_names
    df = normalize_column_names(df)
    
    print(Fore.YELLOW + f"[MESSAGE]: 連作モードで{len(df)}作品を処理します。" + Fore.RESET)
    
    # 連作データ処理
    print(Fore.CYAN + f"[DEBUG]: 入力データの列: {list(df.columns)}" + Fore.RESET)
    eiso_count_col = 'Eiso_count' if 'Eiso_count' in df.columns else 'eiso_count'
    print(Fore.CYAN + f"[DEBUG]: Eiso_count列の値: {df[eiso_count_col].tolist() if eiso_count_col in df.columns else 'なし'}" + Fore.RESET)
    
    processor = SeriesProcessor()
    processed_df = processor.process_series_csv(df)
    
    # 処理要約表示
    summary = processor.get_series_summary()
    print(Fore.CYAN + f"[INFO]: 連作{summary['total_series']}作品を展開、計{len(processed_df)}首を処理" + Fore.RESET)
    
    # 連作用プロンプト生成
    series_content = processor.generate_series_prompt_content()
    
    # 選を生成（連作対応）
    result = ""  # 連作モードでは使用しない
    output = "出力エラー"
else:
    # 従来の単作モード
    print(Fore.YELLOW + f"[MESSAGE]: {ident}に{len(df)}首の短歌を入力し、選を行います。" + Fore.RESET)
    
    result = process_content(df)
    output = "出力エラー"

# model typeを読み込み、trf/ggufならモデルをロード, それ以外は詳細なモデルを指定
model_type = yml[ident]["model_type"]
model =  yml[ident]["model_path"]
tokenizer = 0
if (model_type == "trf"):
    model, tokenizer = trf_load(yml[ident])
elif(model_type == "gguf"):
    model, tokenizer = gguf_load(yml[ident])

# 選を生成
if (model_type == "gemini"):
    if args.series:
        # 連作対応Gemini選評
        output = gemini_series_select(yml[ident], df, result, num, theme, series_content)
    else:
        # 従来の単作Gemini選評
        output = gemini_select(yml[ident], df, result, num, theme)
    print(output)
    
elif (ident == "Mistral-Nemo-Japanese"):
    output = nemo_select(yml[ident], model, tokenizer, df, result, num, theme)

elif (ident == "Mistral-Nemo-Japanese-gguf"):
    output = nemo_select(yml[ident], model, tokenizer, df, result, num, theme)

# 出力をmarkdown形式に変換、PDF生成
application = args.application
output = f"""# {application}
## {ident}による{num}首の選評:
""" + output

def attach_authors_to_output(text, df):
    new = text
    # Author_URL列が存在するかチェック
    has_url_column = 'Author_URL' in df.columns
    
    # Content, Author, Author_URLを組み合わせてソート
    if has_url_column:
        content_author_url = list(zip(df['Content'], df['Author'], df['Author_URL']))
    else:
        content_author_url = list(zip(df['Content'], df['Author'], [None] * len(df)))
    
    # 長い順にソート（部分文字列の置換問題を回避）
    sorted_entries = sorted(content_author_url, key=lambda x: len(x[0]) if x[0] else 0, reverse=True)
    
    for content, author, author_url in sorted_entries:
        if content and content in new:
            # Author_URLがある場合はMarkdownリンクを作成
            if author_url and str(author_url).strip() and str(author_url).strip().lower() != 'nan':
                author_link = f"[{author}]({author_url})"
            else:
                author_link = author
            
            new = new.replace(content, f"{content}（作者：{author_link}）", 1)
    return new

#
# デバッグモード: 生の LLM 出力を保存
# --------------------------------------------------
if args.debug:
    raw_output_path = os.path.join(args.output, f"{common_basename}_raw_output.md")
    print(f"{Fore.YELLOW}[DEBUG]: LLMからの生出力を保存します: {raw_output_path}{Style.RESET_ALL}")
    with open(raw_output_path, 'w', encoding='utf-8') as f:
        # ヘッダーを除いた生の出力のみを保存
        raw_content = output.split("## ")[1].split("首の選評:\n", 1)[1] if "## " in output and "首の選評:\n" in output else output
        f.write(raw_content)

#
# 出力 Markdown の保存
# --------------------------------------------------
output = attach_authors_to_output(output, df)

# 再現性レポートの生成
reproducibility_report = generate_reproducibility_report(
    version=ver,
    model_identifier=ident,
    config_file=args.config,
    model_details=model_details,
    application=args.application if args.application != "毎月短歌" else None,
    theme=theme if theme != "0" else None,
    num_selections=int(num),
    is_series=args.series,
    is_tts=args.tts,
    is_debug=args.debug
)

# markdown 保存用にダミー CSV パスを構築（tools.selection_markdown は拡張子を除いてベース名を利用）
markdown_dummy_csv = os.path.join(os.path.dirname(df_temp_path), f"{common_basename}.csv")

selection_markdown(ident, output, markdown_dummy_csv, report_content=reproducibility_report)

# -----------------------------------------------------------------
result_dir = os.path.dirname(df_temp_path)
md_path = os.path.join(result_dir, f"{common_basename}.md")
script_path = os.path.join(result_dir, f"{common_basename}.radio_script.txt")
radio_script = None
tts_conf = None

try:
    if not os.path.exists(md_path):
        raise FileNotFoundError(f"Markdown ファイル {md_path} が見つかりません。")

    with open(md_path, 'r', encoding='utf-8') as f:
        selection_md = f.read()

    if not os.path.exists(args.tts_config):
        raise FileNotFoundError(f"TTS 設定ファイル {args.tts_config} が見つかりません。")

    with open(args.tts_config, 'r', encoding='utf-8') as yml_file:
        tts_conf = yaml.safe_load(yml_file) or {}

    script_conf = tts_conf.get('script_generation', {})
    template_path = script_conf.get('prompt_template', './generate_script_prompt.md')
    script_model = script_conf.get('model_name', 'gemini-2.5-pro-preview')
    script_temp = script_conf.get('temperature', 0.7)
    script_wait = script_conf.get('wait_sec', 20)

    radio_script = generate_radio_script(
        selection_markdown=selection_md,
        template_path=template_path,
        model_name=script_model,
        temperature=script_temp,
        wait_sec=script_wait,
        theme=theme,
        application=application,
        is_series=args.series,
    )

    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(radio_script)

    print(Fore.YELLOW + f"[MESSAGE]: ラジオ原稿を生成しました → {script_path}" + Fore.RESET)
except FileNotFoundError as e:
    print(Fore.RED + f"[ERROR]: {e}" + Fore.RESET)
except Exception as e:
    print(Fore.RED + f"[ERROR]: ラジオ原稿の生成中に例外が発生しました: {e}" + Fore.RESET)

# -----------------------------------------------------------------
# TTS 出力 (オプション)
# -----------------------------------------------------------------
if args.tts:
    if not radio_script or not tts_conf:
        print(Fore.RED + "[ERROR]: ラジオ原稿またはTTS設定の準備に失敗したため、音声生成をスキップします。" + Fore.RESET)
    else:
        try:
            from lib.env_loader import has_paid_api_key, test_tts_api_key

            # --- TTS API Key Check ----------------------------------------
            if not has_paid_api_key():
                print(Fore.YELLOW + "[WARNING]: 課金設定のあるAPIキー (GOOGLE_API_KEY_PAID) が設定されていません。" + Fore.RESET)
                print(Fore.YELLOW + "[WARNING]: TTS音声生成をスキップし、ラジオ原稿の生成までで完了します。" + Fore.RESET)
                print(Fore.CYAN + "[INFO]: TTS機能を使用するには、.envファイルにGOOGLE_API_KEY_PAIDを設定してください。" + Fore.RESET)
            else:
                print(Fore.YELLOW + "[MESSAGE]: TTS APIキーの有効性をテストしています…" + Fore.RESET)
                if not test_tts_api_key():
                    print(Fore.YELLOW + "[WARNING]: 課金設定のあるAPIキーでTTS機能が利用できません。" + Fore.RESET)
                    print(Fore.YELLOW + "[WARNING]: TTS音声生成をスキップし、ラジオ原稿の生成までで完了します。" + Fore.RESET)
                    print(Fore.CYAN + "[INFO]: Google AI StudioでAPIキーの課金設定を確認してください。" + Fore.RESET)
                else:
                    speech_conf = tts_conf.get('speech_generation', {})
                    speech_wait = speech_conf.get('wait_sec', 20)
                    voices_conf = speech_conf.get(
                        'voices',
                        [
                            {"speaker": "Speaker 1", "voice_name": "Charon"},
                            {"speaker": "Speaker 2", "voice_name": "Gacrux"},
                        ],
                    )

                    from google.genai import types as gtypes

                    speaker_voice_configs = [
                        gtypes.SpeakerVoiceConfig(
                            speaker=v.get("speaker", f"speaker_{idx}"),
                            voice_config=gtypes.VoiceConfig(
                                prebuilt_voice_config=gtypes.PrebuiltVoiceConfig(
                                    voice_name=v.get("voice_name", "Charon")
                                )
                            ),
                        )
                        for idx, v in enumerate(voices_conf)
                    ]

                    output_base = os.path.join(result_dir, common_basename)

                    print(Fore.YELLOW + "[MESSAGE]: TTS を実行しています…" + Fore.RESET)
                    audio_file = generate_speech(
                        script_text=radio_script,
                        output_basename=output_base,
                        model_name=args.voice_model,
                        speaker_voice_configs=speaker_voice_configs,
                        wait_sec=speech_wait,
                    )
                    print(Fore.GREEN + f"[MESSAGE]: 音声ファイルを生成しました → {audio_file}" + Fore.RESET)
        except Exception as e:
            print(Fore.RED + f"[ERROR]: TTS 生成中に例外が発生しました: {e}" + Fore.RESET)
