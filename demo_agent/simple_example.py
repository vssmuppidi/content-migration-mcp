"""
Simple example of using the Content Creation Agent without AgentOS UI.
Run this for quick tests and experiments.
"""

import sys
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Load environment variables from parent directory's .env file
env_path = PROJECT_ROOT / ".env"
load_dotenv(env_path)

from agno.agent import Agent
from agno.models.groq import Groq
from agno.models.openrouter import OpenRouter
from agno.tools.mcp import MCPTools


async def create_agent():
    """Create a content creation agent with properly connected MCP tools."""
    # Use the launcher script
    launcher_script = Path(__file__).parent / "launch_mcp.sh"
    
    # Initialize MCP tools with increased timeout for long-running operations
    mcp_tools = MCPTools(
        transport="stdio",
        command=str(launcher_script),
        timeout_seconds=600  # 5 minutes for complete video generation (fetching, AI processing, voice cloning, video generation, etc.)
    )
    
    # Connect to MCP server (this is critical!)
    print("🔌 Connecting to MCP server...")
    await mcp_tools.connect()
    print("✅ MCP server connected!")
    
    # Print available tools for debugging
    if hasattr(mcp_tools, 'functions'):
        funcs = list(mcp_tools.functions) if hasattr(mcp_tools.functions, '__iter__') else []
        print(f"📦 Available MCP tools: {len(funcs)} tools loaded")
        if funcs:
            func_names = [f.replace('_', '', 1) for f in funcs[:5]]
            print(f"   Tools: {', '.join(func_names)}...")
    
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
    
    agent = Agent(
        name="Content Creator",
        model=model,
        tools=[mcp_tools],
        markdown=True,
        description="Content creation assistant with trending topic research and voice generation",
        instructions=[
            "YOU ARE STRICTLY FORBIDDEN FROM GENERATING SCRIPTS YOURSELF. You MUST use the MCP tools for ALL content generation.",
            "CRITICAL: When asked to generate ANY script, you MUST call generate_complete_script or generate_script tool. DO NOT write scripts yourself.",
            "CRITICAL: When asked about trending topics, you MUST call generate_ideas, generate_reddit_ideas, generate_youtube_ideas, or generate_news_ideas tool.",
            "CRITICAL: When asked about voices, you MUST call list_all_voices tool.",
            "After calling a tool, present the tool's output to the user. DO NOT modify, rewrite, or improve the tool's output.",
            "Always show which tool you're calling and why.",
            "The MCP tools contain specialized logic for emotional tags, context gathering, and voice cloning - you cannot replicate this.",
            "If a user asks for a script, your ONLY job is to call the appropriate tool with the right parameters and show the result."
        ]
    )
    
    return agent, mcp_tools


async def example_1_trending_topics():
    """Example: Get trending topics on a subject."""
    print("\n" + "="*70)
    print("EXAMPLE 1: Research Trending Topics")
    print("="*70 + "\n")
    
    agent, mcp_tools = await create_agent()
    try:
        response = await agent.arun(
            "What are the top 3 trending topics about artificial intelligence on Reddit?"
        )
        print(response.content)
    finally:
        await mcp_tools.close()


async def example_2_generate_script():
    """Example: Generate a script about a topic."""
    print("\n" + "="*70)
    print("EXAMPLE 2: Generate a Script")
    print("="*70 + "\n")
    
    agent, mcp_tools = await create_agent()
    try:
        response = await agent.arun(
            "Create a 30-second script about the latest trends in artificial intelligence. "
            "Research trending topics first, then write an engaging script."
        )
        print(response.content)
    finally:
        await mcp_tools.close()


async def example_3_list_voices():
    """Example: List available voices."""
    print("\n" + "="*70)
    print("EXAMPLE 3: List Available Voices")
    print("="*70 + "\n")
    
    agent, mcp_tools = await create_agent()
    try:
        response = await agent.arun(
            "List all the voices available in my ElevenLabs account."
        )
        print(response.content)
    finally:
        await mcp_tools.close()


async def example_4_complete_workflow():
    """Example: Complete content creation workflow."""
    print("\n" + "="*70)
    print("EXAMPLE 4: Complete Content Creation Workflow")
    print("="*70 + "\n")
    
    agent, mcp_tools = await create_agent()
    try:
        response = await agent.arun(
            "Create a complete content piece about 'AI trends': "
            "1. Research trending topics "
            "2. Generate a 20-second script "
            "3. List available voices so I can choose one"
        )
        print(response.content)
    finally:
        await mcp_tools.close()


async def interactive_mode():
    """Interactive chat mode with the agent."""
    print("\n" + "="*70)
    print("INTERACTIVE MODE - Content Creation Agent")
    print("="*70)
    print("\nCommands:")
    print("  • Type your request and press Enter")
    print("  • Type 'quit' or 'exit' to end")
    print("  • Type 'clear' to start a new conversation")
    print("\nExamples:")
    print("  - 'Research trending AI topics'")
    print("  - 'Generate a 30-second script about machine learning'")
    print("  - 'List my available voices'")
    print("  - 'Create content about climate change with uploaded video'")
    print("  - 'Clone voice from uploaded video and save as JD'")
    print("="*70)
    print("\n📹 Video Context: When you mention 'uploaded video', it refers to test_content/JD.mp4\n")
    print("="*70 + "\n")
    
    agent, mcp_tools = await create_agent()
    
    # Default video path for voice cloning
    default_video_path = str(PROJECT_ROOT / "test_content" / "JD.mp4")
    
    try:
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit']:
                    print("\n👋 Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    await mcp_tools.close()
                    agent, mcp_tools = await create_agent()  # Create fresh agent
                    print("\n🔄 Conversation cleared. Starting fresh!\n")
                    continue
                
                # Add system context if user mentions "uploaded video"
                enriched_prompt = user_input
                if "uploaded video" in user_input.lower():
                    enriched_prompt = f"""SYSTEM CONTEXT: The uploaded video is located at: {default_video_path}

User request: {user_input}

Instructions: Replace any mention of "uploaded video" or "the video" with the actual path: {default_video_path}"""
                
                print("\n🤖 Agent: ", end="", flush=True)
                response = await agent.arun(enriched_prompt)
                
                # Check if response is empty
                if hasattr(response, 'content'):
                    content = str(response.content).strip()
                    if not content:
                        print("(empty response - possible API issue or model not responding)\n")
                    else:
                        print(content + "\n")
                else:
                    print(str(response) + "\n")
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
    finally:
        await mcp_tools.close()


async def main():
    """Main menu for examples."""
    print("\n" + "="*70)
    print("CONTENT CREATION AGENT - EXAMPLES")
    print("="*70)
    print("\nChoose an example to run:")
    print("  1. Get trending topics about AI")
    print("  2. Generate a script")
    print("  3. List available voices")
    print("  4. Complete content creation workflow")
    print("  5. Interactive mode (chat with agent)")
    print("  0. Exit")
    print("="*70)
    
    while True:
        try:
            choice = input("\nEnter choice (0-5): ").strip()
            
            if choice == '0':
                print("\n👋 Goodbye!")
                break
            elif choice == '1':
                await example_1_trending_topics()
            elif choice == '2':
                await example_2_generate_script()
            elif choice == '3':
                await example_3_list_voices()
            elif choice == '4':
                await example_4_complete_workflow()
            elif choice == '5':
                await interactive_mode()
            else:
                print("❌ Invalid choice. Please enter 0-5.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())

