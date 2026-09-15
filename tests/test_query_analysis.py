"""Test suite for query analysis and context injection."""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.utils.query_analyzer import analyze_query_intent, extract_topics, detect_implicit_requirements
from src.services.context_enricher import enrich_query_with_context, fetch_relevant_context
from src.services.context_cache import get_cache
from src.services.tool_orchestrator import orchestrate_complete_workflow, get_recommended_approach
from src.middleware.context_middleware import get_middleware


def test_query_analysis():
    """Test query intent analysis."""
    print("\n" + "="*60)
    print("TEST: Query Intent Analysis")
    print("="*60)
    
    test_queries = [
        "What's trending about AI?",
        "Generate a 60-second script about climate change",
        "Create a video about artificial intelligence",
        "Clone my voice from this video",
        "What's happening with the election?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        try:
            analysis = analyze_query_intent(query)
            print(f"  Intent: {analysis['intent']}")
            print(f"  Topics: {analysis['topics']}")
            print(f"  Context Sources: {analysis['context_sources']}")
            print(f"  Requirements: {analysis['requirements']}")
            print(f"  Confidence: {analysis['confidence']}")
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")


def test_topic_extraction():
    """Test topic extraction."""
    print("\n" + "="*60)
    print("TEST: Topic Extraction")
    print("="*60)
    
    test_queries = [
        "What's trending about artificial intelligence and machine learning?",
        "Generate a script about climate change and renewable energy",
        "What's happening with the US election?",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        topics = extract_topics(query)
        print(f"  Extracted Topics: {topics}")


def test_implicit_requirements():
    """Test implicit requirement detection."""
    print("\n" + "="*60)
    print("TEST: Implicit Requirements Detection")
    print("="*60)
    
    test_queries = [
        "Generate a 60-second informative script about AI",
        "Create a 30-second funny video",
        "Clone voice from /path/to/video.mp4",
        "Use the voice named test_woman",
    ]
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        requirements = detect_implicit_requirements(query)
        print(f"  Requirements: {requirements}")


def test_context_enrichment():
    """Test context enrichment."""
    print("\n" + "="*60)
    print("TEST: Context Enrichment")
    print("="*60)
    
    query = "What's trending about AI?"
    print(f"\nQuery: {query}")
    
    try:
        enriched = enrich_query_with_context(query)
        print(f"\n✓ Enriched query length: {len(enriched)} characters")
        print(f"\nFirst 500 characters of enriched query:")
        print("-" * 60)
        print(enriched[:500])
        print("-" * 60)
        return True
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_context_fetching():
    """Test context fetching."""
    print("\n" + "="*60)
    print("TEST: Context Fetching")
    print("="*60)
    
    topic = "artificial intelligence"
    print(f"\nFetching context for: {topic}")
    
    try:
        context = fetch_relevant_context(
            intent="trending_topics",
            topics=[topic],
            sources=["reddit", "youtube", "news"],
            limit=3
        )
        
        if context:
            print(f"✓ Context fetched successfully")
            print(f"  Reddit items: {len(context.get('sources', {}).get('reddit', {}).get('items', []))}")
            print(f"  YouTube items: {len(context.get('sources', {}).get('youtube', {}).get('items', []))}")
            print(f"  News items: {len(context.get('sources', {}).get('google_news', {}).get('items', []))}")
            return True
        else:
            print("✗ No context fetched")
            return False
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_cache():
    """Test context caching."""
    print("\n" + "="*60)
    print("TEST: Context Caching")
    print("="*60)
    
    cache = get_cache()
    
    # Test cache set/get
    cache.set("test_key", {"data": "test"}, ttl=60.0)
    value = cache.get("test_key")
    
    if value and value.get("data") == "test":
        print("✓ Cache set/get works")
    else:
        print("✗ Cache set/get failed")
        return False
    
    # Test cache expiration
    cache.set("expiring_key", {"data": "expires"}, ttl=0.1)  # Very short TTL
    import time
    time.sleep(0.2)
    expired_value = cache.get("expiring_key")
    
    if expired_value is None:
        print("✓ Cache expiration works")
    else:
        print("✗ Cache expiration failed")
        return False
    
    # Get stats
    stats = cache.get_stats()
    print(f"\nCache Stats:")
    print(f"  Size: {stats['size']}")
    print(f"  Hits: {stats['hits']}")
    print(f"  Misses: {stats['misses']}")
    print(f"  Hit Rate: {stats['hit_rate']:.2%}")
    
    return True


def test_tool_orchestration():
    """Test tool orchestration."""
    print("\n" + "="*60)
    print("TEST: Tool Orchestration")
    print("="*60)
    
    test_cases = [
        ("trending_topics", ["AI"], {}),
        ("script_generation", ["climate change"], {"duration": 60, "style": "informative"}),
        ("video_creation", ["AI"], {"duration": 30, "video_path": "/path/to/video.mp4"}),
    ]
    
    for intent, topics, requirements in test_cases:
        print(f"\nIntent: {intent}, Topics: {topics}")
        orchestration = orchestrate_complete_workflow(intent, topics, requirements)
        print(f"  Tool Sequence: {orchestration['tool_sequence']}")
        print(f"  Auto Context: {orchestration['auto_context']}")
        print(f"  Recommendation: {orchestration.get('recommendation', orchestration.get('note', 'N/A'))}")


def test_middleware_stats():
    """Test middleware statistics."""
    print("\n" + "="*60)
    print("TEST: Middleware Statistics")
    print("="*60)
    
    middleware = get_middleware()
    middleware.reset_stats()
    
    # Simulate some operations
    middleware.track_query_analysis("test query", {"intent": "trending_topics"})
    middleware.track_context_fetch("AI", ["reddit", "youtube"])
    middleware.track_prompt_enrichment("trending_analysis", "test query")
    middleware.track_resource_access("trending://topics/AI")
    middleware.track_cache_hit("test_key")
    middleware.track_cache_miss("miss_key")
    
    stats = middleware.get_stats()
    print("\nMiddleware Stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("QUERY ANALYSIS AND CONTEXT INJECTION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Query Analysis", test_query_analysis),
        ("Topic Extraction", test_topic_extraction),
        ("Implicit Requirements", test_implicit_requirements),
        ("Context Enrichment", test_context_enrichment),
        ("Context Fetching", test_context_fetching),
        ("Cache", test_cache),
        ("Tool Orchestration", test_tool_orchestration),
        ("Middleware Stats", test_middleware_stats),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*60}")
            result = test_func()
            results[test_name] = result if result is not None else True
        except KeyboardInterrupt:
            print("\n\nTest suite interrupted by user.")
            break
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {str(e)}")
            import traceback
            traceback.print_exc()
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"{status:8} {test_name}")
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    total = len(results)
    
    print(f"\nTotal: {passed}/{total} passed, {failed} failed")


if __name__ == "__main__":
    main()

