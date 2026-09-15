"""Configuration management for Content MCP Server."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for managing API keys and settings."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Reddit API Configuration
        self.reddit_client_id = os.getenv("REDDIT_CLIENT_ID")
        self.reddit_client_secret = os.getenv("REDDIT_CLIENT_SECRET")
        self.reddit_user_agent = os.getenv("REDDIT_USER_AGENT", "ContentMCP/0.1.0")
        
        # YouTube API Configuration
        self.youtube_api_key = os.getenv("YOUTUBE_API_KEY")
        
        # OpenRouter API Configuration
        self.openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        self.openrouter_model = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
        
        # Groq API Configuration (backup/alternative)
        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        # Inference Provider Selection
        self.inference_provider = os.getenv("INFERENCE_PROVIDER", "openrouter").lower()
        
        # ElevenLabs API Configuration (for voice generation)
        self.elevenlabs_api_key = os.getenv("ELEVENLABS_API_KEY")
        
        # D-ID API Configuration (for video generation)
        self.did_api_key = os.getenv("DID_API_KEY")
        
        # Script Generation Settings
        self.speaking_rate_wpm = int(os.getenv("SPEAKING_RATE_WPM", "150"))
        
    def validate_reddit_config(self) -> bool:
        """Check if Reddit API configuration is valid."""
        return bool(self.reddit_client_id and self.reddit_client_secret)
    
    def validate_youtube_config(self) -> bool:
        """Check if YouTube API configuration is valid."""
        return bool(self.youtube_api_key)
    
    def validate_openrouter_config(self) -> bool:
        """Check if OpenRouter API configuration is valid."""
        return bool(self.openrouter_api_key)
    
    def validate_groq_config(self) -> bool:
        """Check if Groq API configuration is valid."""
        return bool(self.groq_api_key)
    
    def validate_elevenlabs_config(self) -> bool:
        """Check if ElevenLabs API configuration is valid."""
        return bool(self.elevenlabs_api_key)
    
    def validate_did_config(self) -> bool:
        """Check if D-ID API configuration is valid."""
        return bool(self.did_api_key)
    
    def has_inference_api(self) -> bool:
        """Check if at least one inference API is configured."""
        return self.validate_openrouter_config()
    
    def get_missing_configs(self) -> list[str]:
        """Return a list of missing configuration items."""
        missing = []
        if not self.validate_reddit_config():
            missing.append("Reddit API (REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET)")
        if not self.validate_youtube_config():
            missing.append("YouTube API (YOUTUBE_API_KEY)")
        if not self.has_inference_api():
            missing.append("Inference API (OPENROUTER_API_KEY)")
        # ElevenLabs is optional - only needed for voice generation
        return missing


# Global configuration instance
config = Config()

