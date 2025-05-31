import argparse
import datetime
import yaml
import os
import subprocess
import pandas as pd
import colorama
from colorama import Fore, Back, Style

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 自作 TTS モジュール
from lib.tts import generate_speech

# libの自作モジュールをインポート
from lib.submodules.tools import *
from lib.submodules.model_load import *
from lib.tanka_critic import *
from lib.cli import get_common_parser, handle_version, handle_list, load_config

ver = """Utayomi-selection Version: 0.2.0
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
start_A = datetime.datetime.now()
handle_list(args)

ident = args.identifier
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
    for content, author in sorted(zip(df['Content'], df['Author']), key=lambda x: len(x[0]), reverse=True):
        if content and content in new:
            new = new.replace(content, f"{content}（作者：{author}）", 1)
    return new

output = attach_authors_to_output(output, df)
selection_markdown(ident, output, df_temp_path)

# -----------------------------------------------------------------
# TTS 出力 (オプション)
# -----------------------------------------------------------------
if args.tts:
    try:
        basename_without_ext = os.path.splitext(os.path.basename(df_temp_path))[0]
        dirname = os.path.splitext(os.path.dirname(df_temp_path))[0]
        md_path = dirname + "/" + basename_without_ext + ".selection.md"

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

            # create radio script using Gemini
            radio_script = generate_radio_script(
                selection_markdown=selection_md,
                template_path=template_path,
                model_name=script_model,
                temperature=script_temp,
            )

            # save generated script for reference
            script_path = dirname + "/" + basename_without_ext + ".radio_script.txt"
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(radio_script)

            print(Fore.YELLOW + f"[MESSAGE]: ラジオ原稿を生成しました → {script_path}" + Fore.RESET)

            # --- TTS ------------------------------------------------------
            output_base = dirname + "/" + basename_without_ext + ".selection"

            print(Fore.YELLOW + "[MESSAGE]: TTS を実行しています…" + Fore.RESET)
            audio_file = generate_speech(
                script_text=radio_script,
                output_basename=output_base,
                model_name=args.voice_model,
            )
            print(Fore.GREEN + f"[MESSAGE]: 音声ファイルを生成しました → {audio_file}" + Fore.RESET)
    except Exception as e:
        print(Fore.RED + f"[ERROR]: TTS 生成中に例外が発生しました: {e}" + Fore.RESET)


