#!/usr/bin/env python3
"""
Simple test script to test all MCP server tools.
Tests all idea generation and script generation tools with logging.
"""

import sys
import os
import traceback
from typing import Any, Dict

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.tools.ideas import (
    generate_ideas,
    generate_reddit_ideas,
    generate_youtube_ideas,
    generate_news_ideas
)
from src.tools.script import generate_script, generate_script_from_ideas
from src.config import config


def log_test(test_name: str):
    """Log test start."""
    print(f"\n{'='*60}")
    print(f"TEST: {test_name}")
    print(f"{'='*60}")


def log_success(message: str = "✓ Test passed"):
    """Log success."""
    print(f"✓ {message}")


def log_error(error: Exception, details: str = ""):
    """Log error with details."""
    print(f"✗ ERROR: {str(error)}")
    if details:
        print(f"  Details: {details}")
    print(f"  Traceback:")
    traceback.print_exc()


def log_result(result: Any, max_length: int = 200):
    """Log result summary."""
    result_str = str(result)
    if len(result_str) > max_length:
        result_str = result_str[:max_length] + "..."
    print(f"  Result: {result_str}")


def test_generate_ideas():
    """Test generate_ideas tool."""
    log_test("generate_ideas - Aggregating trending topics about AI")
    
    try:
        result = generate_ideas(topic="AI", limit=3)
        
        if isinstance(result, dict):
            total_items = result.get("summary", {}).get("total_items", 0)
            sources_available = result.get("summary", {}).get("sources_available", 0)
            
            log_success(f"Found {total_items} items from {sources_available} sources")
            
            # Check each source
            for source_name, source_data in result.get("sources", {}).items():
                count = source_data.get("count", 0)
                error = source_data.get("error")
                
                if error:
                    print(f"  ⚠ {source_name}: Error - {error}")
                else:
                    print(f"  ✓ {source_name}: {count} items")
            
            log_result(result, max_length=300)
            return True
        else:
            log_error(Exception("Unexpected result type"), f"Got {type(result)}")
            return False
    
    except Exception as e:
        log_error(e, "Failed to generate ideas from all sources")
        return False


def test_generate_reddit_ideas():
    """Test generate_reddit_ideas tool."""
    log_test("generate_reddit_ideas - Getting Reddit posts about Python")
    
    try:
        result = generate_reddit_ideas(topic="Python", subreddit="all", limit=3)
        
        if isinstance(result, dict):
            count = result.get("count", 0)
            error = result.get("error")
            
            if error:
                log_error(Exception(error), "Reddit API error")
                return False
            
            log_success(f"Found {count} Reddit posts")
            
            items = result.get("items", [])
            for i, item in enumerate(items[:2], 1):
                title = item.get("title", "No title")
                score = item.get("score", 0)
                print(f"  {i}. {title[:60]}... (Score: {score})")
            
            return True
        else:
            log_error(Exception("Unexpected result type"), f"Got {type(result)}")
            return False
    
    except Exception as e:
        log_error(e, "Failed to generate Reddit ideas")
        return False


def test_generate_youtube_ideas():
    """Test generate_youtube_ideas tool."""
    log_test("generate_youtube_ideas - Getting YouTube videos about technology")
    
    try:
        result = generate_youtube_ideas(topic="technology", order="viewCount", limit=3)
        
        if isinstance(result, dict):
            count = result.get("count", 0)
            error = result.get("error")
            
            if error:
                log_error(Exception(error), "YouTube API error")
                return False
            
            log_success(f"Found {count} YouTube videos")
            
            items = result.get("items", [])
            for i, item in enumerate(items[:2], 1):
                title = item.get("title", "No title")
                views = item.get("view_count", 0)
                print(f"  {i}. {title[:60]}... (Views: {views:,})")
            
            return True
        else:
            log_error(Exception("Unexpected result type"), f"Got {type(result)}")
            return False
    
    except Exception as e:
        log_error(e, "Failed to generate YouTube ideas")
        return False


