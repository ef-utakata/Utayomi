# cohere, gemini, ggufのプロンプトフォーマットを作成
def arrange_prompt(model_ident, configs, sys, user, assist):
    prompt = 0
    model_type = configs["model_type"]
    
    # cohere    
    if model_type == "Cohere":
        sys = "<BOS_TOKEN>\n" + "<|START_OF_TURN_TOKEN|><|SYSTEM_TOKEN|>\n" + sys + "<|END_OF_TURN_TOKEN|>\n"
        user = "<|START_OF_TURN_TOKEN|><|USER_TOKEN|>" + user + "<|END_OF_TURN_TOKEN|>\n"
        assist = "<|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>" + assist # 出力結果によってはassistは除去
        prompt = sys + user + assist
        
    # openai
    elif model_type == "openai":
        prompt = [{"role": "system", "content": sys},
                  {"role": "user", "content": user},
                  {"role": "assistant", "content": assist}] # 出力結果によってはassistは除去

    # gemini
    elif model_type == "gemini":
        prompt = """{Sys}

{User}

{Assist}""".format(Sys=sys,
             User=user,
             Assist=assist)
        

    # gguf
    elif model_type == "gguf":

        # Qwen2-57B
        if (model_ident == "Qwen2-57B"):
            sys = "<|im_start|>system\n" + sys + "<|im_end|>\n"
            user = "<|im_start|>user\n" + user + "<|im_end|>\n"
            assist = "<|im_start|>assistant\n" + assist # 出力結果によってはassistは除去
            prompt = sys + user + assist

        # phi-3
        elif model_ident == "Phi-3-medium":
            prompt = f"""
{system_message}\n

### Instruction:\n
 {input}\n

### Response:\n
{assist}
""" # assistは生成結果次第で除去
            
        # phi-3
        elif model_ident == "Phi-3-medium":
            sys = "" # Phi-3にsystem promptはない
            user = "<s><|user|>\n" + user + "<|end|>\n"
            assist = "<|assistant|>" + assist # 出力結果によってはassistは除去
            prompt = sys + user + assist

        # Karakuri
        elif (model_ident == "Karakuri"):
            prompt = f"""<s>[INST] <<SYS>>{system_message}<</SYS>>\n

{input}\n
[ATTR] helpfulness: {configs["attr"]["helpfulness"]} correctness: {configs["attr"]["correctness"]} coherence: {configs["attr"]["coherence"]} complexity: {configs["attr"]["complexity"]} verbosity: {configs["attr"]["verbosity"]} quality: {configs["attr"]["quality"]} toxicity: {configs["attr"]["toxicity"]} humor: {configs["attr"]["humor"]} creativity: {configs["attr"]["creativity"]} [/ATTR][/INST]\n
{assist}
""" # assistは生成結果次第で除去
    
    return(prompt)