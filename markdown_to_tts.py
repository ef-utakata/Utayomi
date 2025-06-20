#!/usr/bin/env python3
"""
Standalone script to generate TTS audio from existing Markdown files.
Useful for re-generating audio after manual editing of selection results.

Usage:
    python markdown_to_tts.py input.md output_dir [--config tts_config.yaml]
"""

import argparse
import os
import sys
import yaml
from pathlib import Path

# Import TTS functions
from lib.tts import generate_radio_script, generate_speech

def load_tts_config(config_path):
    """Load TTS configuration from YAML file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def main():
    parser = argparse.ArgumentParser(
        description="Generate TTS audio from existing Markdown selection files"
    )
    parser.add_argument('input_md', help='Input Markdown file path')
    parser.add_argument('output_dir', help='Output directory for TTS files')
    parser.add_argument('--config', default='./tts_generation_config.yaml', 
                        help='TTS configuration file (default: ./tts_generation_config.yaml)')
    parser.add_argument('--theme', help='Theme for radio script generation')
    parser.add_argument('--application', help='Application/project name for radio script generation')
    parser.add_argument('--template', default='./generate_script_prompt.md',
                        help='Script generation template (default: ./generate_script_prompt.md)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.input_md):
        print(f"[ERROR]: Input file not found: {args.input_md}")
        sys.exit(1)
    
    if not os.path.exists(args.config):
        print(f"[ERROR]: Config file not found: {args.config}")
        sys.exit(1)
        
    if not os.path.exists(args.template):
        print(f"[ERROR]: Template file not found: {args.template}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load configurations
    config = load_tts_config(args.config)
    script_config = config['script_generation']
    speech_config = config['speech_generation']
    
    # Read input markdown
    with open(args.input_md, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    
    # Generate base filename from input
    input_basename = Path(args.input_md).stem
    
    print(f"[MESSAGE]: Processing {args.input_md}")
    print(f"[MESSAGE]: Output directory: {args.output_dir}")
    
    try:
        # Step 1: Generate radio script
        print(f"[MESSAGE]: Generating radio script...")
        script_text = generate_radio_script(
            selection_markdown=markdown_content,
            template_path=args.template,
            model_name=script_config['model_name'],
            temperature=script_config['temperature'],
            wait_sec=script_config['wait_sec'],
            theme=args.theme,
            application=args.application
        )
        
        # Save radio script
        script_path = os.path.join(args.output_dir, f"{input_basename}.radio_script.txt")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_text)
        print(f"[MESSAGE]: Radio script saved: {script_path}")
        
        # Step 2: Generate speech
        print(f"[MESSAGE]: Generating speech audio...")
        
        # Build voice configurations
        from google.genai import types
        speaker_voice_configs = []
        for voice in speech_config['voices']:
            speaker_voice_configs.append(
                types.SpeakerVoiceConfig(
                    speaker=voice['speaker'],
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(
                            voice_name=voice['voice_name']
                        )
                    ),
                )
            )
        
        # Generate audio
        audio_path = generate_speech(
            script_text=script_text,
            output_basename=os.path.join(args.output_dir, input_basename),
            speaker_voice_configs=speaker_voice_configs,
            wait_sec=speech_config['wait_sec']
        )
        
        print(f"[SUCCESS]: TTS generation completed!")
        print(f"[MESSAGE]: Audio file: {audio_path}")
        print(f"[MESSAGE]: Script file: {script_path}")
        
    except Exception as e:
        print(f"[ERROR]: TTS generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()