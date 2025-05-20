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

# libの自作モジュールをインポート
from lib.submodules.tools import *
from lib.submodules.model_load import *
from lib.tanka_critic import *
from lib.cli import get_common_parser, handle_version, handle_list, load_config

ver = """Utayomi-selection Version: 0.1.0
設計: ef_utakata
"""

parser = get_common_parser(
    description="""Utayomi: 入力された短歌についてLLMが選を行うシステムです。設計: ef_utakata """,
    default_config='./model_selection_conf.yaml'
)
parser.add_argument('-n', '--number', help='選ぶ短歌の数', default=5)
parser.add_argument('-a', '--application', help='応募企画・応募分野の名称', default="毎月短歌")

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


