"""Utayomi – 共通 TTS ユーティリティ

Gemini の Multi-Speaker TTS API をラップし、Markdown 等のテキストから
音声ファイル（wav / ogg など）を生成する純粋関数群。

元の `tts_tool.py` から必要部分のみを移植・簡素化した。
"""

from __future__ import annotations

import base64
import mimetypes
import os
import struct
from typing import List

# Google GenAI (>=0.8.5)
import google.genai as genai
from google.genai import types
from lib.env_loader import get_google_api_key, get_google_api_key_paid

# ---------------------------------------------------------------------------
# low-level helpers
# ---------------------------------------------------------------------------


def save_binary_file(file_name: str, data: bytes) -> None:
    """Save *data* to *file_name* (overwrites)."""

    with open(file_name, "wb") as f:
        f.write(data)
    print(f"[MESSAGE]: 音声ファイルを保存しました → {file_name}")


def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Return {bits_per_sample, rate} extracted from a mime-type string."""

    bits_per_sample = 16  # default
    rate = 24000  # default Gemini sample-rate

    for param in mime_type.split(";"):
        param = param.strip().lower()
        if param.startswith("rate="):
            try:
                rate = int(param.split("=", 1)[1])
            except (ValueError, IndexError):
                pass
        elif param.startswith("audio/l"):
            try:
                bits_per_sample = int(param.split("audio/l", 1)[1])
            except (ValueError, IndexError):
                pass

    return {"bits_per_sample": bits_per_sample, "rate": rate}


def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Convert raw PCM (audio/L16;rate=24000 …) to RIFF-WAV bytes."""

    params = parse_audio_mime_type(mime_type)
    bits_per_sample = params["bits_per_sample"]
    sample_rate = params["rate"]

    num_channels = 1  # mono
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",
        chunk_size,
        b"WAVE",
        b"fmt ",
        16,
        1,
        num_channels,
        sample_rate,
        byte_rate,
        block_align,
        bits_per_sample,
        b"data",
        data_size,
    )
    return header + audio_data


# ---------------------------------------------------------------------------
# high-level wrapper
# ---------------------------------------------------------------------------


def generate_speech(
    script_text: str,
    output_basename: str,
    model_name: str = "gemini-2.5-pro-preview-tts",
    speaker_voice_configs: List[types.SpeakerVoiceConfig] | None = None,
    wait_sec: int = 20,
) -> str:
    """Generate speech from *script_text* and save to a file.

    Returns the generated file path. Requires env var `GOOGLE_API_KEY`.
    """

    # ------------------------------------------------------------------
    # Build default multi-speaker config if none supplied.
    # Gemini TTS 原稿は 2 名対話を想定 (Speaker 1 / Speaker 2)。

    if not speaker_voice_configs:
        speaker_voice_configs = [
            types.SpeakerVoiceConfig(
                speaker="Speaker 1",
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Charon")
                ),
            ),
            types.SpeakerVoiceConfig(
                speaker="Speaker 2",
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name="Gacrux")
                ),
            ),
        ]

    speech_cfg = types.SpeechConfig(
        multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
            speaker_voice_configs=speaker_voice_configs
        )
    )

    client = genai.Client(api_key=get_google_api_key_paid())

    contents = script_text

    config = types.GenerateContentConfig(
        response_modalities=["audio"],
        speech_config=speech_cfg,
    )

    print(f"[MESSAGE]: Gemini TTS で音声合成を開始 ({model_name}) …")

    audio_buffer: bytes = b""
    mime_type: str | None = None

    for chunk in client.models.generate_content_stream(
        model=model_name, contents=contents, config=config
    ):
        if (
            chunk.candidates is None
            or chunk.candidates[0].content is None
            or not chunk.candidates[0].content.parts
        ):
            continue

        part = chunk.candidates[0].content.parts[0]
        if part.inline_data:
            if mime_type is None:
                mime_type = part.inline_data.mime_type
            audio_buffer += part.inline_data.data

    if not audio_buffer or mime_type is None:
        raise RuntimeError("TTS 生成に失敗しました。API からオーディオデータを取得できませんでした。")

    # decide extension & convert if needed
    if "audio/l" in mime_type.lower():
        # raw PCM → wav
        print("[MESSAGE]: raw PCM を WAV に変換します …")
        audio_data = convert_to_wav(audio_buffer, mime_type)
        ext = ".wav"
    else:
        audio_data = audio_buffer
        ext = mimetypes.guess_extension(mime_type) or ".audio"

    out_path = f"{output_basename}{ext}"
    save_binary_file(out_path, audio_data)

    # optional wait to mitigate rate limits
    if wait_sec > 0:
        import time
        print(f"[MESSAGE]: waiting {wait_sec} sec after TTS …")
        time.sleep(wait_sec)

    return out_path


