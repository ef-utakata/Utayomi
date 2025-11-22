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

ver = """Utayomi Version: 0.4.0
設計: ef_utakata
"""

# 共通CLI処理を抽出
parser = get_common_parser(
    description="""Utayomi: 入力された短歌についてLLMにより評を生成するシステムです。設計: ef_utakata """,
    default_config='./config/model_conf.yaml'
)
# pipeline-specific arguments
parser.add_argument(
    '-r', '--regen', help='再生成対象のNoリスト(regenモードで使用、yaml形式)'
)
parser.add_argument(
    '-m', '--mode', help='実行モード{first(単作) / rensak(連作) /utakai(要約) /selection(選)} default: first', default='first'
)

args = parser.parse_args()
handle_version(args, ver)
theme = args.theme
start_A = datetime.datetime.now()
handle_list(args)

ident = args.identifier
yml = load_config(args.config, ident)

# 登録モードの確認
mode_input = ["first","utakai","rensak","selection"]
mode_list = ", ".join(mode_input)
if not args.mode in mode_input:
    print(Fore.RED + f"[ERROR]: [{args.mode}] は入力可能なモードではありません。-m 引数は[{mode_list}のいずれかを入力してください。]\n"  + Fore.RESET)
    exit()
else:
    print(Fore.YELLOW + f"[MESSAGE]: モード[{args.mode}]で処理を実行します... \tmodel: " + ident + Fore.RESET)

# 入力ファイルと出力先のパスを指定（途中生成がある場合はその部分から再開）
df, df_temp_path, df_merged = output_preprocess(args.input, 
                                                args.output,
                                                args.mode,
                                                ident)

# model typeを読み込み、trf/ggufならモデルをロード, それ以外は詳細なモデルを指定
model_type = yml[ident]["model_type"]
model =  yml[ident]["model_path"]
tokenizer = 0
if (model_type == "trf"):
    model, tokenizer = trf_load(yml[ident])
elif(model_type == "gguf"):
    model, tokenizer = gguf_load(yml[ident])
elif(model_type == "llamacpp"):
    model = yml[ident]["model_path"]
    tokenizer = "null"

# 解析状況出力のための数値を格納
total_len = len(df)
count_len = 0

# for debug
#print(df)


# 各行を読み込んでプロンプト生成、モデルに入力、出力を確認して再生成
for index, row in df.iterrows():
    
    # 経過ログ出力のためのカウンターを回す
    count_len += 1
    
    # 再生成フラグの初期値をセット         
    regen = [1]
    regen_count = 0
        
    # 再生成フラグがゼロにならない限り推論を実行
    while (len(regen) > 0):
        regen = []
        start_B = datetime.datetime.now()

        # seed指定で再生成は未実装
        seed_number = 0

        # Human-assistedの設定
        Human_comment = "NaN"
        if ("Human_comment" in row):
            Human_comment = row['Human_comment']

        # for debug
        #print(row)

        seed = 0
        output = 0
        df_result = pd.DataFrame()
            
        # 初回生成モード
        if (args.mode == "first"):
            # 短歌評を出力、推論に使用したシード値と中身を取得
            seed, output = tanka_critic(ident,                 # modelごとに固有の処理が必要になった場合に備えて識別子を渡す
                                        yml[ident],            # configをまとめてモジュールに渡す
                                        theme,                 # お題
                                        row['Content'],        # 短歌
                                        row["Author"],         # 作者名
                                        row['Author_comment'], # 作者コメント
                                        Human_comment,         # 補助コメント
                                        model,                 # model pathまたはロードしたモデル
                                        tokenizer,             # ロードしたtokenaizerまたは0
                                        row['No'],
                                        seed_number)

            # 処理時間の出力
            end = datetime.datetime.now()
            result1 = str(end-start_B)[0:7]
            result2 = str(end-start_A)[0:7]
            print(Fore.GREEN + "\n[MESSAGE]: 生成時間:" + result1  + Fore.RESET)
            print(Fore.GREEN + "[MESSAGE]: 合計経過時間" + result2 + " (" + str(count_len) + "/" + str(total_len) + ")" + Fore.RESET)

            # 再生成判定
            NG_word = []            
            for word in yml[ident]["prohibit_list"]:
                if word in row['Content']:
                    print(Fore.YELLOW + "\n[MESSAGE]: 短歌本体に[" + word + "]が含まれています。NGリストからは削除します..." + Fore.RESET)
                else:
                    NG_word = NG_word + [f"{word}"]

            # 再生成判定
            regen, regen_count = regen_decision(output,
                                                NG_word, 
                                                regen, yml[ident]["chr_num"], 
                                                regen_count,
                                                yml[ident]["patience_num"])
            
            # 再生成フラグに合わせて再生成+カウンターを1進める
            if (len(regen) > 0):
                regen_count += 1
                print(Fore.YELLOW + "[MESSAGE]: 再生成します...[" + str(regen_count) + " 回目]\n"  + Fore.RESET)

            # シード値と出力結果をデータフレームに格納
            df_result = pd.DataFrame({f'LLM:{ident}': output},
                                     index=[row['No']])

        # 連作を評価するモード
        elif(args.mode == "rensak"):
            output = rensak(theme, model, row)
            
            # 処理時間の出力
            end = datetime.datetime.now()
            result1 = str(end-start_B)[0:7]
            result2 = str(end-start_A)[0:7]
            print(Fore.GREEN + "\n[MESSAGE]: 生成時間:" + result1  + Fore.RESET)
            print(Fore.GREEN + "[MESSAGE]: 合計経過時間" + result2 + " (" + str(count_len) + "/" + str(total_len) + ")" + Fore.RESET)

            output = output.rstrip("\n ")
            if not output.endswith("。"):
                print(Fore.RED + "\n[MESSAGE]: 出力の末尾が中断されている可能性があります。"  + Fore.RESET)
                regen = regen + [1]

            if (len(regen) > 0):
                regen_count += 1
                print(Fore.YELLOW + "[MESSAGE]: 再生成します...[" + str(regen_count) + " 回目]\n"  + Fore.RESET)
            
            df_result = pd.DataFrame({f'{ident}': output},
                                     index=[row['No']])
            
        # 各LLMの出力をLLMに要約させるモード
        elif(args.mode == "utakai"):
            output = utakai(theme, model, yml[ident], row)
            
            # 処理時間の出力
            end = datetime.datetime.now()
            result1 = str(end-start_B)[0:7]
            result2 = str(end-start_A)[0:7]
            print(Fore.GREEN + "\n[MESSAGE]: 生成時間:" + result1  + Fore.RESET)
            print(Fore.GREEN + "[MESSAGE]: 合計経過時間" + result2 + " (" + str(count_len) + "/" + str(total_len) + ")" + Fore.RESET)

            output = output.rstrip("\n ")
            if not output.endswith("。"):
                print(Fore.RED + "\n[MESSAGE]: 出力の末尾が中断されている可能性があります。"  + Fore.RESET)
                regen = regen + [1]
                
            if (len(regen) > 0):
                regen_count += 1
                print(Fore.YELLOW + "[MESSAGE]: 再生成します...[" + str(regen_count) + " 回目]\n"  + Fore.RESET)
            df_result = pd.DataFrame({f'Utakai:{ident}': output},
                                     index=[row['No']])

    # 出力先がある場合、そこに1行のみ追加書き込みする（ヘッダーはなしで）
    if (os.path.exists(df_temp_path)):
        df_result.to_csv(df_temp_path, mode='a', header=False)
    # 新規の場合はヘッダーつきで作成
    else:
        print(Fore.YELLOW + "[MESSAGE]: 一時ファイル...[" + df_temp_path + "]を生成します..."  + Fore.RESET)
        df_result.to_csv(df_temp_path, mode='x')

