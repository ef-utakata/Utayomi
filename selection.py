import argparse
import datetime
import yaml
import os
import subprocess
import pandas as pd
import colorama
from colorama import Fore, Back, Style

import torch
# 標準ライブラリ
import re

from transformers import AutoTokenizer, AutoModelForCausalLM

# 自作 TTS モジュール
from lib.tts import generate_speech

# libの自作モジュールをインポート
from lib.submodules.tools import *
from lib.submodules.model_load import *
from lib.tanka_critic import *
from lib.cli import get_common_parser, handle_version, handle_list, load_config

ver = """Utayomi-selection Version: 0.2.1
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
parser.add_argument('--voice-model', default='gemini-2.5-pro-preview-tts', help='TTS に使用する Gemini モデル名')
parser.add_argument('--tts-config', default='./tts_generation_config.yaml', help='原稿生成用の設定ファイル')

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
yml = load_config(args.config, ident)
handle_list(args)

# load model configuration
yml = load_config(args.config, ident)

# 入力ファイルと出力先のパスを指定（途中生成がある場合はその部分から再開）
df, df_temp_path, df_merged = output_preprocess(args.input, 
                                                args.output,
                                                "first",
                                                ident)

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
if (ident == "Gemini"):
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
# 出力 Markdown の保存
# --------------------------------------------------
output = attach_authors_to_output(output, df)

# markdown 保存用にダミー CSV パスを構築（tools.selection_markdown は拡張子を除いてベース名を利用）
markdown_dummy_csv = os.path.join(os.path.dirname(df_temp_path), f"{common_basename}.csv")

selection_markdown(ident, output, markdown_dummy_csv)

# -----------------------------------------------------------------
# TTS 出力 (オプション)
# -----------------------------------------------------------------
if args.tts:
    try:
        output_dir = os.path.dirname(df_temp_path)

        md_path = os.path.join(output_dir, f"{common_basename}.md")

        if not os.path.exists(md_path):
            print(Fore.RED + f"[ERROR]: Markdown ファイル {md_path} が見つかりません。TTS をスキップします。" + Fore.RESET)
        else:
            with open(md_path, 'r', encoding='utf-8') as f:
                selection_md = f.read()

            # --- Radio script generation ---------------------------------
            import yaml
            from lib.tts import generate_radio_script

            if not os.path.exists(args.tts_config):
                print(Fore.RED + f"[ERROR]: TTS 設定ファイル {args.tts_config} が見つかりません。TTS をスキップします。" + Fore.RESET)
                raise FileNotFoundError

            with open(args.tts_config, 'r', encoding='utf-8') as yml_file:
                tts_conf = yaml.safe_load(yml_file)

            script_conf = tts_conf.get('script_generation', {})
            template_path = script_conf.get('prompt_template', './generate_script_prompt.md')
            script_model = script_conf.get('model_name', 'gemini-2.5-pro-preview')
            script_temp = script_conf.get('temperature', 0.7)
            script_wait = script_conf.get('wait_sec', 20)

            # create radio script using Gemini
            radio_script = generate_radio_script(
                selection_markdown=selection_md,
                template_path=template_path,
                model_name=script_model,
                temperature=script_temp,
                wait_sec=script_wait,
                theme=theme,
            )

            # save generated script for reference
            script_path = os.path.join(output_dir, f"{common_basename}.radio_script.txt")
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(radio_script)

            print(Fore.YELLOW + f"[MESSAGE]: ラジオ原稿を生成しました → {script_path}" + Fore.RESET)

            # --- TTS ------------------------------------------------------
            speech_conf = tts_conf.get('speech_generation', {})
            speech_wait = speech_conf.get('wait_sec', 20)

            # ------------------------------------------------------------------
            # Build speaker / voice list (configurable)
            # ------------------------------------------------------------------
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

            output_base = os.path.join(output_dir, common_basename)

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


