import pandas as pd
import os
import re
import colorama
from colorama import Fore, Back, Style

# 完全新規の場合に、作品一覧のモデル入力を前処理
def tanka_preprocess(input_csv):

    df = pd.DataFrame()
    df_raw = pd.read_csv(input_csv)

    #解析に用いる列のみを抽出(Human assistの列がある場合は取り込み、ない場合はゼロ埋め)
    if ("Human_comment" in df_raw.columns):
        df = df_raw[['Content','Author_comment','No','Author','Human_comment']]
        df["Human_comment"] =df["Human_comment"].astype(str)
        df = df.fillna("NaN")
    #連作モードの場合の処理
    elif("count" in df_raw.columns):
        df = df_raw[['No','Title','Content','count','Author']]
        df = df.fillna("NaN")
    #単作、Human assistナシの場合の処理
    else:
        df = df_raw[['Content','Author_comment','No','Author']]
        df = df.fillna("NaN")

    # 空の行を除去
    df = df.query('Content != "NaN"')

    df["Content"] = df["Content"].astype(str)
    if("Author_comment" in df_raw.columns):
        df["Author_comment"] =df["Author_comment"].astype(str)
        df["Author_comment"] = df["Author_comment"].str.replace("\r", "")
        df["Author_comment"] = df["Author_comment"].str.replace("\n", "")
    if not ("count" in df_raw.columns):
        df["Content"] = df["Content"].str.replace("\r", "")
        df["Content"] = df["Content"].str.replace("\n", "")
    
    #各列のデータ型の割り当て
    if ("Human_comment" in df_raw.columns):
        df = df.astype({'No': 'int',
                        'Human_comment' : 'str'})
    else:
        df = df.astype({'No': 'int'})
    return(df)

# 完全新規の場合は出力結果と一時出力を生成、出力がある場合はmodel_identの行を含む一時出力を読み込み、その場所から再開
def output_preprocess(input_csv, output_dir, mode, model_ident):
    
    df = pd.DataFrame()
    output_temp = "error"
    output_csv  = "error"
    
    basename_without_ext = os.path.splitext(os.path.basename(input_csv))[0]
    # for debug
    #print("basename_without_ext: " + basename_without_ext)
    
    if basename_without_ext.endswith('_result'):
        output_csv  = output_dir + basename_without_ext + ".csv"
        output_temp = output_dir + basename_without_ext + ".temp.csv"
    else:
        output_csv  = output_dir + basename_without_ext  + "_result.csv"
        output_temp = output_dir + basename_without_ext + model_ident + ".temp.csv"
    # for debug
    #print("output_csv: " + output_csv)
    # 末尾にスラッシュがない場合付与
    if not output_dir.endswith('/'):
        output_dir = output_dir + "/"

    # 入力ファイルと出力先のディレクトリが存在しない場合は終了
    if not os.path.exists(input_csv):
        print(Fore.RED + "[ERROR]: " + "入力ファイル [" + input_csv + "] は存在しません。" + Fore.RESET)
        exit()
    if not os.path.exists(output_dir):
        print(Fore.RED + "[ERROR]: " + "出力ディレクトリ [" + output_dir + "] は存在しません。" + Fore.RESET)
        exit()
    if os.path.isfile(output_dir):
        print(Fore.RED + "[ERROR]: " + "[" + output_dir + "] はファイルです。既存のディレクトリを指定してください。" + Fore.RESET)
        exit()
    if os.path.isdir(input_csv):
        print(Fore.RED + "[ERROR]: " + "[" + input_csv + "] はディレクトリです。既存のファイルを指定してください。" + Fore.RESET)
        exit()

    # 入力と出力先がある場合、統合済みの出力の有無を確認
    else:
        # 通常生成モードの場合
        if (mode == "first"):
            # 新規に出力する場合、出力対象の一覧を前処理してすべての列を返す
            if not os.path.exists(output_csv):
                df = tanka_preprocess(input_csv)
                # for debug
                #print(df)
            
            # 出力済みの一覧がある場合、生成途中のリストを読み込んで途中のものを返す
            else:
                # 生成途中のリストがない場合、出力済み一覧をそのまま解析対象として返す
                if not os.path.exists(output_temp):
                    print(Fore.YELLOW + "[MESSAGE]: [" + model_ident + "]による生成を開始します。" + Fore.RESET)
                    df = pd.read_csv(output_csv, index_col=0)
            
                # 生成途中のリストがある場合、生成済みの行は飛ばして入力
                else:
                    df = pd.read_csv(output_csv, index_col=0)
                    length = len(pd.read_csv(output_temp))
                    print(Fore.YELLOW + "[MESSAGE]: " + " No." + str(length) + "から[" + model_ident + "]による生成を再開します。" + Fore.RESET)
                    query = "No > " + str(length)
                    df = df.query(query)
                    
        # 歌会モードの場合
        elif (mode == "utakai"):
            if not os.path.exists(output_temp):
                print(Fore.YELLOW + "[MESSAGE]: [" + model_ident + "]によるコメントの要約を開始します。" + Fore.RESET)
                df = pd.read_csv(output_csv, index_col=0)
                #print(df)
            else:
                length = len(pd.read_csv(output_temp))
                print(Fore.YELLOW + "[MESSAGE]: " + " No." + str(length) + "から[" + model_ident + "]によるコメントの要約を再開します。" + Fore.RESET)
                df = pd.read_csv(output_csv, index_col=0)
                query = "No > " + str(length)
                df = df.query(query)
                
        # 連作モードの場合
        if (mode == "rensak"):
            print(Fore.YELLOW + "[MESSAGE]: [" + model_ident + "]による連作モードを開始します。" + Fore.RESET)
            # 新規に出力する場合、出力対象の一覧を前処理してすべての列を返す
            if not os.path.exists(output_csv):
                df = tanka_preprocess(input_csv)
                # for debug
                #print(df)
            
            # 出力済みの一覧がある場合、生成途中のリストを読み込んで途中のものを返す
            else:
                # 生成途中のリストがない場合、出力済み一覧をそのまま解析対象として返す
                if not os.path.exists(output_temp):
                    print(Fore.YELLOW + "[MESSAGE]: [" + model_ident + "]による生成を開始します。" + Fore.RESET)
                    df = pd.read_csv(output_csv, index_col=0)
            
                # 生成途中のリストがある場合、生成済みの行は飛ばして入力
                else:
                    df = pd.read_csv(output_csv, index_col=0)
                    length = len(pd.read_csv(output_temp))
                    print(Fore.YELLOW + "[MESSAGE]: " + " No." + str(length) + "から[" + model_ident + "]による生成を再開します。" + Fore.RESET)
                    query = "No > " + str(length)
                    df = df.query(query)
    # for debug
    #print(df)
    
    #各列のデータ型の割り当て
    if ("Human_comment" in df.columns):
        df = df.astype({'No': 'int',
                        'Human_comment' : 'str',
                        'Author_comment' :'str'})
    else:
        # for debug
        #print(df.columns)
        if ('Author_comment' in df.columns):
            df = df.astype({'No': 'int',
                            'Author_comment' :'str'})
    # コメント出力対象と一時出力のパスと統合を返す
    return(df, output_temp, output_csv)