# すべて終了したらメモリを開放
if (model_type == "trf"):
    import torch
    import gc
    del model
    del tokenizer
    torch.cuda.empty_cache()
elif (model_type == "gguf"):
    del model
    del tokenizer

# 全出力が終了した場合に出力を統合
df_integ = pd.DataFrame()
## 統合先がない場合は新規生成
if not os.path.exists(df_merged):
    print(Fore.YELLOW + "[MESSAGE]: 出力ファイル[" + str(df_merged) + "]を新規に生成します..."  + Fore.RESET)
    df_integ = tanka_preprocess(args.input)
    df_integ.to_csv(df_merged, mode='x')
else:
    df_integ = pd.read_csv(df_merged)

df_temp = pd.read_csv(df_temp_path)

if len(df_integ) == len(df_temp):
    print(Fore.YELLOW + "[MESSAGE]: 出力ファイル[" + str(df_merged) + "]を更新します..."  + Fore.RESET)
    print(Fore.YELLOW + "[MESSAGE]: 一時ファイル...[" + df_temp_path + "]を削除します..."  + Fore.RESET)

    subprocess.run(f'rm {df_temp_path}', shell=True)
    subprocess.run(f'rm {df_merged}', shell=True)
    
    # 余分な列を削除して出力を結合
    df_temp = df_temp.drop(df_temp.columns[[0]], axis=1)
    #print(df_integ)
    #print(df_temp)
    
    df_out = pd.concat([df_integ, df_temp], axis=1)
        
    # read_csv時にindexが付加されている場合は削除
    if ("Unnamed: 0" in df_out):
        del df_out["Unnamed: 0"]

    # 列の順番を並び替え
    LLMs = [s for s in df_out.columns.values if s.startswith('LLM:')]
    LLMs = sorted(LLMs)
    # 歌会モードの場合、markdown形式のファイルを出力
    
    if (f'Utakai:{ident}' in df_out.columns):
        list_col = ['No','Content','Author_comment','Author'] + LLMs
        utakai_markdown(df_out, df_merged, f"Utakai:{ident}")
    else:
        list_col = ['No','Content','Author_comment','Author'] + LLMs
        
    df_out = df_out[list_col]
    print(df_merged)
    print(df_out)
    
    # 出力
    df_out.to_csv(df_merged, mode='x')

else:
    print(Fore.RED + "[ERROR]: 入力一覧と出力結果の行数が一致しません。"  + Fore.RESET)
    exit()
    
# TODO
# モジュール化
# 出力に使用AIやパラメーターなどを記載するヘッダがあってもいい(スタック可能なものの方がのぞましい)
# 出力ファイルの変な列を修正
# web APIでseed指定する方法を確認
# ggufモデルの自動ダウンロードの実行
# requirements.txtの構築、cuda環境の確認
# dockerコンテナ化と動作確認

