# お題の有無、作者コメントの有無、指摘コメントの有無に応じて動的にプロンプトを生成、入力モデルに対応したプロンプトを生成するモジュール
def tanka_prompt(configs,
                 Theme,
                 Tanka,
                 Author,
                 Author_comment,
                 Human_comment):

    critic_stance = configs["stance"]

    # promptパーツの初期値を設定
    sys = ""
    user = ""
    assist = ""

    # 再生成で生じる欠損値のエラーを修正
    if (Human_comment == "nan"):
        Human_comment = "NaN"
    if (Author_comment == "nan"):
        Author_comment = "NaN"
    # for debug
    #print ("\ncritic_stance: " + str(critic_stance))
    #print ("Theme: " +  str(Theme))
    #print ("Human_comment: " + Human_comment)
    #print ("Author_comment: " + Author_comment)
    
    # system promptを生成
    if (critic_stance == 0):  # stanceあり
        sys = "あなたは短歌の表現や内容を評価することのできる役立つアシスタントです。"
    else:                     # stanceなし
        sys = """あなたは短歌の表現や内容を評価することのできる役立つアシスタントで、以下のような価値観を持っています。
{stance}
""".format(stance = critic_stance)

    # user prompt を生成(動的には作らず、8条件全部を網羅する形で記述)
    if Theme == 0 and Author_comment == "NaN" and Human_comment == "NaN":
        user = """以下は、{author}さんが詠まれた短歌です。
{tanka}

この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(author = Author, tanka = Tanka)
        
    elif Theme == 0 and Author_comment != "NaN" and Human_comment == "NaN":
        user = """以下は、{author}さんが詠まれた短歌です。
{tanka}

また、この短歌には作者により以下のようなコメントが添えられています。
「{author_comment}」

作者のコメントを踏まえて、この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(author = Author, tanka = Tanka, author_comment = Author_comment)
        
    elif Theme == 0 and Author_comment == "NaN" and Human_comment != "NaN":
        user = """以下は、{author}さんが詠まれた短歌です。
{tanka}

加えて、あなたがこの短歌について誤解したり見落としたりしていることとして、以下の点が指摘されています。
「{human}」

この指摘を踏まえて、この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(author = Author, tanka = Tanka, human = Human_comment)
        
    elif Theme == 0 and Author_comment != "NaN" and Human_comment != "NaN":
        user = """以下は、{author}さんが詠まれた短歌です。
{tanka}

また、この短歌には作者により以下のようなコメントが添えられています。
「{author_comment}」

加えて、あなたがこの短歌について誤解したり見落としたりしていることとして、以下の点が指摘されています。
「{human}」

作者のコメントとこの指摘を踏まえて、この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(author = Author, tanka = Tanka, author_comment = Author_comment, human = Human_comment)
        
    elif Theme != "NaN" and Author_comment == "NaN" and Human_comment == "NaN":
        user = """以下は「{odai}」というお題で詠まれた短歌です。作者は{author}さんです。

{tanka}

お題が「{odai}」であることを踏まえて、この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(odai = Theme, author = Author, tanka = Tanka)
        
    elif Theme != "NaN" and Author_comment != "NaN" and Human_comment == "NaN":
        user = """以下は「{odai}」というお題で詠まれた短歌です。作者は{author}さんです。

{tanka}

また、この短歌には作者により以下のようなコメントが添えられています。
「{author_comment}」

お題が「{odai}」であることと作者のコメントを踏まえて、この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(odai = Theme, author = Author, tanka = Tanka, author_comment = Author_comment)
        
    elif Theme != "NaN" and Author_comment == "NaN" and Human_comment != "NaN":
        user = """以下は「{odai}」というお題で詠まれた短歌です。作者は{author}さんです。

{tanka}

加えて、あなたがこの短歌について誤解したり見落としたりしていることとして、以下の点が指摘されています。
「{human}」

お題が「{odai}」であることとこの指摘を踏まえて、この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(odai = Theme, author = Author, tanka = Tanka, human = Human_comment)
    elif Theme != "NaN" and Author_comment != "NaN" and Human_comment != "NaN":
        user = """以下は「{odai}」というお題で詠まれた短歌です。作者は{author}さんです。

{tanka}

また、この短歌には作者により以下のようなコメントが添えられています。
「{author_comment}」

加えて、あなたがこの短歌について誤解したり見落としたりしていることとして、以下の点が指摘されています。
「{human}」

