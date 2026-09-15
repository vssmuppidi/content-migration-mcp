#!/usr/bin/env python3
"""
Validation script to check if the Content MCP Server is properly configured.
Run this before starting the server to ensure all API keys are set up correctly.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_env_var(name, required=True):
    """Check if an environment variable is set."""
    value = os.getenv(name)
    if value and value != f"your_{name.lower()}_here":
        print(f"✓ {name}: Configured")
        return True
    elif required:
        print(f"✗ {name}: NOT configured (required)")
        return False
    else:
        print(f"⚠ {name}: NOT configured (optional)")
        return True

def main():
    """Run validation checks."""
    print("=" * 60)
    print("Content MCP Server - Configuration Validation")
    print("=" * 60)
    print()
    
    all_good = True
    
    print("Checking Reddit API Configuration:")
    all_good &= check_env_var("REDDIT_CLIENT_ID")
    all_good &= check_env_var("REDDIT_CLIENT_SECRET")
    all_good &= check_env_var("REDDIT_USER_AGENT")
    print()
    
    print("Checking YouTube API Configuration:")
    all_good &= check_env_var("YOUTUBE_API_KEY")
    print()
    
    print("Checking Inference API Configuration:")
    print("(At least one is required - OpenRouter or Groq)")
    openrouter_ok = check_env_var("OPENROUTER_API_KEY", required=False)
    groq_ok = check_env_var("GROQ_API_KEY", required=False)
    
    if not openrouter_ok and not groq_ok:
        print("✗ ERROR: No inference API configured! Please set either OPENROUTER_API_KEY or GROQ_API_KEY")
        all_good = False
    else:
        print("✓ At least one inference API is configured")
    
    check_env_var("INFERENCE_PROVIDER", required=False)
    check_env_var("OPENROUTER_MODEL", required=False)
    check_env_var("GROQ_MODEL", required=False)
    print()
    
    print("Checking Optional Configuration:")
    check_env_var("SPEAKING_RATE_WPM", required=False)
    print()
    
    print("=" * 60)
    if all_good:
        print("✓ All required configurations are set!")
        print("You can now run: python -m src.server")
    else:
        print("✗ Some required configurations are missing.")
        print("Please check your .env file and ensure all required keys are set.")
        print("See SETUP.md or env.example for instructions.")
        sys.exit(1)
    print("=" * 60)

if __name__ == "__main__":
    main()

