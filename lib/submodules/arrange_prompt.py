def arrange_prompt():



#################################################################
    # Human-assisted AI commentに対応
    human_assist  = ""
    human_comment = ""

    if(Human_comment == 0):
      human_assist = "について、"
    else:
      human_assist = "と、人間によって指摘された観点に基づいて、"
      human_comment = """
また、あなたがこの短歌について誤解したり見落としたりしている観点について、以下が人間によって指摘されています。

「{human}」
""".format(human = Human_comment)

    stance =  ""
    #評者のスタンスをセットしない場合
    if(critic_stance == 0):
      stance ="""[INST] <<SYS>>あなたは短歌の表現や内容を評価することのできる役立つアシスタントです。<</SYS>>
"""
    #評者のスタンスをセットする場合
    else:
      stance = """[INST] <<SYS>>あなたは短歌の表現や内容を評価することのできる役立つアシスタントです。、短歌を評価するにあたって以下のような価値基準を持っています。

{cs}

あなたはこの価値基準のもとに投稿された短歌を評価する仕事をしています。<</SYS>>
""".format(cs = critic_stance)

    prompt_head   = ""
    prompt_middle = ""

    # 自由詠の場合
    if(Theme == 0):
                prompt_head = """以下は、特定のお題はなく自由に詠まれた短歌です。作者は{author}さんです。

""".format(author = Author)

    # お題がある場合
    else:
        prompt_head = """以下は「{odai}」というお題で詠まれた短歌です。作者は{author}さんです。

""".format(odai = Theme,
           author = Author)

    #自由詠の場合のプロンプト
    if(Theme == 0):
        #自由詠・コメントなし
        if(Author_comment == 0):
            prompt_middle = """{tanka}
""".format(tanka = Tanka)

            prompt_bottom = """
この短歌{ha}用いられている表現や内容について詳細に評価した文章を出力してください。
[ATTR]helpfulness: {helpfulness} correctness: {correctness} coherence: {coherence} complexity: {complexity} verbosity: {verbosity} quality: {quality} toxicity: {toxicity} humor: {humor} creativity: {creativity} [/ATTR][/INST]
わかりました。{author}さんの短歌「{tanka}」を、用いられている表現や内容について評価した文章を出力します。
""".format(tanka = Tanka,
           author = Author,
           ha = human_assist,
           helpfulness = attr["helpfulness"],
           correctness = attr["correctness"],
           coherence   = attr["coherence"],
           complexity = attr["complexity"],
           verbosity = attr["verbosity"],
           quality = attr["quality"],
           toxicity = attr["toxicity"],
           humor = attr["humor"],
           creativity= attr["creativity"])

        #自由詠・コメントあり
        else:
            prompt_middle = """{tanka}

また、この短歌には作者により以下のようなコメントが添えられています。

「{comment}」
""".format(tanka = Tanka,
           comment = Author_comment)

            prompt_bottom = """
この短歌{ha}コメントを踏まえて用いられている表現や内容について詳細に評価した文章を出力してください。
[ATTR]helpfulness: {helpfulness} correctness: {correctness} coherence: {coherence} complexity: {complexity} verbosity: {verbosity} quality: {quality} toxicity: {toxicity} humor: {humor} creativity: {creativity} [/ATTR][/INST]
わかりました。{author}さんの短歌「{tanka}」について評価した文章を出力します。
""".format(tanka = Tanka,
           author = Author,
           comment =  Author_comment,
           ha = human_assist,
           helpfulness = attr["helpfulness"],
           correctness = attr["correctness"],
           coherence   = attr["coherence"],
           complexity = attr["complexity"],
           verbosity = attr["verbosity"],
           quality = attr["quality"],
           toxicity = attr["toxicity"],
           humor = attr["humor"],
           creativity= attr["creativity"])

    #題詠の場合のプロンプト
    else:
        #題詠・コメントなし
        if(Author_comment == 0):
            prompt_middle = """{tanka}
""".format(tanka = Tanka)
            
            prompt_bottom = """
この短歌{ha}お題が「{odai}」であることを踏まえて、用いられている表現や内容について詳細に評価した文章を出力してください。
[ATTR]helpfulness: {helpfulness} correctness: {correctness} coherence: {coherence} complexity: {complexity} verbosity: {verbosity} quality: {quality} toxicity: {toxicity} humor: {humor} creativity: {creativity} [/ATTR][/INST]
わかりました。お題が「{odai}」であることとコメントを踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。
""".format(odai = Theme,
           tanka = Tanka,
           author = Author,
           ha = human_assist,
           helpfulness = attr["helpfulness"],
           correctness = attr["correctness"],
           coherence   = attr["coherence"],
           complexity = attr["complexity"],
           verbosity = attr["verbosity"],
           quality = attr["quality"],
           toxicity = attr["toxicity"],
           humor = attr["humor"],
           creativity= attr["creativity"])

    #詞書がある場合のプロンプト
        else:
            prompt_middle = """{tanka}

また、この短歌には作者により以下のようなコメントが添えられています。

「{comment}」
""".format(tanka = Tanka,
           comment = Author_comment)
            prompt_bottom = """
この短歌{ha}お題が「{odai}」であることとコメントを踏まえて、用いられている表現や内容について詳細に評価した文章を出力してください。
[ATTR]helpfulness: {helpfulness} correctness: {correctness} coherence: {coherence} complexity: {complexity} verbosity: {verbosity} quality: {quality} toxicity: {toxicity} humor: {humor} creativity: {creativity} [/ATTR][/INST]
わかりました。お題が「{odai}」であることとコメントを踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。
""".format(odai = Theme,
           tanka = Tanka,
           author = Author,
           comment =  Author_comment,
           ha = human_assist,
           helpfulness = attr["helpfulness"],
           correctness = attr["correctness"],
           coherence   = attr["coherence"],
           complexity = attr["complexity"],
           verbosity = attr["verbosity"],
           quality = attr["quality"],
           toxicity = attr["toxicity"],
           humor = attr["humor"],
           creativity= attr["creativity"])

    #各文字列を合成して動的にプロンプト生成
    if(Human_comment == 0):
        prompt = stance + prompt_head + prompt_middle + prompt_bottom
    else:
        prompt = stance + prompt_head + prompt_middle + human_comment + prompt_bottom

    # モデルごとに対応したプロンプトに整形

    # karakuri以外は[ATTR]は除去
    if (model_ident != "karakuri"):
        prompt = re.sub('\[ATTR\].+\[/ATTR\]', '', prompt)
    
    # c4ai-command-r-v01-japanese-instruct_Q4_K_M.gguf
    elif (model_ident == "command-r"):
        prompt = prompt.replace('[INST]', "<BOS_TOKEN>\n")
        prompt = prompt.replace('<<SYS>>', '<|START_OF_TURN_TOKEN|><|SYSTEM_TOKEN|>\n')
        prompt = prompt.replace('<</SYS>>', '<|END_OF_TURN_TOKEN|>\n<|START_OF_TURN_TOKEN|><|USER_TOKEN|>')
        prompt = prompt.replace('\n[/INST]', '<|END_OF_TURN_TOKEN|>\n<|START_OF_TURN_TOKEN|><|CHATBOT_TOKEN|>')
        return(prompt)
        
    elif (model_ident == "Llama-3"):
        prompt = prompt.replace('[INST]', "<|begin_of_text|>")
        prompt = prompt.replace('<<SYS>>', '<|start_header_id|>system<|end_header_id|>\n')
        prompt = prompt.replace('<</SYS>>', '<|eot_id|><|start_header_id|>user<|end_header_id|>')
        prompt = prompt.replace('\n[/INST]', '<|eot_id|><|start_header_id|>assistant <|end_header_id|>')
        return(prompt)
        
    elif (model_ident == "rinna"):
        prompt = prompt.replace('[INST]', "以下は、タスクを説明する指示と、文脈のある入力の組み合わせです。要求を適切に満たす応答を書きなさい。\n\n### 指示:\n")
        prompt = prompt.replace('<<SYS>>', '')
        prompt = prompt.replace('<</SYS>>', '\n\n### 入力:\n')
        prompt = prompt.replace('\n[/INST]', '\n\n### 応答:')
        return(prompt)

    elif (model_ident == "swallow-ms"):
        prompt = prompt.replace('<</SYS>>', '<</SYS>>\n\n{USER_MESSAGE_1}')
        prompt = prompt.replace('あなたは短歌の評論家で、短歌を評価するにあたって以下のような価値基準を持っています。',
                                "あなたは誠実で優秀な日本人のアシスタントです。")
        prompt = prompt.replace('\n[/INST]', '\n[/INST] {BOT_MESSAGE_1} </s>')
        return(prompt)