#!/usr/bin/env python3
"""
Environment variable loader for Utayomi
Loads API keys from .env file if available, falls back to system environment variables
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False

def load_env_vars():
    """
    Load environment variables from .env file if it exists.
    Falls back to system environment variables if .env is not available.
    """
    if DOTENV_AVAILABLE:
        # Look for .env file in the project root
        env_path = Path(__file__).parent.parent / '.env'
        if env_path.exists():
            load_dotenv(env_path)
            print(f"✅ Loaded environment variables from {env_path}")
        else:
            print(f"ℹ️  .env file not found at {env_path}, using system environment variables")
    else:
        print("ℹ️  python-dotenv not installed, using system environment variables only")

def get_api_key(key_name, required=True):
    """
    Get API key from environment variables.
    
    Args:
        key_name (str): Name of the environment variable
        required (bool): Whether the key is required (raises error if missing)
    
    Returns:
        str: API key value or None if not found and not required
    
    Raises:
        ValueError: If required key is not found
    """
    value = os.getenv(key_name)
    if required and not value:
        raise ValueError(f"Required environment variable {key_name} is not set. "
                        f"Please set it in your .env file or system environment.")
    return value

def get_google_api_key():
    """Get Google Gemini API key"""
    return get_api_key('GOOGLE_API_KEY', required=True)

def get_google_api_key_paid():
    """
    Get Google Gemini API key with paid features (TTS/Pro).
    
    Returns:
        str: API key for paid features
    
    Note:
        - First tries GOOGLE_API_KEY_PAID (recommended for TTS/Pro features)
        - Falls back to GOOGLE_API_KEY if paid key is not available
        - Some features like TTS require a paid billing account
    """
    # Try paid key first, fall back to regular key
    paid_key = get_api_key('GOOGLE_API_KEY_PAID', required=False)
    if paid_key:
        return paid_key
    return get_api_key('GOOGLE_API_KEY', required=True)

def has_paid_api_key():
    """
    Check if paid API key is available.
    
    Returns:
        bool: True if GOOGLE_API_KEY_PAID is set, False otherwise
    """
    return get_api_key('GOOGLE_API_KEY_PAID', required=False) is not None

def test_tts_api_key():
    """
    Test if the current API key supports TTS functionality.
    
    Returns:
        bool: True if TTS is supported, False otherwise
    """
    try:
        import google.generativeai as genai
        api_key = get_google_api_key_paid()
        genai.configure(api_key=api_key)
        
        # Simple test: try to create a TTS model instance
        model = genai.GenerativeModel('gemini-2.5-pro-preview-tts')
        return True
        
    except Exception as e:
        error_msg = str(e)
        # Check for quota/billing errors
        if any(keyword in error_msg.lower() for keyword in ['quota', 'billing', '429', 'payment', 'invalid']):
            return False
        return False

def get_openai_api_key():
    """Get OpenAI API key"""
    return get_api_key('OPENAI_API_KEY', required=True)

def get_cohere_api_key():
    """Get Cohere API key"""
    return get_api_key('COHERE_API_KEY', required=True)

# Initialize environment variables on module import
load_env_vars()