#!/usr/bin/env python3
"""Test the complete workflow with a single MCP tool call."""
import asyncio
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def test_complete_workflow():
    """Test complete workflow: ideas → script → audio → video in one call."""
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "src.server"],
        env=None
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("\n" + "="*70)
            print("TESTING COMPLETE WORKFLOW - Single Tool Call")
            print("="*70)
            
            # Test: Ideas → Script → Audio → Video (Complete!)
            print("\n🎬 Testing: generate_complete_video")
            print("   Topic: 'Pluribus Reactions'")
            print("   Duration: 30 seconds")
            print("   Video: test_content/test.mp4")
            print("   Voice: test_woman")
            print("\n⏳ This will:")
            print("   1. Fetch trending topics from Reddit, YouTube, News")
            print("   2. Generate an AI-powered script")
            print("   3. Clone voice from video")
            print("   4. Generate audio with cloned voice")
            print("   5. Extract frame from video")
            print("   6. Create talking head video with D-ID")
            print("\nStarting...\n")
            
            try:
                result = await session.call_tool(
                    "generate_complete_video",
                    arguments={
                        "topic": "Pluribus Reactions",
                        "duration_seconds": 30,
                        "video_path": "test_content/test.mp4",
                        "voice_name": "test_woman"
                    }
                )
                
                print("\n" + "="*70)
                print("✅ SUCCESS! Complete workflow executed in ONE tool call!")
                print("="*70)
                
                for content in result.content:
                    if hasattr(content, 'text'):
                        data = json.loads(content.text)
                        
                        print(f"\n📊 Results:")
                        print(f"   ✓ Script generated: {data.get('script_metadata', {}).get('word_count', 0)} words")
                        print(f"   ✓ Audio generated: {data.get('audio_path', 'N/A')}")
                        print(f"   ✓ Video generated: {data.get('video_path', 'N/A')}")
                        print(f"   ✓ Voice used: {data.get('voice_id', 'N/A')}")
                        
                        if data.get('script'):
                            print(f"\n📝 Script Preview (first 200 chars):")
                            print(f"   {data['script'][:200]}...")
                        
                        print(f"\n🎯 Message: {data.get('message', 'N/A')}")
                
                return True
                
            except Exception as e:
                print(f"\n❌ FAILED: {e}")
                import traceback
                traceback.print_exc()
                return False


if __name__ == "__main__":
    print("\n🚀 Testing MCP Complete Workflow")
    print("="*70)
    success = asyncio.run(test_complete_workflow())
    sys.exit(0 if success else 1)
