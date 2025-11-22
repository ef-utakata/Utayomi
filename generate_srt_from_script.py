#!/usr/bin/env python3
"""Generate SRT subtitles from a radio script using Gemini."""

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

import google.genai as genai
from google.genai import types as genai_types

from lib.env_loader import get_google_api_key

SRT_TIME_RE = re.compile(
    r"^(?P<start>\d{2}:\d{2}:\d{2},\d{3})\s+-->\s+(?P<end>\d{2}:\d{2}:\d{2},\d{3})$"
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert a radio script to SRT subtitles aligned to an existing video."
    )
    parser.add_argument("script", help="Path to the radio script text file")
    parser.add_argument("video", help="Path to the rendered video file")
    parser.add_argument(
        "--model",
        default="gemini-2.5-pro",
        help="Gemini model name used for subtitle generation",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.2,
        help="Sampling temperature for Gemini",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Save intermediate prompt/response artifacts for troubleshooting",
    )
    return parser.parse_args()


def get_video_duration(video_path: Path) -> float:
    if not video_path.exists():
        raise FileNotFoundError(f"Video file not found: {video_path}")

    cmd = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        str(video_path),
    ]
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError(
            "ffprobe is required to measure video duration but was not found in PATH."
        ) from exc
    except subprocess.CalledProcessError as exc:
        raise RuntimeError(
            f"Failed to probe video duration via ffprobe: {exc.stderr.strip()}"
        ) from exc

    try:
        duration = float(result.stdout.strip())
    except ValueError as exc:
        raise RuntimeError("ffprobe returned an invalid duration") from exc

    if duration <= 0:
        raise RuntimeError("Video duration must be greater than zero")
    return duration


def write_debug_artifact(
    enabled: bool,
    base_path: Path,
    suffix: str,
    content: str,
    *,
    binary: bool = False,
) -> None:
    if not enabled:
        return
    debug_path = base_path.with_suffix(base_path.suffix + suffix)
    mode = "wb" if binary else "w"
    with open(debug_path, mode) as fh:
        if binary:
            fh.write(content)  # type: ignore[arg-type]
        else:
            fh.write(content)
    print(f"[DEBUG]: Saved {debug_path}")


FENCE_PATTERN = re.compile(r"```(?:srt)?\s*(.*?)```", re.DOTALL | re.IGNORECASE)


def strip_code_fence(text: str) -> str:
    stripped = text.strip()

    fence_match = FENCE_PATTERN.search(stripped)
    if fence_match:
        return fence_match.group(1).strip()

    lines = stripped.splitlines()
    for idx, line in enumerate(lines):
        if line.strip().isdigit():
            return "\n".join(lines[idx:]).strip()

    return stripped


def parse_srt(text: str, max_duration: float) -> List[Tuple[int, str, str, List[str]]]:
    text = strip_code_fence(text)
    blocks = re.split(r"\n\s*\n", text.strip())
    entries: List[Tuple[int, str, str, List[str]]] = []

    last_end_seconds = 0.0
    for block in blocks:
        lines = [line.rstrip() for line in block.strip().splitlines() if line.strip()]
        if len(lines) < 3:
            raise ValueError("Each SRT block must contain an index, timing line, and text")

        try:
            index = int(lines[0])
        except ValueError as exc:
            raise ValueError(f"Invalid SRT index line: {lines[0]}") from exc

        match = SRT_TIME_RE.match(lines[1])
        if not match:
            raise ValueError(f"Invalid SRT timing line: {lines[1]}")

        start_time = match.group("start")
        end_time = match.group("end")
        subtitles = lines[2:]
        if not subtitles:
            raise ValueError("Subtitle text cannot be empty")

        start_seconds = hms_to_seconds(start_time)
        end_seconds = hms_to_seconds(end_time)
        if start_seconds >= end_seconds:
            raise ValueError("Start time must be before end time")
        if start_seconds < last_end_seconds - 0.5:
            raise ValueError("Subtitle timings must be non-overlapping and ordered")
        if end_seconds - max_duration > 1.0:
            raise ValueError("Subtitle end exceeds video duration")

        last_end_seconds = end_seconds
        entries.append((index, start_time, end_time, subtitles))

    # ensure sequential indices
    expected = 1
    for idx, *_ in entries:
        if idx != expected:
            raise ValueError("Subtitle indices must be sequential starting at 1")
        expected += 1

    return entries


