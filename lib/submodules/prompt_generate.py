import os
import torch
import time
from lib.submodules.tools import *

# gemini
def gemini_generate(prompt, model, configs):
    seed = 0
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    
    gen_count = 0
    roop_flag = 0
    output = 0
    model_list = model
    text = """{}

{}
{}""".format(prompt["sys"],
             prompt["user"],
             prompt["assist"])
    
    while roop_flag == 0:
        if not gen_count in model_list:
            print(Fore.RED +"[MESSAGE]: プロンプトはgeminiのどのモデルにも拒否されました。" + Fore.RESET)
            output = "ERROR"
            break
        else:
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            model_name = model_list[gen_count]
            model = genai.GenerativeModel(model_name)
            print(Fore.YELLOW +"[MESSAGE]: プロンプトを [" + model_name + "] に入力しています..." + Fore.RESET)
            response = model.generate_content(text, 
                                              safety_settings={HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                                                               HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                                                               #HarmCategory.HARM_CATEGORY_DEROGATORY: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                                                               #HarmCategory.HARM_CATEGORY_TOXICITY: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                                                               #HarmCategory.HARM_CATEGORY_VIOLENCE: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                                                               #HarmCategory.HARM_CATEGORY_SEXUAL: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                                                               #HarmCategory.HARM_CATEGORY_DANGEROUS: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                                                               HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE
                                                               }
                                             )
            response.resolve()
            roop_flag = len(response.parts)
        
        if roop_flag > 0: # 生成成功
            output = response.text
        else:
            print(Fore.RED +"[MESSAGE]: プロンプトは [" + model_name + "] に拒否されました。" + Fore.RESET)
            gen_count += 1

    return(output)

# cohere
def cohere_generate(prompt, tokenizer, model, configs):
    import cohere
    text = """{}

{}
{}""".format(prompt["sys"],
             prompt["user"],
             prompt["assist"])
    #key = API_keys[model_type]
    # cohere APIに入力
    co = cohere.Client(os.environ["COHERE_API_KEY"])
                           
    response  = co.chat(seed  = seed_num,
                        temperature = configs["temperature"] ,
                        model = configs["model_path"],
                        chat_history=[],
                        # model="command-r-plus",
                        message=text,
                        # perform web search before answering the question. You can also use your own custom connector.
                        connectors=[{"id": "web-search"}])

    output = response.text
    return(output)
    
# openAI
def openai_generate(prompt, model, configs):
    seed = 0
    import openai
    from openai import OpenAI
    text = """{}

{}
{}""".format(prompt["sys"],
             prompt["user"],
             prompt["assist"])
    
    client = OpenAI()
    #openai.api_key = key
    openai.api_key = os.environ["OPENAI_API_KEY"]
    completion = client.chat.completions.create(model=model,
                                                messages=text,
                                                temperature = configs["temperature"]
                                               )
    output = completion.choices[0].message.content
    return(output)

# Umievo-itr012-Gleipnir-7B
def umievo_generate(prompt, tokenizer, model, configs, seed):
    import transformers
    from transformers import TextStreamer

    text = """[INST] <<SYS>>
{}
<</SYS>>

{}[/INST]
{}""".format(prompt["sys"],
             prompt["user"],
             prompt["assist"])
    input_ids = tokenizer.encode(text, 
                                 add_special_tokens=True, 
                                 return_tensors="pt")
    torch.manual_seed(seed)
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    #print(text) # for debug
    tokens = model.generate(input_ids.to(device=model.device),
                            max_new_tokens=configs["Max_Tokens"],
                            temperature=configs["temperature"],
                            top_p=configs["Top_P"],
                            do_sample=True,
                            pad_token_id=tokenizer.eos_token_id, #error対策
                            bad_words_ids=get_tokens_as_list(configs["prohibit_list"],tokenizer), #NG word
                            min_new_tokens=configs["min_new_tokens"], # test
                            streamer=streamer,
                           )

    
    output = tokenizer.decode(tokens[0][input_ids.shape[1]:], skip_special_tokens=True).strip()
    return(output)

