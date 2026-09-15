"""
Interactive test script for MCP server.
Connects to the server and allows you to send queries and see how it analyzes context and calls functions.
"""

import asyncio
import json
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_query_analysis(session: ClientSession, query: str):
    """Test query analysis tool."""
    print(f"\n{'='*70}")
    print(f"ANALYZING QUERY: {query}")
    print(f"{'='*70}")
    
    try:
        result = await session.call_tool(
            "analyze_query",
            arguments={"query": query}
        )
        analysis = json.loads(result.content[0].text)
        print(f"\n✓ Query Analysis Result:")
        print(f"  Intent: {analysis.get('intent')}")
        print(f"  Topics: {analysis.get('topics')}")
        print(f"  Context Sources: {analysis.get('context_sources')}")
        print(f"  Requirements: {analysis.get('requirements')}")
        print(f"  Confidence: {analysis.get('confidence')}")
        return analysis
    except Exception as e:
        print(f"✗ Error analyzing query: {str(e)}")
        return None


async def test_prompt(session: ClientSession, prompt_name: str, arguments: dict):
    """Test getting a prompt with automatic context injection."""
    print(f"\n{'='*70}")
    print(f"GETTING PROMPT: {prompt_name}")
    print(f"Arguments: {arguments}")
    print(f"{'='*70}")
    
    try:
        # MCP protocol requires all prompt arguments to be strings
        string_arguments = {k: str(v) if v is not None else "" for k, v in arguments.items()}
        result = await session.get_prompt(prompt_name, arguments=string_arguments)
        print(f"\n✓ Prompt Retrieved:")
        print(f"  Prompt: {prompt_name}")
        print(f"  Description: {result.description}")
        if result.messages:
            for i, msg in enumerate(result.messages):
                print(f"\n  Message {i+1}:")
                if hasattr(msg, 'role'):
                    print(f"    Role: {msg.role}")
                if hasattr(msg, 'content'):
                    content = msg.content
                    if hasattr(content, 'text'):
                        text = content.text
                        # Show first 500 chars
                        if len(text) > 500:
                            print(f"    Content (first 500 chars):\n{text[:500]}...")
                        else:
                            print(f"    Content:\n{text}")
    except Exception as e:
        print(f"✗ Error getting prompt: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_resource(session: ClientSession, uri: str):
    """Test reading a resource."""
    print(f"\n{'='*70}")
    print(f"READING RESOURCE: {uri}")
    print(f"{'='*70}")
    
    try:
        result = await session.read_resource(uri)
        print(f"\n✓ Resource Retrieved:")
        if hasattr(result, 'text'):
            text = result.text
            # Show first 500 chars
            if len(text) > 500:
                print(f"  Content (first 500 chars):\n{text[:500]}...")
            else:
                print(f"  Content:\n{text}")
        elif hasattr(result, 'contents'):
            print(f"  Contents: {result.contents}")
    except Exception as e:
        print(f"✗ Error reading resource: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_tool_call(session: ClientSession, tool_name: str, arguments: dict):
    """Test calling a tool."""
    print(f"\n{'='*70}")
    print(f"CALLING TOOL: {tool_name}")
    print(f"Arguments: {json.dumps(arguments, indent=2)}")
    print(f"{'='*70}")
    
    try:
        result = await session.call_tool(tool_name, arguments=arguments)
        print(f"\n✓ Tool Call Result:")
        if result.content:
            for i, content in enumerate(result.content):
                if hasattr(content, 'text'):
                    text = content.text
                    # Try to parse as JSON for pretty printing
                    try:
                        data = json.loads(text)
                        print(f"  Result {i+1} (JSON):\n{json.dumps(data, indent=2)[:1000]}...")
                    except:
                        # Not JSON, print as text
                        if len(text) > 1000:
                            print(f"  Result {i+1} (first 1000 chars):\n{text[:1000]}...")
                        else:
                            print(f"  Result {i+1}:\n{text}")
    except Exception as e:
        print(f"✗ Error calling tool: {str(e)}")
        import traceback
        traceback.print_exc()


async def list_available_tools(session: ClientSession):
    """List all available tools."""
    print(f"\n{'='*70}")
    print("AVAILABLE TOOLS")
    print(f"{'='*70}")
    
    try:
        tools = await session.list_tools()
        print(f"\n✓ Found {len(tools.tools)} tools:")
        for tool in tools.tools:
            print(f"  • {tool.name}: {tool.description[:100]}...")
    except Exception as e:
        print(f"✗ Error listing tools: {str(e)}")


async def list_available_prompts(session: ClientSession):
    """List all available prompts."""
    print(f"\n{'='*70}")
    print("AVAILABLE PROMPTS")
    print(f"{'='*70}")
    
    try:
        prompts = await session.list_prompts()
        print(f"\n✓ Found {len(prompts.prompts)} prompts:")
        for prompt in prompts.prompts:
            print(f"  • {prompt.name}: {prompt.description[:100]}...")
    except Exception as e:
        print(f"✗ Error listing prompts: {str(e)}")


async def list_available_resources(session: ClientSession):
    """List all available resources."""
    print(f"\n{'='*70}")
    print("AVAILABLE RESOURCES")
    print(f"{'='*70}")
    
    try:
        resources = await session.list_resources()
        print(f"\n✓ Found {len(resources.resources)} resources:")
        for resource in resources.resources:
            print(f"  • {resource.uri}: {resource.name}")
    except Exception as e:
        print(f"✗ Error listing resources: {str(e)}")


async def interactive_session():
    """Run an interactive session with the MCP server."""
    print("\n" + "="*70)
    print("MCP SERVER INTERACTIVE TEST")
    print("="*70)
    print("\nThis script connects to the MCP server and allows you to:")
    print("  1. Analyze queries to see intent and context needs")
    print("  2. Test prompts with automatic context injection")
    print("  3. Read resources")
    print("  4. Call tools directly")
    print("  5. Test complete workflows")
    print("\n" + "="*70)
    
    # Server parameters
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server"],
        env=None
    )
    
    # Connect to server
    print("\n🔌 Connecting to MCP server...")
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize session
            await session.initialize()
            
            print("✅ Connected to MCP server!")
            
            # List available tools, prompts, and resources
            await list_available_tools(session)
            await list_available_prompts(session)
            await list_available_resources(session)
            
            # Interactive loop
            print("\n" + "="*70)
            print("INTERACTIVE MODE")
            print("="*70)
            print("\nCommands:")
            print("  analyze <query>          - Analyze a query")
            print("  prompt <name> <args>     - Get a prompt (args as JSON)")
            print("  resource <uri>           - Read a resource")
            print("  tool <name> <args>       - Call a tool (args as JSON)")
            print("  workflow <query>         - Test complete workflow (prompts)")
            print("  complete-script <topic>  - Complete workflow: Ideas → Script")
            print("  complete-audio <topic>   - Complete workflow: Ideas → Script → Audio")
            print("  complete-video <topic>   - Complete workflow: Ideas → Script → Audio → Video")
            print("  list-tools               - List all tools")
            print("  list-prompts             - List all prompts")
            print("  list-resources           - List all resources")
            print("  exit                     - Exit")
            print("\nExamples:")
            print('  analyze "Generate a 30 sec script about Pluribus Reactions"')
            print('  prompt script_generation {\"topic\": \"AI\", \"duration_seconds\": \"30\"}')
            print('  tool generate_ideas {\"topic\": \"AI\", \"limit\": 5}')
            print('  complete-video "Pluribus Reactions"  # Does EVERYTHING in one call!')
            print('  workflow "Generate a 30 sec script about Pluribus Reactions"')
            print("\n" + "="*70)
            
            while True:
                try:
                    user_input = input("\n> ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.lower() == "exit":
                        print("👋 Goodbye!")
                        break
                    
                    parts = user_input.split(" ", 1)
                    command = parts[0].lower()
                    
                    if command == "analyze" and len(parts) > 1:
                        query = parts[1]
                        await test_query_analysis(session, query)
                    
                    elif command == "prompt" and len(parts) > 1:
                        prompt_parts = parts[1].split(" ", 1)
                        prompt_name = prompt_parts[0]
                        if len(prompt_parts) > 1:
                            try:
                                arguments = json.loads(prompt_parts[1])
                            except:
                                print("✗ Invalid JSON arguments")
                                continue
                        else:
                            arguments = {}
                        await test_prompt(session, prompt_name, arguments)
                    
                    elif command == "resource" and len(parts) > 1:
                        uri = parts[1]
                        await test_resource(session, uri)
                    
                    elif command == "tool" and len(parts) > 1:
                        tool_parts = parts[1].split(" ", 1)
                        tool_name = tool_parts[0]
                        if len(tool_parts) > 1:
                            try:
                                arguments = json.loads(tool_parts[1])
                            except:
                                print("✗ Invalid JSON arguments")
                                continue
                        else:
                            arguments = {}
                        await test_tool_call(session, tool_name, arguments)
                    
                    elif command == "workflow" and len(parts) > 1:
                        query = parts[1]
                        print(f"\n🧪 Testing complete workflow for: {query}")
                        
                        # Step 1: Analyze query
                        analysis = await test_query_analysis(session, query)
                        if not analysis:
                            continue
                        
                        # Step 2: Based on analysis, test appropriate prompt or tool
                        intent = analysis.get("intent")
                        topics = analysis.get("topics", [])
                        
                        if intent == "trending_topics" and topics:
                            topic = topics[0]
                            print(f"\n📊 Testing trending_analysis prompt for topic: {topic}")
                            await test_prompt(session, "trending_analysis", {"topic": topic})
                        
                        elif intent == "script_generation" and topics:
                            # Combine topics if multiple (e.g., "Pluribus Reactions")
                            topic = " ".join(topics[:2]) if len(topics) > 1 else topics[0]
                            duration = analysis.get("requirements", {}).get("duration", 30)
                            if duration is None:
                                duration = 30
                            print(f"\n📝 Testing script_generation prompt for topic: {topic}, duration: {duration}s")
                            await test_prompt(session, "script_generation", {
                                "topic": topic,
                                "duration_seconds": duration
                            })
                    
                    elif command == "list-tools":
                        await list_available_tools(session)
                    
                    elif command == "list-prompts":
                        await list_available_prompts(session)
                    
                    elif command == "list-resources":
                        await list_available_resources(session)
                    
                    elif command == "complete-script" and len(parts) > 1:
                        topic = parts[1]
                        print(f"\n🎬 Complete Workflow: Ideas → Script")
                        await test_tool_call(session, "generate_complete_script", {
                            "topic": topic,
                            "duration_seconds": 30
                        })
                    
                    elif command == "complete-audio" and len(parts) > 1:
                        topic = parts[1]
                        print(f"\n🎬 Complete Workflow: Ideas → Script → Audio")
                        print("📝 Note: Using test_content/test.mp4 for voice cloning")
                        await test_tool_call(session, "generate_complete_content", {
                            "topic": topic,
                            "duration_seconds": 30,
                            "video_path": "test_content/test.mp4",
                            "voice_name": "test_woman"
                        })
                    
                    elif command == "complete-video" and len(parts) > 1:
                        topic = parts[1]
                        print(f"\n🎬 Complete Workflow: Ideas → Script → Audio → Video")
                        print("📝 Note: Using test_content/test.mp4 for voice and face")
                        await test_tool_call(session, "generate_complete_video", {
                            "topic": topic,
                            "duration_seconds": 30,
                            "video_path": "test_content/test.mp4",
                            "voice_name": "test_woman"
                        })
                    
                    else:
                        print("✗ Unknown command. Type 'exit' to quit.")
                
                except KeyboardInterrupt:
                    print("\n\n👋 Interrupted. Goodbye!")
                    break
                except Exception as e:
                    print(f"\n✗ Error: {str(e)}")
                    import traceback
                    traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(interactive_session())