def test_generate_news_ideas():
    """Test generate_news_ideas tool."""
    log_test("generate_news_ideas - Getting news about climate change")
    
    try:
        result = generate_news_ideas(topic="climate change", limit=3)
        
        if isinstance(result, dict):
            count = result.get("count", 0)
            error = result.get("error")
            
            if error:
                log_error(Exception(error), "Google News error")
                return False
            
            log_success(f"Found {count} news articles")
            
            items = result.get("items", [])
            for i, item in enumerate(items[:2], 1):
                title = item.get("title", "No title")
                source = item.get("source", "Unknown")
                print(f"  {i}. {title[:60]}... ({source})")
            
            return True
        else:
            log_error(Exception("Unexpected result type"), f"Got {type(result)}")
            return False
    
    except Exception as e:
        log_error(e, "Failed to generate news ideas")
        return False


def test_generate_script():
    """Test generate_script tool."""
    log_test("generate_script - Generating a 15-second script about space")
    
    try:
        # Check which providers are available
        print(f"  Available providers:")
        if config.validate_groq_config():
            print(f"    ✓ Groq: {config.groq_model}")
        if config.validate_openrouter_config():
            print(f"    ✓ OpenRouter: {config.openrouter_model}")
        print(f"  Primary provider: {config.inference_provider}")
        print()
        
        result = generate_script(
            topic="space exploration",
            duration_seconds=15,
            style="excited and informative"
        )
        
        if isinstance(result, dict):
            success = result.get("success", False)
            error = result.get("error")
            
            if not success:
                # Show more detailed error info
                error_msg = error or "Script generation failed"
                provider_errors = result.get("provider_errors", [])
                
                print(f"  Provider errors:")
                for i, provider_error in enumerate(provider_errors, 1):
                    provider_name = provider_error.split(":")[0] if ":" in provider_error else "Unknown"
                    error_text = provider_error.split(":", 1)[1] if ":" in provider_error else provider_error
                    print(f"    {i}. {provider_name}: {error_text[:100]}")
                
                # Check if it's an authentication error
                if "401" in error_msg or "Unauthorized" in error_msg:
                    print(f"\n  ⚠ Authentication error detected!")
                    print(f"    This usually means:")
                    print(f"    - API key is incorrect or invalid")
                    print(f"    - API key has expired")
                    print(f"    - API key format is wrong")
                    print(f"    - Check your .env file:")
                    print(f"      - GROQ_API_KEY should start with 'gsk_'")
                    print(f"      - OPENROUTER_API_KEY should start with 'sk-or-v1-'")
                elif "403" in error_msg or "Forbidden" in error_msg:
                    print(f"  ⚠ Authorization error: API key may not have required permissions")
                elif "429" in error_msg or "Rate limit" in error_msg:
                    print(f"  ⚠ Rate limit exceeded: Wait a moment and try again")
                elif "quota" in error_msg.lower():
                    print(f"  ⚠ Quota exceeded: Check your API account limits")
                
                log_error(Exception(error_msg), "Script generation error")
                return False
            
            script = result.get("script", "")
            metadata = result.get("metadata", {})
            provider = metadata.get("provider", "unknown")
            model = metadata.get("model", "unknown")
            word_count = metadata.get("actual_word_count", 0)
            
            log_success(f"Generated script using {provider} ({model})")
            print(f"  Word count: {word_count}")
            print(f"  Script preview: {script[:150]}...")
            
            return True
        else:
            log_error(Exception("Unexpected result type"), f"Got {type(result)}")
            return False
    
    except Exception as e:
        log_error(e, "Failed to generate script")
        return False