__all__ = [
    "generate_speech",
    "generate_radio_script",
    "save_binary_file",
    "convert_to_wav",
    "parse_audio_mime_type",
]

# ---------------------------------------------------------------------------
# radio script generation helper
# ---------------------------------------------------------------------------


def generate_radio_script(
    selection_markdown: str,
    template_path: str,
    model_name: str = "gemini-2.5-pro-preview",
    temperature: float = 0.7,
    wait_sec: int = 20,
    theme: str | None = None,
    application: str | None = None,
    is_series: bool = False,
) -> str:
    """Generate a radio-show style script from *selection_markdown*.

    The *template_path* must contain a placeholder string
    "{出力した選評とコメントをここに入力}" which will be replaced by the
    Markdown text.
    
    If is_series=True, automatically selects series-specific template.
    """

    # 連作モードの場合は自動的に連作用テンプレートを選択
    if is_series:
        template_dir = os.path.dirname(template_path)
        template_name = "generate_script_prompt_series.md"
        series_template_path = os.path.join(template_dir, template_name)
        
        if os.path.exists(series_template_path):
            template_path = series_template_path
            print(f"[MESSAGE]: 連作モード - 連作用テンプレートを使用: {template_path}")
        else:
            print(f"[WARNING]: 連作用テンプレート {series_template_path} が見つかりません。通常テンプレートを使用します。")

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # ---------------------------------------
    # テンプレート置換
    # ---------------------------------------

    prompt_text = template.replace(
        "{出力した選評とコメントをここに入力}", selection_markdown
    )

    # 企画セクションを置換（テンプレートに含まれていない場合も考慮）
    if "{企画セクション}" in prompt_text:
        if application and str(application) not in ("0", "", "None"):
            application_sentence = f"今回の投稿企画は「{application}」です。"
        else:
            application_sentence = ""
        prompt_text = prompt_text.replace("{企画セクション}", application_sentence)

    # お題セクションを置換（テンプレートに含まれていない場合も考慮）
    if "{お題セクション}" in prompt_text:
        if theme and str(theme) not in ("0", "", "None"):
            theme_sentence = (
                f"今回のお題は「{theme}」です。そのお題で詠まれた短歌について"
                "Gemini が選評を行いました。"
            )
        else:
            theme_sentence = ""
        prompt_text = prompt_text.replace("{お題セクション}", theme_sentence)
    # 旧テンプレート互換: placeholder がない場合は何もしない

    import google.genai as genai

    client = genai.Client(api_key=get_google_api_key())

    print(f"[MESSAGE]: Gemini にラジオ原稿生成を依頼しています … ({model_name})")

    config = genai.types.GenerateContentConfig(
        temperature=temperature,
    )
    
    response = client.models.generate_content(
        model=model_name,
        contents=prompt_text,
        config=config,
    )

    # New Gemini API response handling
    if hasattr(response, 'text') and response.text:
        script_text = response.text
    elif hasattr(response, 'parts') and response.parts:
        script_text = response.text
    else:
        raise RuntimeError("Gemini script generation returned empty response.")

    if wait_sec > 0:
        import time
        print(f"[MESSAGE]: waiting {wait_sec} sec after script generation …")
        time.sleep(wait_sec)

    return script_text
