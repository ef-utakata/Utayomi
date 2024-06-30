import re
import glob
import yaml
import random
import colorama
import time
from colorama import Fore, Back, Style

# model実行用の自作モジュールをインポート
from lib.model_input import *
from lib.submodules.tanka_prompt import *

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

# 入力されたお題、短歌、著者、著者コメントについて指定されたモデルに対応したプロンプト生成し、指定された形式のを入力、短歌の評を生成して返す
def tanka_critic(model_ident,
                 configs,
                 Theme,
                 Tanka,
                 Author,
                 Author_comment,
                 Human_comment,
                 model,
                 tokenizer,
                 No,
                 seed_number):
    
    #各文字列を合成して動的にプロンプト生成
    sys, user, assist = tanka_prompt(configs,
                                     Theme,
                                     Tanka,
                                     Author,
                                     Author_comment,
                                     Human_comment)
    # promptを辞書形式で格納
    prompt = {"sys": sys,
              "user": user,
              "assist": assist}
    # 表示
    for key in prompt:
        print(Fore.YELLOW +"<<" + key + ">>\n" + prompt[key]+ Fore.RESET)

    seed = 0
    #シード値をランダムに決定
    if (seed_number == 0):
        seed = random.randint(1, 100000000000000)
    else:
        seed = seed_number
        
    #モデルに合わせて成型したプロンプトをモデルに入力して推論を実行
    output = 0
    seed, output = model_input(model_ident,
                               configs, 
                               model,     # model_pathまたはload model
                               tokenizer, # 0 またはload takenizer
                               prompt, 
                               seed)

    # sleep
    if "sleep" in configs:
        print(Fore.YELLOW +"[MESSAGE]: sleep in " + str(configs["sleep"]) + " secs..." + Fore.RESET)
        time.sleep(configs["sleep"])
    #出力結果と使用したシード値を返す
    return(seed, output)

# utakai
def utakai(theme, model, row):
    configs = ""
    # LLMコメントがある列を抽出
    LLMs = [s for s in row.keys() if s.startswith('LLM:')]
    #for debug
    #print(LLMs)
    if(len(LLMs) < 2):
        print(Fore.RED +"[ERROR]: コメント列が2つ以上ある出力結果を入力してください。" + Fore.RESET)
        exit()
        
    sys, user, assist = utakai_prompt(theme, row, LLMs)
    prompt = {"sys": sys,
              "user": user,
              "assist": assist}

    output = gemini_generate(prompt, model, configs)
    output = output.replace("\n\n", "\n")

    print(output)
    # sleep
    print(Fore.YELLOW +"[MESSAGE]: sleep in " + str(60) + " secs..." + Fore.RESET)
    time.sleep(60)
    
    return(output)

