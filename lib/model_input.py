import os
import time
import re
import colorama
from colorama import Fore, Back, Style

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline, set_seed

from lib.submodules.tools import *
from lib.arrange_prompt import *
from lib.submodules.prompt_generate import *

def model_input(model_ident,
                configs,
                model, 
                tokenizer, 
                prompt, 
                seed_num):

    # config読み込み、その他初期値を指定
    model_type = configs["model_type"]
    output = 0
    seed = seed_num
    device = "cuda"
    
    sys = prompt["sys"]
    user = prompt["user"]
    assist = prompt["assist"]

    # 対応モデルごとに定義したモジュール(prompt_generate.py中に記述)を用いてコメントを生成
    # cohere
    if (model_type == "cohere"):
        output = cohere_generate(prompt, configs)   
    # GPT
    elif (model_type == "openai"):
        output = openai_generate(prompt, model, configs)
    # gemini
    elif (model_type == "gemini"):
        output = gemini_generate(prompt, model, configs)

    # llama-cpp-python
    elif (model_type == "gguf"):
        output = llama_cpp_generate(prompt, model, configs, seed_num)
        
    # llama-cpp
    elif (model_type == "llamacli"):
        output = llamacli_generate(prompt, model, configs, seed_num)

    # huggingfaceで入出力を行うモデル
    elif (model_type == "trf"):
        # Umievo-itr012-Gleipnir-7B
        if (model_ident == "Umievo"):
            output = umievo_generate(prompt, tokenizer, model, configs, seed_num)
        # Oumuamua
        elif (model_ident == "Oumuamua"):
            output = oumuamua_generate(prompt, tokenizer, model, configs, seed_num)
        # Phi-3-mini
        elif(model_ident == "Phi-3-mini"):
            output = phi_mini_generate(prompt, tokenizer, model, configs, seed_num)
        # Ninja-V2-7B
        elif(model_ident == "Ninja-v2-7b"):
            output = ninja_generate(prompt, tokenizer, model, configs, seed)
        # Shadows-MoE
        elif(model_ident == "Shadows-moe"):
            output = ninja_generate(prompt, tokenizer, model, configs, seed)
    
    # エラーメッセージの表示
    if (output == 0):
        print (Fore.RED +"[ERROR]: モデルへのプロンプトの入出力に失敗しました。"+ Fore.RESET)
        exit()
    return(seed, output)
