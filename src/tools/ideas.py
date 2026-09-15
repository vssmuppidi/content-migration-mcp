"""Content idea generation tools for MCP server."""

from typing import Dict, List, Optional, Any
from ..sources.reddit import get_reddit_ideas
from ..sources.youtube import get_youtube_ideas
from ..sources.google_news import get_news_ideas


def generate_ideas(topic: str, limit: int = 10) -> Dict[str, Any]:
    """
    Generate content ideas by aggregating data from all sources.
    
    This is the generalized tool that scans Reddit, YouTube, and Google News
    to identify trending topics and related information.
    
    Args:
        topic: The topic or event to search for (e.g., "AI", "Trump", "climate change")
        limit: Maximum number of results per source (default: 10)
        
    Returns:
        Dictionary containing trending topics from all sources with metadata
    """
    results = {
        "topic": topic,
        "sources": {
            "reddit": {"items": [], "count": 0, "error": None},
            "youtube": {"items": [], "count": 0, "error": None},
            "google_news": {"items": [], "count": 0, "error": None}
        },
        "summary": {
            "total_items": 0,
            "sources_available": 0
        }
    }
    
    # Fetch from Reddit
    try:
        reddit_data = get_reddit_ideas(topic, limit=limit)
        results["sources"]["reddit"]["items"] = reddit_data
        results["sources"]["reddit"]["count"] = len(reddit_data)
        if reddit_data:
            results["summary"]["sources_available"] += 1
            results["summary"]["total_items"] += len(reddit_data)
    except Exception as e:
        results["sources"]["reddit"]["error"] = str(e)
    
    # Fetch from YouTube
    try:
        youtube_data = get_youtube_ideas(topic, limit=limit)
        results["sources"]["youtube"]["items"] = youtube_data
        results["sources"]["youtube"]["count"] = len(youtube_data)
        if youtube_data:
            results["summary"]["sources_available"] += 1
            results["summary"]["total_items"] += len(youtube_data)
    except Exception as e:
        results["sources"]["youtube"]["error"] = str(e)
    
    # Fetch from Google News
    try:
        news_data = get_news_ideas(topic, limit=limit)
        results["sources"]["google_news"]["items"] = news_data
        results["sources"]["google_news"]["count"] = len(news_data)
        if news_data:
            results["summary"]["sources_available"] += 1
            results["summary"]["total_items"] += len(news_data)
    except Exception as e:
        results["sources"]["google_news"]["error"] = str(e)
    
    return results


def generate_reddit_ideas(
    topic: str,
    subreddit: Optional[str] = "all",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Generate content ideas from Reddit only.
    
    Args:
        topic: The topic to search for
        subreddit: Target subreddit (default: "all")
        limit: Maximum number of results (default: 10)
        
    Returns:
        Dictionary containing Reddit posts with metadata
    """
    try:
        items = get_reddit_ideas(topic, subreddit=subreddit, limit=limit)
        return {
            "source": "reddit",
            "topic": topic,
            "subreddit": subreddit,
            "count": len(items),
            "items": items,
            "error": None
        }
    except Exception as e:
        return {
            "source": "reddit",
            "topic": topic,
            "subreddit": subreddit,
            "count": 0,
            "items": [],
            "error": str(e)
        }


def generate_youtube_ideas(
    topic: str,
    order: str = "viewCount",
    limit: int = 10
) -> Dict[str, Any]:
    """
    Generate content ideas from YouTube only.
    
    Args:
        topic: The topic to search for
        order: Sort order - "viewCount", "relevance", "date", "rating" (default: "viewCount")
        limit: Maximum number of results (default: 10)
        
    Returns:
        Dictionary containing YouTube videos with metadata
    """
    try:
        items = get_youtube_ideas(topic, limit=limit, order=order)
        return {
            "source": "youtube",
            "topic": topic,
            "order": order,
            "count": len(items),
            "items": items,
            "error": None
        }
    except Exception as e:
        return {
            "source": "youtube",
            "topic": topic,
            "order": order,
            "count": 0,
            "items": [],
            "error": str(e)
        }


def generate_news_ideas(
    topic: str,
    limit: int = 10
) -> Dict[str, Any]:
    """
    Generate content ideas from Google News only.
    
    Args:
        topic: The topic to search for
        limit: Maximum number of results (default: 10)
        
    Returns:
        Dictionary containing news articles with metadata
    """
    try:
        items = get_news_ideas(topic, limit=limit)
        return {
            "source": "google_news",
            "topic": topic,
            "count": len(items),
            "items": items,
            "error": None
        }
    except Exception as e:
        return {
            "source": "google_news",
            "topic": topic,
            "count": 0,
            "items": [],
            "error": str(e)
        }

