import os
import subprocess
import re
import colorama
from colorama import Fore, Back, Style

# llama-cpp-pythonで生成する場合のモジュール
def gguf_load(config):
    from llama_cpp import Llama
    if os.path.isfile(config["model_path"]):
        model_path = config["model_path"]
    else:
        print(Fore.YELLOW +"[MESSAGE] モデル: " + config["model_url"]+  " をダウンロードしています......"  + Fore.RESET)
        url = config["model_url"]
        command = "wget " + url + " -P" + " ./models"
        
        subprocess.call(command, shell=True)
        
    print(Fore.GREEN +"[MESSAGE] model: " + config["model_url"] +  " をロードしています......"  + Fore.RESET)
    llm = Llama(model_path = config["model_path"],
                n_ctx = 1024,
                #seed = seed_num,
                embedding = False,
                verbose = True, # decugのためTrue
                n_gpu_layers = -1,
                n_batch = 2048,
                flash_attn = True,
                )
    tokenizer = 0
    return(llm, tokenizer)

# huggingface形式のモデルをロード
def trf_load(config):
    model_path = config["model_path"]
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM, LogitsProcessorList
    model_path = config["model_path"]
    
    print(Fore.GREEN +"[MESSAGE] model: " + model_path +  " をロードしています......"  + Fore.RESET)

    tokenizer = AutoTokenizer.from_pretrained(model_path,
                                              torch_dtype="auto",
                                              device_map="auto",)
    
    model = AutoModelForCausalLM.from_pretrained(model_path,
                                                 torch_dtype="auto",
                                                 device_map="auto",
                                                 low_cpu_mem_usage=True, #GLMで追加
                                                 trust_remote_code=True, #GLMで追加
                                                 attn_implementation="eager", #Phi-3-miniで追加
                                                )
    
    #logits_processor = model._get_logits_processor(
    #    repetition_penalty=None,
    #    no_repeat_ngram_size=None,
    #    bad_words_ids=None,
    #    min_length=None,
    #    eos_token_id=tokenizer.eos_token_id,
    #    logits_processor=LogitsProcessorList(),
    #    renormalize_logits=None,
    #)
    
    model.eval()

    #if torch.cuda.is_available():
    #    model = model.to("cuda")

    return(model, tokenizer)


