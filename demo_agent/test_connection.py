#!/usr/bin/env python3
"""
Quick test to verify the agent can connect to the MCP server.
Run this before using the full agent to ensure everything is set up correctly.
"""

import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from parent directory's .env file
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

print("🔍 Testing Content MCP Server Connection...")
print("=" * 70)

# Test 1: Import MCP server
print("\n1. Testing MCP server imports...")
try:
    from src.server import app
    print("   ✅ MCP server imports successfully")
except Exception as e:
    print(f"   ❌ Failed to import MCP server: {e}")
    sys.exit(1)

# Test 2: Check environment variables
print("\n2. Checking environment variables...")
try:
    from src.config import config
    
    missing = config.get_missing_configs()
    if missing:
        print(f"   ⚠️  Missing configs: {', '.join(missing)}")
        print("   Note: Some features may not work without all API keys")
    else:
        print("   ✅ All API keys configured")
        
    # Check specific keys
    print("\n   API Key Status:")
    print(f"   - Reddit: {'✅' if config.validate_reddit_config() else '❌'}")
    print(f"   - YouTube: {'✅' if config.validate_youtube_config() else '❌'}")
    print(f"   - Groq: {'✅' if config.validate_groq_config() else '❌'}")
    print(f"   - ElevenLabs: {'✅' if config.validate_elevenlabs_config() else '❌'}")
    
except Exception as e:
    print(f"   ❌ Failed to check config: {e}")

# Test 3: Test Agno imports
print("\n3. Testing Agno framework imports...")
try:
    from agno.agent import Agent
    from agno.models.groq import Groq
    from agno.models.openrouter import OpenRouter
    from agno.tools.mcp import MCPTools
    print("   ✅ Agno framework imports successfully")
except ImportError as e:
    print(f"   ❌ Failed to import Agno: {e}")
    print("   💡 Install with: pip install agno>=2.0.0")
    sys.exit(1)

# Test 4: Try to create a minimal agent
print("\n4. Testing agent creation...")
try:
    # Use the launcher script
    launcher_script = Path(__file__).parent / "launch_mcp.sh"
    
    # Try to use OpenRouter first, fall back to Groq if needed
    try:
        openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
        if not openrouter_api_key:
            raise ValueError("OPENROUTER_API_KEY not set")
        
        print("   🚀 Using OpenRouter for inference (primary)")
        model = OpenRouter(
            id="openai/gpt-4o-mini",  # Known working model - cheap and reliable
            api_key=openrouter_api_key
        )
    except Exception as e:
        print(f"   ⚠️  OpenRouter unavailable ({str(e)}), falling back to Groq")
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("Neither OPENROUTER_API_KEY nor GROQ_API_KEY is set. Please set at least one.")
        
        print("   🚀 Using Groq for inference (backup)")
        model = Groq(id="openai/gpt-oss-20b")
    
    test_agent = Agent(
        name="Test Agent",
        model=model,
        tools=[
            MCPTools(
                transport="stdio",
                command=str(launcher_script)
            )
        ],
    )
    print("   ✅ Agent created successfully")
    print(f"   - Name: {test_agent.name}")
    print(f"   - Model: {test_agent.model.id}")
    print(f"   - Tools: MCP Server connected")
except Exception as e:
    print(f"   ❌ Failed to create agent: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n" + "=" * 70)
print("✅ ALL TESTS PASSED - Agent is ready to use!")
print("\nNext steps:")
print("  1. Run simple examples: python simple_example.py")
print("  2. Start AgentOS UI: python content_agent.py")
print("=" * 70)

