"""Test the video generation tool through the MCP server."""

import asyncio
import json
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_video_tool():
    """Test the generate_video_from_video tool through MCP server."""
    
    # Server parameters - starts the MCP server
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src"],
        env=None
    )
    
    print("🚀 Starting MCP server...")
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            print("✓ MCP server connected\n")
            
            # List available tools
            tools_list = await session.list_tools()
            print(f"📦 Available tools: {len(tools_list.tools)}")
            
            # Find our video tool
            video_tool = None
            for tool in tools_list.tools:
                if tool.name == "generate_video_from_video":
                    video_tool = tool
                    print(f"✓ Found tool: {tool.name}")
                    break
            
            if not video_tool:
                print("✗ Tool 'generate_video_from_video' not found!")
                return
            
            print(f"\nTool description: {video_tool.description}\n")
            
            # Prepare the tool call arguments
            arguments = {
                "video_path": "test_content/test.mp4",
                "audio_path": "test_content/generated_audio_57679.mp3",
                "frame_timestamp": 2.0
            }
            
            print("🎬 Calling tool with arguments:")
            print(json.dumps(arguments, indent=2))
            print("\n⏳ Generating video... (this may take 30-60 seconds)\n")
            
            # Call the tool
            result = await session.call_tool("generate_video_from_video", arguments)
            
            # Parse the result
            if result.content:
                result_text = result.content[0].text
                result_data = json.loads(result_text)
                
                print("="*60)
                if result_data.get("success"):
                    print("✓ VIDEO GENERATION SUCCESSFUL!")
                    print("="*60)
                    print(f"\n📹 Video saved to: {result_data['video_path']}")
                    print(f"🖼️  Frame extracted: {result_data['frame_path']}")
                    print(f"🎵 Audio used: {result_data['audio_path']}")
                    print(f"\nMetadata:")
                    print(json.dumps(result_data.get('metadata', {}), indent=2))
                else:
                    print("✗ VIDEO GENERATION FAILED")
                    print("="*60)
                    print(f"\nError: {result_data.get('error')}")
            else:
                print("✗ No response from tool")


async def main():
    """Main function."""
    print("\n" + "="*60)
    print("MCP VIDEO GENERATION TOOL TEST")
    print("="*60 + "\n")
    
    try:
        await test_video_tool()
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
    except Exception as e:
        print(f"\n✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "="*60)
    print("Test complete")
    print("="*60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())

