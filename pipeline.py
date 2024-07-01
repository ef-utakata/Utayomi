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

ver = """Utayomi Version: 0.2.0
設計: ef_utakata
"""

parser = argparse.ArgumentParser(description="""Utayomi: 入力された短歌についてLLMにより評を生成するシステムです。設計: ef_utakata """)

# 必須引数
parser.add_argument('input', help='入力短歌一覧のパス(csv形式で入力), 再生成モードの場合は前回の出力一覧')
parser.add_argument('output', help='出力先ディレクトリのパス(csv形式で出力)')
parser.add_argument('-c','--config', default='./model_conf.yaml', help='利用モデルの入力設定ファイル(yaml形式)')
parser.add_argument('-i','--identifier', help='入力設定ファイル内の設定識別子(--listで一覧を確認可能)')

# 実行モードの指定
parser.add_argument('-m','--mode', help='実行モード{first(初回生成) / utakai(要約)} default: first', default='first') #regen
# お題の指定
parser.add_argument('-t', '--theme',  help='お題(入力がない場合自由詠)', default=0)

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
            regen, regen_count = regen_decision(output,
                                                yml[ident]["prohibit_list"], 
                                                regen, yml[ident]["chr_num"], 
                                                regen_count)
            
            # 再生成フラグに合わせて再生成+カウンターを1進める
            if (len(regen) > 0):
                regen_count += 1
                print(Fore.YELLOW + "[MESSAGE]: 再生成します...[" + str(regen_count) + " 回目]\n"  + Fore.RESET)

            # シード値と出力結果をデータフレームに格納
            df_result = pd.DataFrame({f'LLM:{ident}': output},
                                     index=[row['No']])
            
        # 各LLMの出力をGeminiに要約させるモード
        elif(args.mode == "utakai"):
            output = utakai(theme, model, row)
            
            # 処理時間の出力
            end = datetime.datetime.now()
            result1 = str(end-start_B)[0:7]
            result2 = str(end-start_A)[0:7]
            print(Fore.GREEN + "\n[MESSAGE]: 生成時間:" + result1  + Fore.RESET)
            print(Fore.GREEN + "[MESSAGE]: 合計経過時間" + result2 + " (" + str(count_len) + "/" + str(total_len) + ")" + Fore.RESET)
            
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
    subprocess.run(f'rm {df_merged}', shell=True)
    subprocess.run(f'rm {df_temp_path}', shell=True)

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
    if ('Utakai:Gemini' in df_out.columns):
        list_col = ['No','Content','Author_comment','Author','Utakai:Gemini'] + LLMs
    else:
        list_col = ['No','Content','Author_comment','Author'] + LLMs
        
    df_out = df_out[list_col]
    
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


