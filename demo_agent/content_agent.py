"""
Content Creation Agent using Agno Framework
Connects to the Content MCP Server for content creation capabilities.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.groq import Groq
from agno.models.openrouter import OpenRouter
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# Load environment variables from parent directory's .env file
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

# Get the launcher script path
LAUNCHER_SCRIPT = Path(__file__).parent / "launch_mcp.sh"

# ************* Select Model with Fallback *************
# Try to use OpenRouter first, fall back to Groq if needed
try:
    openrouter_api_key = os.getenv("OPENROUTER_API_KEY")
    if not openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY not set")
    
    print("🚀 Using OpenRouter for inference (primary)")
    model = OpenRouter(
        id="openai/gpt-4o-mini",  # Known working model - cheap and reliable
        api_key=openrouter_api_key
    )
except Exception as e:
    print(f"⚠️  OpenRouter unavailable ({str(e)}), falling back to Groq")
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        raise ValueError("Neither OPENROUTER_API_KEY nor GROQ_API_KEY is set. Please set at least one.")
    
    print("🚀 Using Groq for inference (backup)")
    model = Groq(id="openai/gpt-oss-20b")

# ************* Create Content Creation Agent *************
content_agent = Agent(
    name="Content Creator",
    model=model,
    db=SqliteDb(db_file="content_agent.db"),
    tools=[
        MCPTools(
            transport="stdio",
            command=str(LAUNCHER_SCRIPT)
        )
    ],
    add_history_to_context=True,
    markdown=True,
    description=(
        "You are a content creation assistant that helps users create engaging content. "
        "You can research trending topics, generate scripts, and create audio narrations. "
        "Always be helpful and creative in assisting with content creation tasks."
    ),
    instructions=[
        "ALWAYS use the available MCP tools to answer questions - never make up information",
        "When asked about voices, use the list_all_voices tool to get actual voices from ElevenLabs",
        "When asked about trending topics, use generate_ideas or source-specific tools",
        "When asked to create content, first gather trending topics using generate_ideas",
        "Generate scripts that are engaging and well-structured using the generate_script tools",
        "For voice generation, list available voices first if the user hasn't specified one",
        "Always provide clear summaries of what you've created",
        "Show the user what tools you're using and what data you're getting from them"
    ]
)

# ************* Create AgentOS *************
agent_os = AgentOS(agents=[content_agent])
app = agent_os.get_app()

# ************* Run AgentOS *************
if __name__ == "__main__":
    print("🚀 Starting Content Creation Agent with AgentOS...")
    print("📡 Connecting to Content MCP Server...")
    print("🌐 AgentOS UI will be available at: http://localhost:7777")
    print("\nAgent Capabilities:")
    print("  • Generate content ideas from Reddit, YouTube, Google News")
    print("  • Create engaging scripts with AI")
    print("  • Generate audio with voice cloning")
    print("  • List and reuse existing voices")
    print("\n" + "="*60)
    
    agent_os.serve(app="content_agent:app", reload=True, host="0.0.0.0", port=7777)