#oumuamua
def oumuamua_generate(prompt, tokenizer, model, configs, seed):
    
    import transformers
    from transformers import TextStreamer
    
    messages = [{"role": "system", "content": prompt["sys"]},
                {"role": "user", "content": prompt["user"]},
                {"role": "assist", "content":  prompt["assist"]}
               ]

    encodeds = tokenizer.apply_chat_template(messages, 
                                             return_tensors="pt")
    streamer = TextStreamer(tokenizer, 
                            skip_prompt=True, 
                            skip_special_tokens=True)

    model_inputs = encodeds.to("cuda")
    torch.manual_seed(seed)
    
    generated_ids = model.generate(model_inputs, 
                                   max_new_tokens=configs["Max_Tokens"], 
                                   do_sample=True, 
                                   temperature=configs["temperature"],
                                   pad_token_id=tokenizer.eos_token_id,
                                   streamer=streamer,
                                   bad_words_ids=get_tokens_as_list(configs["prohibit_list"],tokenizer),)
    
    output = tokenizer.decode(generated_ids[0][encodeds.shape[1]:], skip_special_tokens=True).strip()
    return(output)
    
#phi-3-mini
def phi_mini_generate(prompt, tokenizer, model, configs, seed):
    
    torch.manual_seed(seed)
    
    messages = [{"role": "system", "content": prompt["sys"]},
                {"role": "user", "content": prompt["user"]},
                {"role": "assist", "content":  prompt["assist"]}
               ]

    encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt")
    streamer = TextStreamer(tokenizer, 
                            skip_prompt=True, 
                            skip_special_tokens=True)

    model_inputs = encodeds.to("cuda")
    generated_ids = model.generate(model_inputs, 
                                   max_new_tokens=configs["Max_Tokens"], 
                                   do_sample=True, 
                                   temperature=configs["temperature"],
                                   streamer=streamer,)
    output = tokenizer.decode(generated_ids[0][encodeds.shape[1]:], skip_special_tokens=True).strip()
    return(output)

#Ninja-V1-RP
def ninja_generate(prompt, tokenizer, model, configs, seed):
    import transformers
    import re
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, TextStreamer

    # Vicuna 1.1
    messages = """{Sys}
USER: {User}

ASSISTANT: {Assist}""".format(Sys = prompt["sys"],
                              User = prompt["user"],
                              Assist = prompt["assist"])
    encodeds = tokenizer(messages, return_tensors="pt")
    
    streamer = TextStreamer(tokenizer, skip_prompt=True, skip_special_tokens=True)
    torch.manual_seed(seed)
    
    model_inputs = encodeds.to("cuda")
    generated_ids = model.generate(**model_inputs, 
                                   max_new_tokens=configs["Max_Tokens"],
                                   top_p=configs["Top_P"],
                                   temperature=configs["temperature"],
                                   bad_words_ids=get_tokens_as_list(configs["prohibit_list"], tokenizer),
                                   do_sample=True,
                                   pad_token_id=tokenizer.eos_token_id,
                                   repetition_penalty=configs["repetition_penalty"],
                                   streamer=streamer,)

    # prompt部分を除去
    output = tokenizer.decode(generated_ids[0], skip_special_tokens=True)
    result = re.sub(r'(.*\n)+.*\n+.*文章を出力します。', '', output, re.DOTALL|re.MULTILINE)
    return(result)

# llama-cpp-python test
def llama_cpp_generate(prompt, model, configs, seed_num):
    import llama_cpp
    output = model.create_chat_completion(messages=[{"role": "system", "content": prompt["sys"]},
                                                    {"role": "user", "content": prompt["user"]},
                                                    {"role": "assist", "content": prompt["assist"]},
                                                   ],
                                          temperature=configs["temperature"],
                                          seed = seed_num,
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
    return(result)