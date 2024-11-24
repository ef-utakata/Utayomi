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

ver = """Utayomi-selection Version: 0.1.0
設計: ef_utakata
"""

parser = argparse.ArgumentParser(description="""Utayomi: 入力された短歌についてLLMが選を行うシステムです。設計: ef_utakata """)

# 必須引数
parser.add_argument('input', help='入力短歌一覧のパス(csv形式で入力)')
parser.add_argument('output', help='出力先ディレクトリのパス(csv形式で出力)')
parser.add_argument('-c','--config', default='./model_selection_conf.yaml', help='利用モデルの入力設定ファイル(yaml形式)')
parser.add_argument('-i','--identifier', help='入力設定ファイル内の設定識別子(--listで一覧を確認可能)')

# お題の指定
parser.add_argument('-t', '--theme',  help='お題(入力がない場合自由詠)', default=0)

# 選ぶ短歌の数
parser.add_argument('-n', '--number',  help='選ぶ短歌の数', default=5)

# 選評対象(出力に記載)
parser.add_argument('-a', '--application',  help='応募企画・応募分野の名称', default="毎月短歌")

# configの内容確認用
parser.add_argument('--list', help='-cで指定した入力設定ファイルの一覧を表示', action='store_true')
# version出力
parser.add_argument('-V', '--version', action='store_true', help='バージョン情報の表示')

args = parser.parse_args()    # 4. 引数を解析

# version番号の表示
if (args.version):
    print(ver)
    exit()

# お題がある場合は指定、ない場合は0(自由詠)
theme = 0
if not (args.theme == None):
    theme = args.theme   

# 選ぶ短歌の数
num = args.number

# 開始時間記録
start_A = datetime.datetime.now()

# configの引数一覧を表示
if (args.list):
    print("[MESSAGE]: 現在、以下のモデルが利用可能です。-i に各モデルの識別子を入力して切り替え可能です。")
    with open(args.config, 'r') as yml:
        yml = yaml.safe_load(yml)
        for key in yml.keys():
            print(key)
            
    print("\n[MESSAGE]: 現在、以下のモデルがキャッシュされています。キャッシュされていないモデルは初回実行時に自動でダウンロードされます。")
    subprocess.run('huggingface-cli scan-cache', shell=True)
    subprocess.run('find ./models -name "*.gguf"', shell=True)
    exit()


# model_typeごとにモジュールを読み込んで評生成
ident = args.identifier
yml = []

# configファイルを読み込み, identifierに応じた設定を読み込む
with open(args.config, 'r') as yml:
    yml = yaml.safe_load(yml)
    if not ident in yml :
        print(Fore.RED + "[ERROR]: identifer [" + str(ident) + "] は入力設定ファイルに登録されていません。--listで出力される一覧と-i で入力した識別子を確認してください。\n"  + Fore.RESET)
        exit()
        
    print(Fore.YELLOW + "[MESSAGE]:入力設定ファイルを読み込んでいます...\n\tmodel: " + ident + Fore.RESET)
    for elem in yml[ident]:
        print(Fore.YELLOW +"\t" +elem + ":" + str(yml[ident][elem]) + Fore.RESET)

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

selection_markdown(ident, output, df_temp_path)