# LLMに評の再生成を命じる条件をここで指定
def regen_decision(output, prohibit_list, regen, chr_num, regen_count, patience_num):
    # 禁止ワードリストを受け取ってある場合は再生成フラグを追加
    for word in prohibit_list:
        if word in output:
            print(Fore.RED + "[MESSAGE]: 再生成ワード [" + word + "] " + "が含まれています。\n"  + Fore.RESET)
            regen = regen + [1]
            
    # 再生成が5回を超えている場合はフラグを0にしてwhileループから抜ける
    if (regen_count > patience_num):
        print(Fore.YELLOW + "\n[MESSAGE]: " + str(regen_count) + "回再生成しています。不適切な再生成ワードが指定されている可能性があります。"  + Fore.RESET)
        regen = []

    if len(output) < chr_num:
        print(Fore.YELLOW + "\n[MESSAGE]: 出力が指定文字数 [" + str(chr_num) + "] 文字より少ないです。"  + Fore.RESET)
        regen = regen + [1]
                
    # time outの場合再生成カウントを上げる
    if re.search(r'評の生成時間がタイムアウトしました', output):
        regen = regen + [1]

    # 安全設定で拒否された場合(gemini)の場合はループから抜ける
    if (output == "ERROR"):
        regen = []
        
    return(regen, regen_count)

# transformerで生成時にNGワードリストを入力するためのモジュール
def get_tokens_as_list(word_list, tokenizer):
    "Converts a sequence of words into a list of tokens"
    tokens_list = []
    for word in word_list:
        tokenized_word = tokenizer([word], add_special_tokens=False).input_ids[0]
        tokens_list.append(tokenized_word)
    return tokens_list

# 歌会モードの結果を作者順でソートし、markdown形式のファイルで出力
def utakai_markdown(df, out_csv):
    
    basename_without_ext = os.path.splitext(os.path.basename(out_csv))[0]
    
    
    df = df.sort_values('Author')

    with open(out_csv, mode='w') as f:
        for index, row in df.iterrows():
            f.write("\n## 投稿歌\n")
            f.write("**" + row['Content'] + "**\n")
            f.write("## 作者\n")
            f.write(str(row['Author']))
            f.write("\n")
            sub = row['Utakai:Gemini'].replace("\n**", "\n### **")
            test = sub
            
            # Geminiが拒否した場合はLLMのコメントをそのまま掲載
            if row['Utakai:Gemini'] == "ERROR":
                sub = "* Geminiの入力エラーで要約が実行できなかったため、各LLMからのコメントをそのまま掲載します。  \n"
                f.write(sub)
                LLMs = [s for s in df.columns.values if s.startswith('LLM:')]
                for LLM in LLMs:
                    f.write("### " + row[f"{LLM}"])
                    comment = row[f"{LLM}"]
                    f.write(f"{comment}\n")
            else:
                f.write(sub)
            f.write("<div style=\"page-break-before:always\"></div>\n")