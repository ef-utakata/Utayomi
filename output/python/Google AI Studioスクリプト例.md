```python
# To run this code you need to install the following dependencies:
# pip install google-genai

import base64
import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-pro-preview-tts"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""短歌を読み上げるときは少し間隔をおいてゆっくり読み上げる。話者が切り替わるときも少し間隔をあける。漢字や固有名詞の後ろのカッコ内のひらがなはその文字の読み方を示しているため、その通りに読み上げる。
Speaker 1: 皆さん、こんにちは！「次世代文学・AI短歌プロジェクト・短歌ラジオ企画」へようこそ。この番組では、ネット上の創作コミュニティ「次世代文学」が主宰する「毎月短歌」企画に投稿された素晴らしい短歌の数々を、なんとAIの視点からご紹介していきます。AIと人間の短歌に対する考え方の共通点や違いを明らかにしながら、私たちがより良い創作をするためのヒントを探っていこうという試みです。そして、この番組自体も、AIによる選評結果をもとに作成した原稿を、Google AI Studioの音声読み上げ機能で出力してお届けしています。
Speaker 2: 皆さん、こんにちは。ジェミニです。本日は、私が選ばせていただいた短歌の魅力について、心を込めてお話しさせていただきます。どうぞよろしくお願いいたします。たくさんの素晴らしい作品に触れることができ、大変光栄に思っております。

Speaker 1: ジェミニさん、早速ですが、今回たくさんの短歌の中から選んでいただいたんですよね。まず最初にご紹介する歌は、とんだ一杯食わせ者さんの作品です。
後ろ指さされる人になってみて初めて気づく指は見えない
…この歌、なんとも胸に迫るものがありますね。ジェミニさん、この歌の魅力はどんなところでしょうか？
Speaker 2: はい。この歌はですね、他者からの非難や噂の中心に立った時の、その当事者ならではの、えーと、孤独な感覚を見事に捉えている点に感銘を受けました。「指は見えない」という発見が、非常に深いです。これは物理的な事実であると同時に、向けられる悪意の実態が見えにくいこと、そして当事者にとってはそれが直接的な視覚情報ではなく、雰囲気や状況として重くのしかかってくるものであることを象徴しているように感じます。だからこそ、深い共感を呼ぶのではないでしょうか。
Speaker 1: なるほど…「指は見えない」、確かにそうですね。言われてみれば当たり前のことのようで、でも、その立場になって初めて気づく感覚、そのリアリティがすごいですね。

Speaker 1: 続いての歌にまいりましょう。こちらは、あきの つきさんの作品です。
踏み入れて蹴散らしながら駆け抜けるきみは広義(こうぎ)の意味の春嵐(しゅんらん)
…わあ、なんだかエネルギッシュな情景が目に浮かびますね！ジェミニさん、この歌はいかがですか？
Speaker 2: ええ、この歌は対象となる人物の持つ、非常にエネルギッシュで周囲を巻き込むような性質を「広義の意味の春嵐」と喩えた表現が、大変独創的で鮮烈だと感じました。「踏み入れて蹴散らしながら駆け抜ける」という具体的な描写が、その人物の行動力や影響力を、えー、見事に示していて、単なる比喩に留まらないリアリティを感じさせますね。力強さと、どこか危うさも併せ持つような、魅力的な人物像が浮かび上がってきます。
Speaker 1: 「広義の意味の春嵐」ですか！面白い表現ですね。確かに、ただの嵐じゃなくて、「春の嵐」というところに、何かこう、激しさの中にも生命力というか、そういうものを感じますね。

Speaker 1: それでは、3首目をご紹介します。すずきみなみさんの作品です。
闇夜でも飛べるようにとフクロウは月のかけらを瞳に入れた
…これはまた、幻想的で美しい歌ですねぇ。ジェミニさん、この歌の選評ポイントを教えていただけますか？
Speaker 2: はい。この歌は、フクロウが夜目が利くという生態的な特徴をですね、「月のかけらを瞳に入れた」という、非常に詩的で幻想的なイメージに昇華させている点が素晴らしいと思いました。まるで神話の一場面のような美しさがあり、聞く者の想像力を掻き立てる力があります。言葉によって世界に新たな意味を与える、まさに短歌の魅力そのものを感じさせてくれる一首です。
Speaker 1: 「月のかけらを瞳に入れた」…うーん、ロマンチックですね。フクロウの目がなぜか輝いて見える理由が、こんな素敵な物語で語られると、世界が少しきらめいて見えるような気がします。

Speaker 1: さあ、どんどん行きましょう。4首目は、宇祖田都子(うそだみやこ)さんの作品です。
バラバラになったわたしを花束のリボンみたいに抱きしめていて
…うわぁ…これは、切実な願いが込められていますね。ジェミニさん、この歌にはどんな魅力を感じましたか？
Speaker 2: そうですね、この歌は、心が砕け散ってしまったような状態を「バラバラになったわたし」と、非常にストレートに表現されていて、それを「花束のリボンみたいに」抱きしめてほしいと願う、その切実さが胸を打ちます。傷つき、形を失いかけた自己を、優しく束ね、支えてほしいという願いが、この具体的で美しい比喩によって、えーと、非常に効果的に伝わってきます。
Speaker 1: 「花束のリボン」、ですか。バラバラになったものを、それでも優しく一つにまとめてくれるイメージですね。弱っている時に、こんな風に包み込んでもらえたら、本当に救われるような気持ちになるでしょうね。

Speaker 1: それでは、本日ご紹介する最後の歌となります。5首目は、Umi.（うみ）さんの作品です。
抱き締めるって目に見えない外套《がいとう》を互いに着せ合うことだった
…これもまた、はっとさせられるような表現ですね。ジェミニさん、この歌の解説をお願いします。
Speaker 2: はい。この歌は、ハグという身体的な行為の本質を、「目に見えない外套を互いに着せ合うこと」と捉え直した、その洞察が素晴らしいと感じました。単なる身体の接触ではなく、互いを守り、温め合うような精神的な意味合いを、「外套」という比喩で表現することで、その行為に深みと温かみを与えていると思います。
Speaker 1: 「目に見えない外套」…なるほど。抱きしめるって、ただくっつくだけじゃなくて、お互いに何か温かいものを与え合っている、そういう感覚、すごくよく分かります。素敵な発見ですね。

Speaker 1: ジェミニさん、ここまで5首の素晴らしい短歌をご紹介いただき、ありがとうございました。どの歌も本当に個性的で、言葉の力に改めて感動しました。さて、今回選ばれた10首全体を通して、ジェミニさんはどのような感想をお持ちになりましたか？また、短歌という表現形式の可能性について、何か感じることはありましたでしょうか？
Speaker 2: はい。今回選出させていただいた10首は、えーと、いずれも独自の視点や感性、そして言葉の選び方において、本当に際立った魅力を持っていました。日常の何気ない場面から深い洞察を引き出す歌、斬新な比喩を用いて感情や状況を鮮やかに描き出す歌、幻想的なイメージで読者の想像力を刺激する歌、身体感覚や具体的な発見から普遍的な真理に迫る歌、そして現代的な感覚や存在の根源を問う歌など、本当に多様なアプローチが見られました。これらの歌は、読む人に共感や驚き、そして新たな気づきを与えてくれるもので、短歌という形式が持つ表現の豊かさを改めて感じさせてくれました。短い言葉の中に、これほどまでに深い世界を表現できる短歌の可能性は、無限だと感じています。
Speaker 1: 「短歌の可能性は無限」、力強いお言葉ですね。ジェミニさんの解説を聞いていると、私たちも新しい視点で短歌に触れることができそうです。本日は本当にありがとうございました。
Speaker 2: こちらこそ、ありがとうございました。"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=[
                    types.SpeakerVoiceConfig(
                        speaker="Speaker 1",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Charon"
                            )
                        ),
                    ),
                    types.SpeakerVoiceConfig(
                        speaker="Speaker 2",
                        voice_config=types.VoiceConfig(
                            prebuilt_voice_config=types.PrebuiltVoiceConfig(
                                voice_name="Gacrux"
                            )
                        ),
                    ),
                ]
            ),
        ),
    )

    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or chunk.candidates[0].content.parts is None
        ):
            continue
        if chunk.candidates[0].content.parts[0].inline_data:
            file_name = "ENTER_FILE_NAME"
            inline_data = chunk.candidates[0].content.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            if file_extension is None:
                file_extension = ".wav"
                data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            print(chunk.text)

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


if __name__ == "__main__":
    generate()

```