def hms_to_seconds(timestamp: str) -> float:
    hours, minutes, rest = timestamp.split(":")
    seconds, millis = rest.split(",")
    total = (
        int(hours) * 3600
        + int(minutes) * 60
        + int(seconds)
        + int(millis) / 1000.0
    )
    return total


def format_srt(entries: List[Tuple[int, str, str, List[str]]]) -> str:
    blocks = []
    for index, start, end, lines in entries:
        block = [str(index), f"{start} --> {end}", *lines]
        blocks.append("\n".join(block))
    return "\n\n".join(blocks) + "\n"


def build_prompt(script_text: str, duration_sec: float) -> str:
    minutes = int(duration_sec // 60)
    seconds = int(duration_sec % 60)
    fractional = duration_sec - int(duration_sec)
    millis = round(fractional * 1000)
    duration_label = f"{minutes}m {seconds}s"
    return f"""
あなたはプロのナレーション編集者です。以下の条件に従ってSRT形式字幕を作成してください。

- 元の読み上げ原稿は日本語で記述されています。文脈を保ちながら自然な区切りで字幕を分割してください。
- 字幕は1行あたり最大2行まで、各字幕は原稿の順番を保ってください。
- 字幕全体は動画再生時間 {duration_label} (合計 {duration_sec:.3f} 秒) 全体にわたって均等に割り当ててください。
- SRTのフォーマット (インデックス番号 / "HH:MM:SS,mmm --> HH:MM:SS,mmm" / 字幕本文 / 空行) を厳守してください。
- 字幕本文には余計なマークダウンや記号を含めず、純粋な読み上げテキストのみを出力してください。

### 読み上げ原稿
{script_text}
""".strip()


def request_srt(
    script_text: str,
    duration_sec: float,
    model_name: str,
    temperature: float,
    debug_enabled: bool,
    script_path: Path,
) -> Tuple[str, str]:
    prompt = build_prompt(script_text, duration_sec)
    write_debug_artifact(debug_enabled, script_path, ".prompt.txt", prompt)

    client = genai.Client(api_key=get_google_api_key())
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
        config=genai_types.GenerateContentConfig(temperature=temperature),
    )
    response_text = getattr(response, "text", "").strip()
    if not response_text:
        raise RuntimeError("Gemini returned an empty response for SRT generation")

    write_debug_artifact(debug_enabled, script_path, ".gemini_raw.txt", response_text)
    return response_text, prompt


def main() -> None:
    args = parse_args()
    script_path = Path(args.script)
    video_path = Path(args.video)

    if not script_path.exists():
        print(f"[ERROR] Script file not found: {script_path}")
        sys.exit(1)

    script_text = script_path.read_text(encoding="utf-8").strip()
    if not script_text:
        print("[ERROR] Script file is empty")
        sys.exit(1)

    duration_sec = get_video_duration(video_path)

    print(f"[MESSAGE]: Video duration detected: {duration_sec:.2f} seconds")
    raw_srt, prompt = request_srt(
        script_text,
        duration_sec,
        args.model,
        args.temperature,
        args.debug,
        script_path,
    )

    cleaned_srt = strip_code_fence(raw_srt)
    write_debug_artifact(args.debug, script_path, ".gemini_clean.txt", cleaned_srt)

    try:
        entries = parse_srt(cleaned_srt, duration_sec)
    except ValueError as exc:
        if args.debug:
            write_debug_artifact(
                True,
                script_path,
                ".gemini_parse_error.txt",
                f"Prompt:\n{prompt}\n\nRaw Response:\n{raw_srt}\n\nCleaned:\n{cleaned_srt}\n\nError: {exc}\n",
            )
        print(f"[ERROR] Gemini output could not be parsed as SRT: {exc}")
        sys.exit(1)

    srt_text = format_srt(entries)
    output_path = video_path.with_suffix(".srt")
    output_path.write_text(srt_text, encoding="utf-8")

    print(f"[MESSAGE]: SRT file generated → {output_path}")


if __name__ == "__main__":
    main()
