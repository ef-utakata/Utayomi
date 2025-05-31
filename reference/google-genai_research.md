■ API 概要

* モデル呼び出しのエントリポイント：
  * google-generativeai Python SDK v0.8.5では非推奨となっており、新しい `google-genai` SDKへの移行が推奨されています
  * 新しいSDK（google-genai）では、エントリポイントは `genai.Client()` となり、このクライアントオブジェクトを通じて各種機能にアクセスします
  * 旧API（`genai.GenerativeModel`）から新API（`client.models.generate_content`）に変更されています

* TTS (Text-to-Speech) APIの呼び出し手順・必須引数：
  * `response_modalities=["AUDIO"]` を設定し、音声出力を有効にします
  * `speech_config=types.SpeechConfig` を指定し、音声設定を構成します
  * 単一話者の場合は `voice_config=types.VoiceConfig` で話者の音声を設定します
  * 複数話者の場合は `multi_speaker_voice_config=types.MultiSpeakerVoiceConfig` で各話者の設定を行います
  * 各話者には `prebuilt_voice_config=types.PrebuiltVoiceConfig` で音声名を指定します

* 音声ストリーミングの受け取り：
  * レスポンスの音声データは `response.candidates[0].content.parts[0].inline_data.data` に格納されます
  * このデータは16ビットPCM形式のバイナリデータで、サンプルレートは24kHzです
  * WAVファイル形式で保存する場合は、適切なヘッダー情報を追加する必要があります

■ サンプルコード

```python
# Gemini 2.5モデルでTTSを使用する最小限の実装例
from google import genai
from google.genai import types
import wave
import os

# APIキーを環境変数から取得
api_key = os.environ.get("GOOGLE_API_KEY")
client = genai.Client(api_key=api_key)

# 単一話者のTTS生成
def generate_tts_single_speaker(text, voice_name="Kore", output_file="output.wav"):
    """
    テキストを音声に変換し、ファイルに保存する
    
    Args:
        text: 音声に変換するテキスト
        voice_name: 使用する音声の名前（デフォルト: "Kore"）
        output_file: 出力ファイル名
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice_name,
                    )
                )
            ),
        )
    )

    # 音声データを取得
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    
    # WAVファイルとして保存（サンプルレート: 24kHz, 16ビット, モノラル）
    with wave.open(output_file, "wb") as wf:
        wf.setnchannels(1)  # モノラル
        wf.setsampwidth(2)  # 16ビット = 2バイト
        wf.setframerate(24000)  # 24kHz
        wf.writeframes(audio_data)
    
    print(f"音声ファイルを保存しました: {output_file}")
    return audio_data

# 複数話者のTTS生成
def generate_tts_multi_speakers(text, speakers_config, output_file="output_multi.wav"):
    """
    複数話者のテキストを音声に変換し、ファイルに保存する
    
    Args:
        text: 会話形式のテキスト
        speakers_config: 話者名と音声名の辞書 (例: {"Joe": "Kore", "Jane": "Puck"})
        output_file: 出力ファイル名
    """
    # 話者の設定を作成
    speaker_voice_configs = [
        types.SpeakerVoiceConfig(
            speaker=name,
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name=voice,
                )
            )
        )
        for name, voice in speakers_config.items()
    ]
    
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                    speaker_voice_configs=speaker_voice_configs
                )
            )
        )
    )

    # 音声データを取得
    audio_data = response.candidates[0].content.parts[0].inline_data.data
    
    # WAVファイルとして保存
    with wave.open(output_file, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_data)
    
    print(f"複数話者の音声ファイルを保存しました: {output_file}")
    return audio_data

if __name__ == "__main__":
    # 単一話者の例
    generate_tts_single_speaker("Say cheerfully: Have a wonderful day!", voice_name="Kore")
    
    # 複数話者の例
    conversation_text = """TTS the following conversation between Joe and Jane:
    Joe: How's it going today Jane?
    Jane: Not too bad, how about you?"""
    
    generate_tts_multi_speakers(
        conversation_text, 
        speakers_config={"Joe": "Kore", "Jane": "Puck"}
    )
```

■ Breaking changes

* 0.6系以前から大きな変更点：
  * `google-generativeai` SDKは非推奨となり、新しい`google-genai` SDKへの移行が推奨されています
  * クラス階層が変更され、`genai.GenerativeModel` から `genai.Client().models.generate_content` への変更が必要です
  * 設定方法が変更され、モデルの作成時にパラメータを渡す代わりに、`config` 引数でPydanticモデルまたは辞書として渡すようになりました
  * 音声生成機能のインターフェースも変更され、`speech_config` パラメータの構造が更新されています

* 移行方法：
  * 古いSDKを新しいSDKに置き換える：`pip uninstall google-generativeai && pip install google-genai`
  * クライアントの作成方法を変更：`genai.configure(api_key=...)` → `client = genai.Client(api_key=...)`
  * APIの呼び出し方法を変更：`model.generate_content()` → `client.models.generate_content()`
  * パラメータの指定方法を変更：個別引数 → `config` パラメータ内に記述
  * チャット機能の使用方法を変更：`model.start_chat()` → `client.chats.create()`

■ 参考 URL

* 公式ドキュメント：
  * Google Gen AI SDK: https://googleapis.github.io/python-genai/
  * Gemini API音声生成(TTS)ガイド: https://ai.google.dev/gemini-api/docs/speech-generation
  * 移行ガイド: https://ai.google.dev/gemini-api/docs/migrate

* GitHub:
  * 新SDKリポジトリ: https://github.com/googleapis/python-genai
  * 旧SDKリポジトリ: https://github.com/google-gemini/deprecated-generative-ai-python

* PyPI:
  * 新SDK: https://pypi.org/project/google-genai/
  * 旧SDK: https://pypi.org/project/google-generativeai/