お題が「{odai}」であることと作者のコメント、そしてこの指摘を踏まえて、この短歌の表現や内容について詳細に評価した文章を出力してください。""".format(odai = Theme, author = Author, tanka = Tanka, author_comment = Author_comment, human = Human_comment)

    # assist promptを生成(8つの全条件で指定)
    if Theme == 0 and Author_comment == "NaN" and Human_comment == "NaN":
        assist = """わかりました。{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(author = Author, tanka = Tanka)
    elif Theme == 0 and Author_comment != "NaN" and Human_comment == "NaN":
        assist = """わかりました。作者のコメントを踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(author = Author, tanka = Tanka)
    elif Theme == 0 and Author_comment == "NaN" and Human_comment != "NaN":
        assist = """わかりました。指摘された点を踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(author = Author, tanka = Tanka)
    elif Theme == 0 and Author_comment != "NaN" and Human_comment != "NaN":
        assist = """わかりました。作者のコメントと指摘された点を踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(author = Author, tanka = Tanka)
    elif Theme != "NaN" and Author_comment == "NaN" and Human_comment == "NaN":
        assist = """わかりました。お題が「{odai}」であることを踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(odai = Theme, author = Author, tanka = Tanka)
    elif Theme != "NaN" and Author_comment != "NaN" and Human_comment == "NaN":
        assist = """わかりました。お題が「{odai}」であることと作者のコメントを踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(odai = Theme, author = Author, tanka = Tanka)
    elif Theme != "NaN" and Author_comment == "NaN" and Human_comment != "NaN":
        assist = """わかりました。お題が「{odai}」であること、そして指摘された内容を踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(odai = Theme, author = Author, tanka = Tanka)
    elif Theme != "NaN" and Author_comment != "NaN" and Human_comment != "NaN":
        assist = """わかりました。お題が「{odai}」であることと作者のコメント、そして指摘された内容を踏まえて、{author}さんの短歌「{tanka}」について評価した文章を出力します。""".format(odai = Theme, author = Author, tanka = Tanka)

    return (sys, user, assist)

# 歌会モードのプロンプト生成
def utakai_prompt(theme, row, LLMs):
    sys = ""
    user = ""
    assist = ""
    
    # 自由詠
    if(theme == 0):
        sys = f"""あなたは、異なる評価者の複数のコメントを要約し、共通点や相違点について整理することのできるファシリテーターです。
以下に、{row["Author"]}さんの短歌「{row["Content"]}」について、{str(len(LLMs))}人の異なる評価者によるコメントがあります。
"""
        LLM_num = 1
        for LLM in LLMs:
            row[f"{LLM}"] = row[f"{LLM}"].replace("\n\n", "\n")
            user = user + f"\n{str(LLM_num)}人目の評価者のコメントは以下の通りです。\n"
            user = user + "『" + row[f"{LLM}"] + "』\n"
        
            LLM_num  += 1
            
        prompt = sys + user + f"""\n以上の{str(len(LLMs))}個のコメントを以下の基準で要約してください。
1. 評価者間の共通点
2. 評価者間の相違点
最後に、ファシリテーターとしてのコメントを補足してください。"""
    # 題詠
    else:
        sys = f"""あなたは、異なる評価者の複数のコメントについて要約、整理することのできるファシリテーターです。
以下に、{theme}というお題で{row["Author"]}さんが詠んだ短歌「{row["Content"]}」について、{str(len(LLMs))}人の異なる評価者によるコメントがあります。
"""
        user = ""
        LLM_num = 1
        for LLM in LLMs:
            row[f"{LLM}"] = row[f"{LLM}"].replace("\n\n", "\n")
            user = user + f"\n{str(LLM_num)}人目の評価者のコメントは以下の通りです。\n"
            user = user + "『" + row[f"{LLM}"] + "』\n"
        
            LLM_num  += 1
            
        prompt = sys + user + f"""\n以上の{str(len(LLMs))}個のコメントを以下の基準で要約してください。
1. 評価者間の共通点
2. 評価者間の相違点
最後に、ファシリテーターとしてのコメントを補足してください。"""
        
    return(sys, user, assist)

# 連作モードのプロンプト生成
def rensak_prompt(theme, row):
    sys = ""
    user = ""
    assist = ""
    
        # 自由詠
    if(theme == 0):
        sys = f"""あなたは短歌の表現や内容を評価することのできる役立つアシスタントです。
以下は{row["Author"]}さんによる{row["count"]}首からなる短歌連作で、タイトルは「{row["Title"]}」です。

{row["Content"]}

この連作の表現や内容について、各短歌間のつながりを踏まえて考察した詳細な文章を出力してください。
"""
    return(sys, user, assist)













    