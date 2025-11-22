#!/usr/bin/env python3
"""
既存の選評Markdownファイルから音声ガイドを生成するスクリプト
Usage: python markdown_to_audio.py <markdown_file> <output_basename> [theme]
"""

import sys
import os
import yaml
from lib.tts import generate_radio_script, generate_speech

def main():
    if len(sys.argv) < 3:
        print("Usage: python markdown_to_audio.py <markdown_file> <output_basename> [theme]")
        print("Example: python markdown_to_audio.py selected_選評_Gemini.md output_audio 自由詠")
        sys.exit(1)
    
    markdown_file = sys.argv[1]
    output_basename = sys.argv[2]
    theme = sys.argv[3] if len(sys.argv) > 3 else None
    
    # Google API Keyの確認
    if 'GOOGLE_API_KEY' not in os.environ:
        print("Error: GOOGLE_API_KEY environment variable is required.")
        print("Set it with: export GOOGLE_API_KEY='your_api_key'")
        sys.exit(1)
    
    # TTS設定ファイルの読み込み
    try:
        with open('./config/tts_generation_config.yaml', 'r', encoding='utf-8') as f:
            tts_config = yaml.safe_load(f)
    except FileNotFoundError:
        print("Error: config/tts_generation_config.yaml not found")
        sys.exit(1)
    
    # Markdownファイルの読み込み
    try:
        with open(markdown_file, 'r', encoding='utf-8') as f:
            selection_markdown = f.read()
    except FileNotFoundError:
        print(f"Error: {markdown_file} not found")
        sys.exit(1)
    
    print(f"🎯 Converting {markdown_file} to audio...")
    
    try:
        # ラジオ原稿の生成
        print("📝 Generating radio script...")
        radio_script = generate_radio_script(
            selection_markdown=selection_markdown,
            template_path='./templates/generate_script_prompt.md',
            model_name=tts_config.get('script_generation', {}).get('model_name', 'gemini-2.5-pro-preview'),
            temperature=tts_config.get('script_generation', {}).get('temperature', 0.7),
            wait_sec=tts_config.get('script_generation', {}).get('wait_sec', 20),
            theme=theme
        )
        
        # ラジオ原稿の保存
        script_file = f"{output_basename}.radio_script.txt"
        with open(script_file, 'w', encoding='utf-8') as f:
            f.write(radio_script)
        print(f"✅ Radio script saved: {script_file}")
        
        # 音声の生成
        print("🎵 Generating audio...")
        audio_file = generate_speech(
            script_text=radio_script,
            output_basename=output_basename,
            model_name=tts_config.get('speech_generation', {}).get('model_name', 'gemini-2.5-pro-preview-tts'),
            wait_sec=tts_config.get('speech_generation', {}).get('wait_sec', 20)
        )
        
        print(f"✅ Audio generated: {audio_file}")
        print("🎉 Conversion completed!")
        
    except Exception as e:
        print(f"❌ Error during conversion: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
