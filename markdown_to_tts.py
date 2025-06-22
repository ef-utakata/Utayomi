#!/usr/bin/env python3
"""
Standalone script to generate TTS audio from existing radio script files.
Useful for re-generating audio after manual editing of radio scripts for pronunciation corrections.

Usage:
    python markdown_to_tts.py input.radio_script.txt output_dir [--config tts_config.yaml]
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
        description="Generate TTS audio from existing radio script files"
    )
    parser.add_argument('input_script', help='Input radio script file path (e.g., *.radio_script.txt)')
    parser.add_argument('output_dir', help='Output directory for TTS files')
    parser.add_argument('--config', default='./tts_generation_config.yaml', 
                        help='TTS configuration file (default: ./tts_generation_config.yaml)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not os.path.exists(args.input_script):
        print(f"[ERROR]: Input file not found: {args.input_script}")
        sys.exit(1)
    
    if not os.path.exists(args.config):
        print(f"[ERROR]: Config file not found: {args.config}")
        sys.exit(1)
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Load configurations
    config = load_tts_config(args.config)
    speech_config = config['speech_generation']
    
    # Read input radio script
    with open(args.input_script, 'r', encoding='utf-8') as f:
        script_text = f.read()
    
    # Generate base filename from input (remove .radio_script.txt extension)
    input_basename = Path(args.input_script).stem
    if input_basename.endswith('.radio_script'):
        input_basename = input_basename[:-13]  # Remove '.radio_script' suffix
    
    print(f"[MESSAGE]: Processing {args.input_script}")
    print(f"[MESSAGE]: Output directory: {args.output_dir}")
    
    try:
        # Generate speech directly from the input script
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
        print(f"[MESSAGE]: Input script: {args.input_script}")
        
    except Exception as e:
        print(f"[ERROR]: TTS generation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()