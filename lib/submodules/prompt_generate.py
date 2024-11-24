import subprocess
import yaml
import glob
import os
import torch
import time
from lib.submodules.tools import *

# gemini
def gemini_generate(sys, prompt, model):
    seed = 0
    import google.generativeai as genai
    from google.generativeai.types import HarmCategory, HarmBlockThreshold
    
    gen_count = 0
    roop_flag = 0
    output = 0
    model_list = model
    text = prompt

    while roop_flag == 0:
        if not gen_count in model_list:
            print(Fore.RED +"[MESSAGE]: プロンプトはgeminiのどのモデルにも拒否されました。" + Fore.RESET)
            output = "ERROR"
            break
        else:
            genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
            model_name = model_list[gen_count]
            model = genai.GenerativeModel(model_name,
                                          system_instruction=sys)
            print(Fore.YELLOW +"[MESSAGE]: プロンプトを [" + model_name + "] に入力しています..." + Fore.RESET)
            print(Fore.YELLOW +f"<<sys>>:\n{sys}\n<<prompt>>{prompt}" + Fore.RESET)
            
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
                                             return_tensors="pt",
                                             return_attention_mask=True)
    streamer = TextStreamer(tokenizer, 
                            skip_prompt=True, 
                            skip_special_tokens=True)

    model_inputs = encodeds.to("cuda:0")
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
    
#Llm-jp-3-13B
def llm_jp_generate(prompt, tokenizer, model, configs, seed):
    import transformers
    from transformers import TextStreamer
    
    torch.manual_seed(seed)
    
    messages = [{"role": "system", "content": prompt["sys"]},
                {"role": "user", "content": prompt["user"]},
                {"role": "assist", "content":  prompt["assist"]}
               ]

    encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt",
                                             padding=True,
                                             add_generation_prompt=True,
                                             return_attention_mask=True)

    streamer = TextStreamer(tokenizer, 
                            skip_prompt=True, 
                            skip_special_tokens=True)
    #attention_mask=encodeds['attention_mask']
    
    model_inputs = encodeds.to("cuda:0")
    #attention_mask=attention_mask.to("cuda:0")
    
    generated_ids = model.generate(model_inputs, 
                                   #attention_mask=attention_mask,
                                   max_new_tokens=configs["Max_Tokens"], 
                                   do_sample=True, 
                                   temperature=configs["temperature"],
                                   streamer=streamer,)
    output = tokenizer.decode(generated_ids[0][encodeds.shape[1]:], skip_special_tokens=True).strip()
    return(output)
# Llama-3.1-Swallow-8B
def Llama_Swallow_generate(prompt, tokenizer, model, configs, seed):
    import transformers
    from transformers import TextStreamer
    
    torch.manual_seed(seed)
    
    messages = [{"role": "system", "content": "以下は、タスクを説明する指示です。要求を適切に満たす応答を書きなさい。"},
                {"role": "user", "content": prompt["user"]},
                {"role": "assist", "content":  prompt["assist"]}
               ]

    encodeds = tokenizer.apply_chat_template(messages, return_tensors="pt",
                                             padding=True,
                                             add_generation_prompt=True,
                                             return_attention_mask=True)

    streamer = TextStreamer(tokenizer, 
                            skip_prompt=True, 
                            skip_special_tokens=True)
    #attention_mask=encodeds['attention_mask']
    
    model_inputs = encodeds.to("cuda:0")
    #attention_mask=attention_mask.to("cuda:0")
    
    generated_ids = model.generate(model_inputs, 
                                   #attention_mask=attention_mask,
                                   max_new_tokens=configs["Max_Tokens"], 
                                   do_sample=True, 
                                   temperature=configs["temperature"],
                                   streamer=streamer,)
    output = tokenizer.decode(generated_ids[0][encodeds.shape[1]:], skip_special_tokens=True).strip()
    return(output)

    
# llama-cpp-python test
def llama_cpp_generate(prompt: dict, model, configs: dict, seed_num: int):
    import llama_cpp
    
    message_list = []

    # gemma由来モデルはsystemロールがないので除去
    if "gemma" in configs["model_path"]:
        message_list = [{"role": "user", "content": prompt["user"]},
                        {"role": "assist", "content": prompt["assist"]},
                       ]
    # それ以外のモデルはsystemロールを付与
    else:
        message_list = [{"role": "system", "content": prompt["sys"]},
                        {"role": "user", "content": prompt["user"]},
                        {"role": "assist", "content": prompt["assist"]},
                       ]
        
    
    output = model.create_chat_completion(messages=message_list,
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