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

from google import genai
from google.genai import types

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

    if speaker_voice_configs is None:
        speaker_voice_configs = [
            types.SpeakerVoiceConfig(speaker="speaker_a", voice="VOICE_FEMALE_1")
        ]

    client = genai.Client()

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=script_text)],
        )
    ]

    config = types.GenerateContentConfig(
        response_modalities=["audio"],
        speech_config=types.SpeechConfig(
            multi_speaker_voice_config=types.MultiSpeakerVoiceConfig(
                speaker_voice_configs=speaker_voice_configs
            )
        ),
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
) -> str:
    """Generate a radio-show style script from *selection_markdown*.

    The *template_path* must contain a placeholder string
    "{出力した選評とコメントをここに入力}" which will be replaced by the
    Markdown text.
    """

    if not os.path.exists(template_path):
        raise FileNotFoundError(f"Prompt template not found: {template_path}")

    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()

    # simple replacement
    prompt_text = template.replace("{出力した選評とコメントをここに入力}", selection_markdown)

    import google.generativeai as genai

    client = genai.Client()
    model = client.models.get(model_name)

    print(f"[MESSAGE]: Gemini にラジオ原稿生成を依頼しています … ({model_name})")

    response = model.generate_content(
        prompt_text,
        generation_config=genai.types.GenerationConfig(temperature=temperature),
    )

    if not response.parts:
        raise RuntimeError("Gemini script generation returned empty response.")

    script_text = response.text

    if wait_sec > 0:
        import time
        print(f"[MESSAGE]: waiting {wait_sec} sec after script generation …")
        time.sleep(wait_sec)

    return script_text
