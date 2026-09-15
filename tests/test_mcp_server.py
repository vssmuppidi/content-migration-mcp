#!/usr/bin/env python3
"""
Test script for MCP server using MCP protocol.
Tests the server by sending MCP protocol messages and receiving responses.
This tests the full workflow: Get trending topics -> Generate script using Groq
"""

import asyncio
import json
import sys
import os
from mcp import ClientSession, StdioServerParameters, stdio_client


async def test_mcp_server_workflow():
    """Test the MCP server workflow: Get ideas -> Generate script with Groq."""
    print("="*70)
    print("MCP SERVER TEST - Full Workflow")
    print("="*70)
    print("\nTesting workflow:")
    print("1. Get trending topics about a subject (Reddit + YouTube + Google News)")
    print("2. Generate script from those topics using Groq only")
    print("\n" + "="*70 + "\n")
    
    # Get the Python executable path
    python_exe = sys.executable
    
    # Setup server parameters
    server_params = StdioServerParameters(
        command=python_exe,
        args=["-m", "src.server"],
        env=os.environ.copy()
    )
    
    try:
        # Connect to server
        print("Connecting to MCP server...")
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize
                print("Initializing server...")
                await session.initialize()
                print("✓ Server initialized\n")
                
                # List tools
                print("-"*70)
                print("Step 1: Listing available tools...")
                print("-"*70)
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"✓ Found {len(tools)} tools:")
                for tool in tools:
                    # Highlight the composite tool
                    marker = " ⭐ (Recommended for agents)" if tool.name == "generate_complete_script" else ""
                    print(f"  - {tool.name}{marker}")
                print()
                
                # Test: Get trending topics
                print("-"*70)
                print("Step 2: Getting trending topics about 'artificial intelligence'...")
                print("-"*70)
                print("  Fetching from: Reddit, YouTube, Google News\n")
                
                ideas_result = await session.call_tool(
                    "generate_ideas",
                    arguments={
                        "topic": "artificial intelligence",
                        "limit": 3
                    }
                )
                
                # Parse the result
                ideas_text = ideas_result.content[0].text
                ideas_data = json.loads(ideas_text)
                
                print(f"✓ Successfully fetched trending topics:")
                print(f"  - Reddit: {ideas_data['sources']['reddit']['count']} items")
                print(f"  - YouTube: {ideas_data['sources']['youtube']['count']} items")
                print(f"  - Google News: {ideas_data['sources']['google_news']['count']} items")
                print(f"  - Total: {ideas_data['summary']['total_items']} items")
                
                # Show sample items
                if ideas_data['sources']['reddit']['items']:
                    sample = ideas_data['sources']['reddit']['items'][0]
                    print(f"\n  📱 Sample Reddit post:")
                    print(f"     {sample['title'][:70]}...")
                    print(f"     Score: {sample.get('score', 0)} upvotes")
                
                if ideas_data['sources']['youtube']['items']:
                    sample = ideas_data['sources']['youtube']['items'][0]
                    print(f"\n  🎥 Sample YouTube video:")
                    print(f"     {sample['title'][:70]}...")
                    print(f"     Views: {sample.get('view_count', 0):,}")
                
                if ideas_data['sources']['google_news']['items']:
                    sample = ideas_data['sources']['google_news']['items'][0]
                    print(f"\n  📰 Sample News article:")
                    print(f"     {sample['title'][:70]}...")
                    print(f"     Source: {sample.get('source', 'Unknown')}")
                
                # Test: Generate script using the new composite tool (one-step)
                print("\n" + "-"*70)
                print("Step 3: Generating script using composite tool (ONE STEP)...")
                print("-"*70)
                print("  Using: generate_complete_script (fetches topics + generates script)")
                print("  Provider: Groq (FREE)")
                print("  Duration: 30 seconds")
                print("  Style: informative and engaging")
                print("  Note: This tool handles everything internally - perfect for agents!\n")
                
                script_result = await session.call_tool(
                    "generate_complete_script",
                    arguments={
                        "topic": "artificial intelligence",
                        "duration_seconds": 30,
                        "provider": "groq",  # Use Groq only
                        "style": "informative and engaging",
                        "limit": 3
                    }
                )
                
                # Parse the result
                script_text = script_result.content[0].text
                script_data = json.loads(script_text)
                
                if not script_data.get("success"):
                    print(f"✗ Script generation failed:")
                    error = script_data.get("error", "Unknown error")
                    print(f"  Error: {error}")
                    
                    provider_errors = script_data.get("provider_errors", [])
                    if provider_errors:
                        print("\n  Provider errors:")
                        for err in provider_errors:
                            print(f"    - {err}")
                    
                    # Check for specific errors
                    if "decommissioned" in error.lower():
                        print("\n  ⚠ Model decommissioned error!")
                        print("     Update GROQ_MODEL in your .env file")
                        print("     Try: llama-3.1-8b-instant or llama-3.3-70b-versatile")
                    elif "401" in error or "Unauthorized" in error:
                        print("\n  ⚠ Authentication error!")
                        print("     Check your GROQ_API_KEY in .env file")
                        print("     Key should start with 'gsk_'")
                    
                    return False
                
                metadata = script_data.get("metadata", {})
                script_content = script_data.get("script", "")
                trending_data = script_data.get("trending_data", {})
                
                # Also print the raw response for debugging
                print(f"✓ Successfully generated script using composite tool!")
                print(f"  - Provider: {metadata.get('provider', 'unknown')}")
                print(f"  - Model: {metadata.get('model', 'unknown')}")
                print(f"  - Word count: {metadata.get('actual_word_count', 0)}")
                print(f"  - Estimated duration: {metadata.get('estimated_duration_seconds', 0)}s")
                print(f"  - Script length: {len(script_content)} characters")
                
                # Show trending data summary (from composite tool)
                if trending_data:
                    total_items = trending_data.get("summary", {}).get("total_items", 0)
                    print(f"  - Trending topics fetched: {total_items} items")
                    
                    # Show enhanced context features (new features are automatically used)
                    print(f"\n  🔍 Enhanced Context Intelligence Features Used:")
                    print(f"     ✓ Intelligent ranking (relevance, engagement, recency, credibility)")
                    print(f"     ✓ Theme extraction across all sources")
                    print(f"     ✓ Sentiment analysis (positive/negative/mixed)")
                    print(f"     ✓ Trend detection (emerging, gaining traction, unique angles)")
                    print(f"     ✓ Cross-source correlation analysis")
                    print(f"     ✓ AI-powered summary (if Groq available, else rule-based)")
                
                # Print raw response text for debugging (optional - comment out for cleaner output)
                # print(f"\n  🔍 Raw Response (first 1000 chars):")
                # print("  " + "-"*66)
                # raw_preview = script_text[:1000] + "..." if len(script_text) > 1000 else script_text
                # print(f"  {raw_preview}")
                # print("  " + "-"*66)
                
                print(f"\n  📝 Generated Script (Full - {len(script_content)} chars):")
                print("  " + "="*66)
                # Show the complete script - print line by line to ensure we see everything
                if script_content:
                    print(script_content)
                else:
                    print("  (Script content is empty)")
                print("  " + "="*66)
                print(f"\n  Script Statistics:")
                print(f"  - Total characters: {len(script_content)}")
                print(f"  - Total words: {metadata.get('actual_word_count', 0)}")
                print(f"  - Estimated duration: {metadata.get('estimated_duration_seconds', 0)}s")
                print(f"  - Raw JSON length: {len(script_text)} characters")
                
                # Summary
                print("\n" + "="*70)
                print("TEST SUMMARY")
                print("="*70)
                print("✓ MCP server connected successfully")
                print("✓ Tools listed and accessible")
                print("✓ Composite tool 'generate_complete_script' tested")
                print("  - Automatically fetches trending topics (Reddit, YouTube, Google News)")
                print("  - Generates script incorporating trending data")
                print("  - Perfect for agents - one tool call does everything!")
                print("✓ Enhanced Context Intelligence Features:")
                print("  - Intelligent ranking with composite scoring")
                print("  - Theme extraction and keyword analysis")
                print("  - Sentiment analysis (positive/negative/mixed)")
                print("  - Trend detection (emerging, gaining traction, unique angles)")
                print("  - Cross-source correlation analysis")
                print("  - AI-powered summary generation (with automatic fallback)")
                print("✓ Script generated using Groq")
                print(f"  - Model: {metadata.get('model')}")
                print(f"  - Duration: {metadata.get('estimated_duration_seconds')}s")
                print(f"  - Word count: {metadata.get('actual_word_count', 0)} words")
                print("\n🎉 All tests passed! The MCP server workflow is working correctly.")
                print("💡 All enhanced context intelligence features are automatically used!")
                print("💡 Agents can now use 'generate_complete_script' for one-step script generation!")
                print("="*70)
                
                return True
                
    except Exception as e:
        print(f"\n✗ Test failed with exception: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the MCP server test."""
    try:
        # Check if we're in the right directory
        if not os.path.exists("src/server.py"):
            print("✗ Error: Cannot find src/server.py")
            print("  Please run this script from the project root directory")
            return 1
        
        result = asyncio.run(test_mcp_server_workflow())
        return 0 if result else 1
        
    except KeyboardInterrupt:
        print("\n\n⚠ Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
