import re
import os
import glob
import yaml
import random
import colorama
import time
from colorama import Fore, Back, Style

# model実行用の自作モジュールをインポート
from lib.model_input import *
from lib.submodules.tanka_prompt import *
from lib.submodules.tools import *

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TextStreamer
import google.generativeai as genai

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
def utakai(theme, model, configs, row):

    utakai_sleep = 1800

    model_type = configs["model_type"]

    seed = random.randint(1, 100000000000000)
    
    # LLMコメントがある列を抽出
    LLMs = [s for s in row.keys() if s.startswith('LLM:')]
    #for debug
    print(LLMs)
    if(len(LLMs) < 2):
        print(Fore.RED +"[ERROR]: コメント列が2つ以上ある出力結果を入力してください。" + Fore.RESET)
        exit()
    # 歌会モード用の入力プロンプトを生成
    sys, user, assist = utakai_prompt(theme, row, LLMs)
    
    # 表示
    prompt = {"sys": sys,
              "user": user,
              "assist": assist}
    #for key in prompt:
    #    print(Fore.YELLOW +f"<<{key}>>\n" + prompt[key]+ Fore.RESET)

    # geminiで生成する場合の処理
    if  model_type == "gemini":
        input_prompt = user + "\n" + assist
        output = gemini_generate(sys, input_prompt, model)
        output = output.replace("\n\n", "\n")
        print(output)
        # sleep
        print(Fore.YELLOW +"[MESSAGE]: sleep in " + str(utakai_sleep) + " secs..." + Fore.RESET)
        time.sleep(utakai_sleep)
    # ローカルLLM(GGUF)で生成する場合の処理
    elif model_type == "gguf":
        output = llama_cpp_generate(prompt, model, configs, seed)
    return(output)

# rensak
def rensak(theme, model, row):
    print(Fore.YELLOW +"[MESSAGE]: 連作モードによるコメントの生成を実行します。" + Fore.RESET)
    configs = ""

    #for debug
    #print(LLMs)

    # prompt生成
    sys, user, assist = rensak_prompt(theme, row)
    prompt = {"sys": sys,
              "user": user,
              "assist": assist}

    # promptをgeminiに投入
    output = gemini_generate(prompt, model, configs)
    output = output.replace("\n\n", "\n")

    print(output)
    # sleep
    print(Fore.YELLOW +"[MESSAGE]: sleep in " + str(60) + " secs..." + Fore.RESET)
    time.sleep(60)
    
    return(output)

# geminiによる選
def gemini_select(configs, df, result, num, theme):
    odai = ""
    if not (theme == 0):
        odai = theme + "というお題で"
    genai.configure(api_key=os.environ['GOOGLE_API_KEY'])

    system = "あなたは短歌の表現や内容を詳細に評価することのできる役立つアシスタントです。"
    test_prompt = f"""以下は、短歌投稿企画に{odai}投稿された短歌の一覧です。

```txt
{result}
```

これら{len(df)}首の投稿作品を読み込み、あなたが優れていると思った短歌をこの中から最大{num}首選び、各短歌に1から{num}までの番号を振って、それぞれについて詳しくコメントしてください。
なお、コメント中には短歌の一覧に記載されている通し番号を記載せず、最後に選出番号を用いて投稿歌全体の総評をコメントしてください。
"""

    model = genai.GenerativeModel(model_name=configs["model_path"],
                                  system_instruction=system)
    response = model.generate_content(test_prompt,
                                      generation_config=genai.types.GenerationConfig(temperature=configs["temperature"]))
    return(response.text)

# geminiによる選
def nemo_select(configs, model, tokenizer, df, result, num, theme):
    odai = ""
    output = "output error"
    if not (theme == 0):
        odai = theme + "というお題で"

    # Format message with the chat template
    messages = [{"role": "system", "content": """あなたは短歌の表現や内容を評価することのできる役立つアシスタントです。"""},
                {"role": "user", "content":  f"""以下は、短歌投稿企画に{odai}投稿された短歌の一覧です。

        ```
        {result}
        ```

        これら{len(df)}首の投稿作品を読み込み、あなたが優れていると思った短歌をこの中から{num}首選び、各短歌に1から{num}までの番号を振って、以下のmarkdown形式で出力してください。選出番号と短歌、コメントを含めるとともに、一覧の通し番号は含めないようにしてください。

        1. **<選んだ短歌>**  \n
           <コメント内容>

        最後に、{num}首の投稿歌全体についての総評を、選出番号を参照してコメントしてください。
        """},
                {"role": "assist", "content": f"""わかりました。私が優れたと感じた短歌{num}首を選び、それぞれについてのコメントと投稿歌全体の総評を出力します。"""},]

    # transformers
    if (configs["model_type"] == "trf"):
        input_ids = tokenizer.apply_chat_template(messages, 
                                                  tokenize=True, 
                                                  add_generation_prompt=True, 
                                                  return_tensors="pt")
        input_ids = input_ids.to("cuda:0")


        streamer = TextStreamer(tokenizer, 
                                skip_prompt=True, 
                                skip_special_tokens=True)

        gen_tokens = model.generate(input_ids, 
                                    temperature=configs["temperature"],
                                    top_p=configs["Top_P"],
                                    max_new_tokens=configs["Max_Tokens"],
                                    do_sample=True, 
                                    streamer=streamer,)
        output = tokenizer.decode(gen_tokens[0][input_ids.shape[1]:], skip_special_tokens=True).strip()

    # gguf(llama-cpp-python)
    elif (configs["model_type"] == "gguf"):
        import llama_cpp
        output = model.create_chat_completion(messages=messages,
                                              temperature=configs["temperature"],
                                              seed = -1,
                                              top_p=configs["top_P"],
                                              max_tokens = configs["max_Tokens"],
                                              stream = True,
                                              )
        result = ""
        for chunk in output:
            delta = chunk['choices'][0]['delta']
            if 'role' in delta:
                print(delta['role'], end=': ', flush=True) 
            elif 'content' in delta:
                result = result + delta['content']
                tokens = delta['content'].split()
                for token in tokens:
                    print(token, end="", flush=True)
        output = result
    
    return(output)

