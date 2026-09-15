"""Context enrichment service for automatically fetching and formatting context."""

from typing import Dict, List, Any, Optional
from ..tools.ideas import generate_ideas
from ..tools.context_processor import create_context_summary
from ..utils.query_analyzer import analyze_query_intent, determine_context_needs
from .context_cache import get_cache, cache_key_for_topic, cache_key_for_context_summary
from ..middleware.context_middleware import get_middleware


def enrich_query_with_context(query: str, analysis: Optional[Dict[str, Any]] = None) -> str:
    """
    Enrich a query with automatically fetched context.
    
    Args:
        query: The user's query
        analysis: Optional pre-computed query analysis (if None, will analyze)
    
    Returns:
        Enriched query string with context injected
    """
    # Analyze query if analysis not provided
    middleware = get_middleware()
    if analysis is None:
        analysis = analyze_query_intent(query)
        middleware.track_query_analysis(query, analysis)
    
    # Determine if context should be fetched
    context_needs = determine_context_needs(analysis["intent"], analysis["topics"])
    
    if not context_needs["should_fetch"] or not context_needs["sources"]:
        # No context needed, return original query
        return query
    
    # Fetch context
    context_data = fetch_relevant_context(
        intent=analysis["intent"],
        topics=analysis["topics"],
        sources=context_needs["sources"],
        limit=context_needs["limit"]
    )
    
    # Track context fetch
    if context_data:
        topic_str = analysis["topics"][0] if analysis.get("topics") else "unknown"
        middleware.track_context_fetch(
            topic_str,
            context_needs["sources"]
        )
    
    if not context_data:
        # Context fetch failed, return original query
        return query
    
    # Format context for prompt
    formatted_context = format_context_for_prompt(context_data, query, analysis)
    
    # Return enriched query
    return formatted_context


def fetch_relevant_context(
    intent: str,
    topics: List[str],
    sources: List[str],
    limit: int = 5
) -> Optional[Dict[str, Any]]:
    """
    Fetch relevant context from specified sources.
    
    Args:
        intent: Query intent
        topics: List of topics to fetch context for
        sources: List of sources to fetch from (reddit, youtube, news, all)
        limit: Maximum items per source
    
    Returns:
        Dictionary with fetched context data, or None if fetch failed
    """
    if not topics or not isinstance(topics, list) or len(topics) == 0:
        return None
    
    # Use first topic (or combine topics)
    topic = topics[0] if len(topics) == 1 else " ".join(topics[:2])
    
    # Normalize sources
    if "all" in sources:
        sources = ["reddit", "youtube", "news"]
    elif "none" in sources:
        return None
    
    # Check cache first
    cache = get_cache()
    middleware = get_middleware()
    cache_key = cache_key_for_topic(topic, sources)
    cached_data = cache.get(cache_key)
    
    if cached_data:
        middleware.track_cache_hit(cache_key)
        return cached_data
    else:
        middleware.track_cache_miss(cache_key)
    
    try:
        # Fetch context from sources
        # Use generate_ideas which fetches from all sources
        ideas_data = generate_ideas(topic=topic, limit=limit)
        
        # Cache the result (1 hour TTL for trending data)
        cache.set(cache_key, ideas_data, ttl=3600.0)
        
        return ideas_data
        
    except Exception as e:
        print(f"Error fetching context: {str(e)}")
        return None


def format_context_for_prompt(
    context_data: Dict[str, Any],
    query: str,
    analysis: Dict[str, Any]
) -> str:
    """
    Format context data as a prompt enhancement.
    
    Args:
        context_data: Fetched context data
        query: Original user query
        analysis: Query analysis result
    
    Returns:
        Formatted string with context and query
    """
    # Generate intelligent context summary
    topics = analysis.get("topics", [])
    topic = topics[0] if topics and len(topics) > 0 else context_data.get("topic", "unknown")
    
    # Check cache for summary
    cache = get_cache()
    sources = analysis.get("context_sources", ["all"])
    if "all" in sources:
        sources = ["reddit", "youtube", "news"]
    
    summary_cache_key = cache_key_for_context_summary(topic, sources)
    cached_summary = cache.get(summary_cache_key)
    
    if cached_summary:
        context_summary = cached_summary
    else:
        # Generate summary using context processor
        try:
            context_summary = create_context_summary(
                ideas_data=context_data,
                topic=topic,
                top_n_per_source=5,
                use_ai_summary=True
            )
            # Cache summary (1 hour TTL)
            cache.set(summary_cache_key, context_summary, ttl=3600.0)
        except Exception as e:
            print(f"Error generating context summary: {str(e)}")
            # Fallback to simple summary
            context_summary = _generate_simple_summary(context_data)
    
    # Format as enriched prompt
    enriched_prompt = f"""CONTEXT: {context_summary}

USER QUERY: {query}

Based on the context above, please provide a comprehensive response."""
    
    return enriched_prompt


def _generate_simple_summary(context_data: Dict[str, Any]) -> str:
    """Generate a simple summary from context data (fallback)."""
    summary_parts = []
    
    # Add topic
    topic = context_data.get("topic", "unknown")
    summary_parts.append(f"Trending topics about: {topic}")
    
    # Add source summaries
    sources = context_data.get("sources", {})
    for source_name, source_data in sources.items():
        items = source_data.get("items", [])
        if items:
            summary_parts.append(f"\n{source_name.upper()}:")
            for i, item in enumerate(items[:3], 1):
                title = item.get("title", "Unknown")
                summary_parts.append(f"  {i}. {title}")
    
    return "\n".join(summary_parts)


def should_auto_fetch_context(intent: str) -> bool:
    """
    Determine if context should be automatically fetched based on intent.
    
    Args:
        intent: Query intent
    
    Returns:
        True if context should be auto-fetched, False otherwise
    """
    auto_fetch_intents = [
        "trending_topics",
        "script_generation",
        "video_creation",
        "general_query"  # Might need context
    ]
    return intent in auto_fetch_intents