def test_generate_script_from_ideas():
    """Test generate_script_from_ideas tool."""
    log_test("generate_script_from_ideas - Generating script from trending ideas")
    
    try:
        # First, get some ideas
        print("  Step 1: Fetching trending ideas...")
        ideas_data = generate_ideas(topic="artificial intelligence", limit=2)
        
        if not isinstance(ideas_data, dict):
            log_error(Exception("Failed to get ideas data"), "Cannot proceed without ideas")
            return False
        
        total_items = ideas_data.get("summary", {}).get("total_items", 0)
        if total_items == 0:
            log_error(Exception("No ideas found"), "Cannot generate script without source material")
            return False
        
        print(f"  ✓ Found {total_items} trending items")
        
        # Now generate script from ideas
        print("  Step 2: Generating script from ideas...")
        result = generate_script_from_ideas(
            ideas_data=ideas_data,
            duration_seconds=20,
            style="informative and engaging"
        )
        
        if isinstance(result, dict):
            success = result.get("success", False)
            error = result.get("error")
            
            if not success:
                log_error(Exception(error or "Script generation failed"), "Script generation error")
                return False
            
            script = result.get("script", "")
            metadata = result.get("metadata", {})
            provider = metadata.get("provider", "unknown")
            word_count = metadata.get("actual_word_count", 0)
            
            log_success(f"Generated script using {provider}")
            print(f"  Word count: {word_count}")
            print(f"  Script preview: {script[:150]}...")
            
            return True
        else:
            log_error(Exception("Unexpected result type"), f"Got {type(result)}")
            return False
    
    except Exception as e:
        log_error(e, "Failed to generate script from ideas")
        return False


def check_configuration():
    """Check if configuration is valid."""
    print(f"\n{'='*60}")
    print("CONFIGURATION CHECK")
    print(f"{'='*60}")
    
    # Check each service
    checks = {
        "Reddit": config.validate_reddit_config(),
        "YouTube": config.validate_youtube_config(),
        "OpenRouter": config.validate_openrouter_config(),
        "Groq": config.validate_groq_config(),
    }
    
    for service, is_configured in checks.items():
        status = "✓" if is_configured else "✗"
        print(f"  {status} {service}: {'Configured' if is_configured else 'Not configured'}")
    
    # Check inference APIs
    has_inference = config.has_inference_api()
    print(f"\n  {'✓' if has_inference else '✗'} Inference API: {'Available' if has_inference else 'NOT AVAILABLE (need OpenRouter or Groq)'}")
    
    if config.validate_openrouter_config():
        print(f"  → OpenRouter Model: {config.openrouter_model}")
    if config.validate_groq_config():
        print(f"  → Groq Model: {config.groq_model}")
    if has_inference:
        print(f"  → Primary Provider: {config.inference_provider}")
    
    print()
    
    if not has_inference:
        print("⚠ WARNING: No inference API configured. Script generation tests will fail.")
        print("  Please configure at least one: OPENROUTER_API_KEY or GROQ_API_KEY\n")
    
    return all([checks["Reddit"], checks["YouTube"], has_inference])


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("CONTENT MCP SERVER - TOOL TESTING")
    print("="*60)
    
    # Check configuration first
    config_ok = check_configuration()
    
    if not config_ok:
        print("⚠ Some required configurations are missing.")
        print("  Some tests may fail. Continuing anyway...\n")
    
    # Test results
    results = {}
    
    # Test idea generation tools
    print("\n" + "="*60)
    print("TESTING IDEA GENERATION TOOLS")
    print("="*60)
    
    results["generate_ideas"] = test_generate_ideas()
    results["generate_reddit_ideas"] = test_generate_reddit_ideas()
    results["generate_youtube_ideas"] = test_generate_youtube_ideas()
    results["generate_news_ideas"] = test_generate_news_ideas()
    
    # Test script generation tools
    print("\n" + "="*60)
    print("TESTING SCRIPT GENERATION TOOLS")
    print("="*60)
    
    results["generate_script"] = test_generate_script()
    results["generate_script_from_ideas"] = test_generate_script_from_ideas()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    total_tests = len(results)
    passed_tests = sum(1 for v in results.values() if v)
    failed_tests = total_tests - passed_tests
    
    for test_name, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {total_tests} tests")
    print(f"  Passed: {passed_tests}")
    print(f"  Failed: {failed_tests}")
    
    if failed_tests == 0:
        print("\n🎉 All tests passed!")
        return 0
    else:
        print(f"\n⚠ {failed_tests} test(s) failed. Check the errors above.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {str(e)}")
        traceback.print_exc()
        sys.exit(1)

