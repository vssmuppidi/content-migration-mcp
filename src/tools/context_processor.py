"""Context processing and intelligence for script generation.

This module provides intelligent context extraction, ranking, and summarization
to improve the quality of context provided to AI models for script generation.
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re
from collections import Counter
import json


def calculate_relevance_score(item: Dict[str, Any], topic: str, source_type: str) -> float:
    """
    Calculate relevance score for an item based on topic matching.
    
    Args:
        item: Item from Reddit, YouTube, or News
        topic: The search topic
        source_type: "reddit", "youtube", or "google_news"
        
    Returns:
        Relevance score (0-100)
    """
    topic_lower = topic.lower()
    topic_words = set(topic_lower.split())
    
    # Extract text to search
    text_to_search = ""
    if source_type == "reddit":
        text_to_search = f"{item.get('title', '')} {item.get('selftext', '')}".lower()
    elif source_type == "youtube":
        text_to_search = f"{item.get('title', '')} {item.get('description', '')}".lower()
        # Also check tags
        tags = item.get('tags', [])
        if tags:
            text_to_search += " " + " ".join(tags).lower()
    elif source_type == "google_news":
        text_to_search = f"{item.get('title', '')} {item.get('description', '')}".lower()
    
    # Count topic word matches
    matches = sum(1 for word in topic_words if word in text_to_search)
    relevance = (matches / max(len(topic_words), 1)) * 100
    
    # Boost if topic phrase appears exactly
    if topic_lower in text_to_search:
        relevance = min(100, relevance + 20)
    
    return min(100, relevance)


def calculate_engagement_score(item: Dict[str, Any], source_type: str) -> float:
    """
    Calculate engagement score based on source-specific metrics.
    
    Args:
        item: Item from Reddit, YouTube, or News
        source_type: "reddit", "youtube", or "google_news"
        
    Returns:
        Engagement score (0-100)
    """
    if source_type == "reddit":
        # Use pre-calculated engagement_score if available
        if "engagement_score" in item:
            return min(100, item["engagement_score"])
        # Fallback calculation
        score = item.get("score", 0)
        comments = item.get("num_comments", 0)
        return min(100, (score * 0.4) + (comments * 0.6))
    
    elif source_type == "youtube":
        # Use engagement_ratio if available
        if "engagement_ratio" in item:
            return min(100, item["engagement_ratio"] * 10)  # Scale to 0-100
        # Fallback: use view count as proxy
        view_count = item.get("view_count", 0)
        if view_count > 1000000:
            return 100
        elif view_count > 100000:
            return 75
        elif view_count > 10000:
            return 50
        else:
            return 25
    
    elif source_type == "google_news":
        # News doesn't have engagement metrics, use credibility
        return item.get("credibility_score", 0.5) * 100
    
    return 50  # Default


def calculate_recency_score(item: Dict[str, Any], source_type: str) -> float:
    """
    Calculate recency score (newer = higher score).
    
    Args:
        item: Item from Reddit, YouTube, or News
        source_type: "reddit", "youtube", or "google_news"
        
    Returns:
        Recency score (0-100)
    """
    if source_type == "reddit":
        if "recency_score" in item:
            return item["recency_score"]
        # Fallback calculation
        age_hours = item.get("age_hours", 720)  # Default to 30 days old
        return max(0, 100 - (age_hours / 24))
    
    elif source_type == "youtube":
        # Parse published_at if available (ISO format)
        published_at = item.get("published_at", "")
        if published_at:
            try:
                # Try parsing ISO format date (YouTube uses RFC 3339)
                # Remove timezone info for simplicity
                date_str = published_at.split('T')[0] if 'T' in published_at else published_at
                if date_str:
                    return 75
            except Exception:
                pass
        return 50
    
    elif source_type == "google_news":
        if "recency_score" in item:
            return item["recency_score"]
        return 50
    
    return 50


def calculate_credibility_score(item: Dict[str, Any], source_type: str) -> float:
    """
    Calculate credibility score based on source.
    
    Args:
        item: Item from Reddit, YouTube, or News
        source_type: "reddit", "youtube", or "google_news"
        
    Returns:
        Credibility score (0-100)
    """
    if source_type == "reddit":
        # Reddit: use upvote_ratio as credibility proxy
        upvote_ratio = item.get("upvote_ratio", 0.5)
        return upvote_ratio * 100
    
    elif source_type == "youtube":
        # YouTube: use channel reputation (simplified)
        # Major channels get higher credibility
        channel = item.get("channel_title", "").lower()
        major_channels = ["ted", "ted-ed", "veritasium", "kurzgesagt", "vsauce", "national geographic"]
        if any(mc in channel for mc in major_channels):
            return 90
        return 70  # Default
    
    elif source_type == "google_news":
        # Use pre-calculated credibility_score
        if "credibility_score" in item:
            return item["credibility_score"] * 100
        return 50
    
    return 50


def calculate_composite_score(
    item: Dict[str, Any],
    topic: str,
    source_type: str,
    weights: Optional[Dict[str, float]] = None
) -> Tuple[float, Dict[str, float]]:
    """
    Calculate composite score for ranking items.
    
    Args:
        item: Item from Reddit, YouTube, or News
        topic: The search topic
        source_type: "reddit", "youtube", or "google_news"
        weights: Optional custom weights (default: relevance 40%, engagement 30%, recency 20%, credibility 10%)
        
    Returns:
        Tuple of (composite_score, score_breakdown)
    """
    if weights is None:
        weights = {
            "relevance": 0.40,
            "engagement": 0.30,
            "recency": 0.20,
            "credibility": 0.10
        }
    
    relevance = calculate_relevance_score(item, topic, source_type)
    engagement = calculate_engagement_score(item, source_type)
    recency = calculate_recency_score(item, source_type)
    credibility = calculate_credibility_score(item, source_type)
    
    composite = (
        relevance * weights["relevance"] +
        engagement * weights["engagement"] +
        recency * weights["recency"] +
        credibility * weights["credibility"]
    )
    
    return (
        round(composite, 2),
        {
            "relevance": round(relevance, 2),
            "engagement": round(engagement, 2),
            "recency": round(recency, 2),
            "credibility": round(credibility, 2)
        }
    )


def rank_and_filter_items(
    items: List[Dict[str, Any]],
    topic: str,
    source_type: str,
    top_n: int = 5
) -> List[Dict[str, Any]]:
    """
    Rank and filter items by composite score.
    
    Args:
        items: List of items from a source
        topic: The search topic
        source_type: "reddit", "youtube", or "google_news"
        top_n: Number of top items to return
        
    Returns:
        List of top-ranked items with scores added
    """
    scored_items = []
    for item in items:
        composite_score, score_breakdown = calculate_composite_score(item, topic, source_type)
        item_with_score = item.copy()
        item_with_score["_composite_score"] = composite_score
        item_with_score["_score_breakdown"] = score_breakdown
        scored_items.append(item_with_score)
    
    # Sort by composite score (descending)
    scored_items.sort(key=lambda x: x["_composite_score"], reverse=True)
    
    return scored_items[:top_n]


def extract_themes(items: List[Dict[str, Any]], source_type: str) -> Dict[str, Any]:
    """
    Extract key themes and keywords from items.
    
    Args:
        items: List of items from sources
        source_type: "reddit", "youtube", or "google_news"
        
    Returns:
        Dictionary with themes, keywords, and insights
    """
    all_text = []
    keywords = []
    
    for item in items:
        if source_type == "reddit":
            all_text.append(item.get("title", ""))
            all_text.append(item.get("selftext", ""))
            # Add comment text
            for comment in item.get("top_comments", []):
                all_text.append(comment.get("text", ""))
        elif source_type == "youtube":
            all_text.append(item.get("title", ""))
            all_text.append(item.get("description", ""))
            keywords.extend(item.get("tags", []))
        elif source_type == "google_news":
            all_text.append(item.get("title", ""))
            all_text.append(item.get("description", ""))
            keywords.extend(item.get("keywords", []))
    
    # Extract common words (simple approach)
    text = " ".join(all_text).lower()
    # Remove common stop words
    stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
    
    words = re.findall(r'\b[a-z]{4,}\b', text)  # Words 4+ chars
    filtered_words = [w for w in words if w not in stop_words]
    
    # Count word frequency
    word_freq = Counter(filtered_words)
    top_keywords = [word for word, count in word_freq.most_common(10)]
    
    # Combine with explicit keywords
    all_keywords = list(set(top_keywords + keywords))[:15]
    
    return {
        "top_keywords": all_keywords,
        "word_frequency": dict(word_freq.most_common(10)),
        "total_items_analyzed": len(items)
    }


def analyze_sentiment(items: List[Dict[str, Any]], source_type: str) -> Dict[str, Any]:
    """
    Simple sentiment analysis based on keywords.
    
    Args:
        items: List of items from sources
        source_type: "reddit", "youtube", or "google_news"
        
    Returns:
        Dictionary with sentiment analysis
    """
    positive_words = ['good', 'great', 'excellent', 'amazing', 'wonderful', 'fantastic', 'love', 'best', 'awesome', 'brilliant', 'success', 'win', 'positive', 'improve', 'better']
    negative_words = ['bad', 'terrible', 'awful', 'worst', 'hate', 'fail', 'problem', 'issue', 'negative', 'worse', 'disappoint', 'critic', 'concern', 'worry']
    neutral_words = ['news', 'report', 'update', 'announce', 'information', 'data', 'study', 'research']
    
    all_text = []
    for item in items:
        if source_type == "reddit":
            all_text.append(item.get("title", ""))
            all_text.append(item.get("selftext", ""))
        elif source_type == "youtube":
            all_text.append(item.get("title", ""))
            all_text.append(item.get("description", ""))
        elif source_type == "google_news":
            all_text.append(item.get("title", ""))
            all_text.append(item.get("description", ""))
    
    text = " ".join(all_text).lower()
    
    positive_count = sum(1 for word in positive_words if word in text)
    negative_count = sum(1 for word in negative_words if word in text)
    neutral_count = sum(1 for word in neutral_words if word in text)
    
    total = positive_count + negative_count + neutral_count
    if total == 0:
        sentiment = "neutral"
    elif positive_count > negative_count * 1.5:
        sentiment = "positive"
    elif negative_count > positive_count * 1.5:
        sentiment = "negative"
    else:
        sentiment = "mixed"
    
    return {
        "sentiment": sentiment,
        "positive_signals": positive_count,
        "negative_signals": negative_count,
        "neutral_signals": neutral_count,
        "confidence": "high" if total > 5 else "medium" if total > 2 else "low"
    }


def detect_trends(
    items: List[Dict[str, Any]],
    source_type: str
) -> Dict[str, Any]:
    """
    Detect emerging trends and identify what's gaining vs losing traction.
    
    Args:
        items: List of items from sources (should be sorted by composite score)
        source_type: "reddit", "youtube", or "google_news"
        
    Returns:
        Dictionary with trend analysis including emerging trends, gaining traction, etc.
    """
    if not items:
        return {
            "emerging_trends": [],
            "gaining_traction": [],
            "losing_traction": [],
            "stable_trends": [],
            "unique_angles": []
        }
    
    # Calculate engagement velocity (rate of engagement)
    # Items with high engagement and high recency = gaining traction
    # Items with high engagement but low recency = stable/established
    # Items with low engagement but high recency = emerging
    
    emerging_trends = []
    gaining_traction = []
    losing_traction = []
    stable_trends = []
    
    # Thresholds for classification
    high_engagement_threshold = 70  # Above this = high engagement
    high_recency_threshold = 70  # Above this = very recent
    medium_engagement_threshold = 40
    medium_recency_threshold = 40
    
    for item in items:
        engagement_score = item.get("_score_breakdown", {}).get("engagement", 0)
        recency_score = item.get("_score_breakdown", {}).get("recency", 0)
        composite_score = item.get("_composite_score", 0)
        
        # Extract key information
        trend_info = {
            "title": item.get("title", "")[:100],
            "engagement_score": engagement_score,
            "recency_score": recency_score,
            "composite_score": composite_score,
            "source": source_type
        }
        
        # Add source-specific metrics
        if source_type == "reddit":
            trend_info["score"] = item.get("score", 0)
            trend_info["comments"] = item.get("num_comments", 0)
            trend_info["age_hours"] = item.get("age_hours", 0)
        elif source_type == "youtube":
            trend_info["views"] = item.get("view_count", 0)
            trend_info["engagement_ratio"] = item.get("engagement_ratio", 0)
        elif source_type == "google_news":
            trend_info["source_name"] = item.get("source", "Unknown")
            trend_info["age_hours"] = item.get("age_hours", 0)
        
        # Classify trends
        if recency_score >= high_recency_threshold and engagement_score >= medium_engagement_threshold:
            # Very recent + good engagement = gaining traction
            if engagement_score >= high_engagement_threshold:
                gaining_traction.append(trend_info)
            else:
                # High recency but moderate engagement = emerging
                emerging_trends.append(trend_info)
        elif engagement_score >= high_engagement_threshold and recency_score >= medium_recency_threshold:
            # High engagement + decent recency = stable/established trend
            stable_trends.append(trend_info)
        elif engagement_score < medium_engagement_threshold and recency_score < medium_recency_threshold:
            # Low engagement + old = losing traction
            losing_traction.append(trend_info)
        elif recency_score >= high_recency_threshold and engagement_score < medium_engagement_threshold:
            # Very recent but low engagement = emerging (potential)
            emerging_trends.append(trend_info)
        else:
            # Default to stable
            stable_trends.append(trend_info)
    
    # Find unique angles (items with high relevance but lower overall engagement)
    # These might be niche topics or unique perspectives
    unique_angles = []
    for item in items:
        relevance = item.get("_score_breakdown", {}).get("relevance", 0)
        engagement = item.get("_score_breakdown", {}).get("engagement", 0)
        
        # High relevance but moderate engagement = unique angle
        if relevance >= 70 and engagement < high_engagement_threshold:
            unique_angles.append({
                "title": item.get("title", "")[:100],
                "relevance_score": relevance,
                "engagement_score": engagement,
                "source": source_type,
                "insight": "High relevance but niche engagement - unique perspective"
            })
    
    # Limit results to top items
    emerging_trends = sorted(emerging_trends, key=lambda x: x.get("recency_score", 0), reverse=True)[:5]
    gaining_traction = sorted(gaining_traction, key=lambda x: x.get("composite_score", 0), reverse=True)[:5]
    losing_traction = sorted(losing_traction, key=lambda x: x.get("recency_score", 0))[:3]  # Oldest first
    stable_trends = sorted(stable_trends, key=lambda x: x.get("composite_score", 0), reverse=True)[:5]
    unique_angles = unique_angles[:5]
    
    return {
        "emerging_trends": emerging_trends,
        "gaining_traction": gaining_traction,
        "losing_traction": losing_traction,
        "stable_trends": stable_trends,
        "unique_angles": unique_angles
    }


def find_cross_source_correlations(
    reddit_items: List[Dict[str, Any]],
    youtube_items: List[Dict[str, Any]],
    news_items: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Find correlations and common themes across sources.
    
    Args:
        reddit_items: Top Reddit items
        youtube_items: Top YouTube items
        news_items: Top News items
        
    Returns:
        Dictionary with correlations and insights
    """
    # Extract keywords from each source
    reddit_themes = extract_themes(reddit_items, "reddit")
    youtube_themes = extract_themes(youtube_items, "youtube")
    news_themes = extract_themes(news_items, "google_news")
    
    # Find common keywords
    reddit_keywords = set(reddit_themes.get("top_keywords", []))
    youtube_keywords = set(youtube_themes.get("top_keywords", []))
    news_keywords = set(news_themes.get("top_keywords", []))
    
    # Find intersections
    all_common = reddit_keywords & youtube_keywords & news_keywords
    reddit_youtube_common = reddit_keywords & youtube_keywords
    reddit_news_common = reddit_keywords & news_keywords
    youtube_news_common = youtube_keywords & news_keywords
    
    # Build correlation insights
    correlations = []
    
    if all_common:
        correlations.append({
            "type": "all_sources",
            "keywords": list(all_common),
            "insight": f"These keywords appear across all sources, indicating strong consensus on these topics."
        })
    
    if reddit_youtube_common:
        correlations.append({
            "type": "reddit_youtube",
            "keywords": list(reddit_youtube_common),
            "insight": "Reddit discussions align with trending YouTube content on these topics."
        })
    
    if reddit_news_common:
        correlations.append({
            "type": "reddit_news",
            "keywords": list(reddit_news_common),
            "insight": "Reddit community discussions match recent news coverage."
        })
    
    if youtube_news_common:
        correlations.append({
            "type": "youtube_news",
            "keywords": list(youtube_news_common),
            "insight": "YouTube content creators are covering topics that match recent news."
        })
    
    return {
        "correlations": correlations,
        "reddit_themes": reddit_themes,
        "youtube_themes": youtube_themes,
        "news_themes": news_themes,
        "unique_reddit": list(reddit_keywords - youtube_keywords - news_keywords),
        "unique_youtube": list(youtube_keywords - reddit_keywords - news_keywords),
        "unique_news": list(news_keywords - reddit_keywords - youtube_keywords),
    }


def generate_ai_powered_summary(
    ranked_items: Dict[str, List[Dict[str, Any]]],
    themes: Dict[str, Dict[str, Any]],
    sentiment: Dict[str, Dict[str, Any]],
    trends: Dict[str, Dict[str, Any]],
    correlations: Dict[str, Any],
    topic: str
) -> str:
    """
    Generate AI-powered context summary using Groq API.
    
    Args:
        ranked_items: Dictionary with ranked items from each source
        themes: Theme extraction results from each source
        sentiment: Sentiment analysis from each source
        trends: Trend detection results from each source
        correlations: Cross-source correlation results
        topic: The search topic
        
    Returns:
        AI-generated intelligent summary string
    """
    try:
        import requests
        from ..config import config
        
        # Check if OpenRouter is available
        if not config.validate_openrouter_config():
            # Fallback to rule-based summary if OpenRouter not available
            return None
        
        # Prepare data for AI analysis
        analysis_data = {
            "topic": topic,
            "reddit_summary": {
                "top_items": [item.get("title", "") for item in ranked_items.get("reddit", [])[:3]],
                "themes": themes.get("reddit", {}).get("top_keywords", [])[:10],
                "sentiment": sentiment.get("reddit", {}).get("sentiment", "neutral"),
                "emerging_trends": [t.get("title", "") for t in trends.get("reddit", {}).get("emerging_trends", [])[:3]],
                "gaining_traction": [t.get("title", "") for t in trends.get("reddit", {}).get("gaining_traction", [])[:3]]
            },
            "youtube_summary": {
                "top_items": [item.get("title", "") for item in ranked_items.get("youtube", [])[:3]],
                "themes": themes.get("youtube", {}).get("top_keywords", [])[:10],
                "sentiment": sentiment.get("youtube", {}).get("sentiment", "neutral"),
                "emerging_trends": [t.get("title", "") for t in trends.get("youtube", {}).get("emerging_trends", [])[:3]],
                "gaining_traction": [t.get("title", "") for t in trends.get("youtube", {}).get("gaining_traction", [])[:3]]
            },
            "news_summary": {
                "top_items": [item.get("title", "") for item in ranked_items.get("news", [])[:3]],
                "themes": themes.get("news", {}).get("top_keywords", [])[:10],
                "sentiment": sentiment.get("news", {}).get("sentiment", "neutral"),
                "emerging_trends": [t.get("title", "") for t in trends.get("news", {}).get("emerging_trends", [])[:3]],
                "gaining_traction": [t.get("title", "") for t in trends.get("news", {}).get("gaining_traction", [])[:3]]
            },
            "correlations": [
                corr.get("insight", "") for corr in correlations.get("correlations", [])[:3]
            ],
            "unique_angles": []
        }
        
        # Add unique angles from all sources
        for source in ["reddit", "youtube", "news"]:
            unique = trends.get(source, {}).get("unique_angles", [])
            analysis_data["unique_angles"].extend([ua.get("title", "") for ua in unique[:2]])
        
        # Create prompt for AI analysis
        prompt = f"""Analyze the following trending topics data about "{topic}" and generate a comprehensive, intelligent summary.

DATA SUMMARY:
{json.dumps(analysis_data, indent=2)}

Your task:
1. Identify the key insights and trends
2. Highlight what's gaining traction vs what's stable
3. Find unique angles or perspectives that others might miss
4. Summarize cross-source correlations
5. Provide actionable insights for content creation

Generate a concise but comprehensive summary (300-500 words) that:
- Starts with the most important trends and insights
- Highlights emerging topics that are gaining momentum
- Identifies unique angles or niche perspectives
- Explains cross-source connections
- Provides clear takeaways for content creators

IMPORTANT: Focus on the CONTENT and themes themselves. Minimize or avoid explicit mentions of the platforms 
(Reddit, YouTube, News) - instead, describe what people are discussing, what's trending, and why it matters.
The summary should read as insights about the topic, not as a report about social media activity.

Output ONLY the summary text, no meta-commentary or explanations."""
    
        # Call OpenRouter API
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.openrouter_model,
                "messages": [
                    {"role": "system", "content": "You are an expert content analyst who identifies trends and insights from social media, video platforms, and news sources."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.7
            },
            timeout=30
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("choices") and data["choices"][0].get("message", {}).get("content"):
            return data["choices"][0]["message"]["content"].strip()
        else:
            return None
            
    except Exception as e:
        # If AI summary fails, return None to fall back to rule-based
        print(f"Warning: AI-powered summary generation failed: {str(e)}")
        return None


def create_context_summary(
    ideas_data: Dict[str, Any],
    topic: str,
    top_n_per_source: int = 5,
    use_ai_summary: bool = True
) -> str:
    """
    Create intelligent, structured context summary for script generation.
    
    Args:
        ideas_data: Output from generate_ideas()
        topic: The search topic
        top_n_per_source: Number of top items to include per source
        use_ai_summary: Whether to use AI-powered summary (default: True, falls back to rule-based if unavailable)
        
    Returns:
        Formatted context string for AI prompt
    """
    # Get items from each source
    reddit_items = ideas_data.get("sources", {}).get("reddit", {}).get("items", [])
    youtube_items = ideas_data.get("sources", {}).get("youtube", {}).get("items", [])
    news_items = ideas_data.get("sources", {}).get("google_news", {}).get("items", [])
    
    # Rank and filter items
    ranked_reddit = rank_and_filter_items(reddit_items, topic, "reddit", top_n_per_source)
    ranked_youtube = rank_and_filter_items(youtube_items, topic, "youtube", top_n_per_source)
    ranked_news = rank_and_filter_items(news_items, topic, "google_news", top_n_per_source)
    
    # Extract themes
    reddit_themes = extract_themes(ranked_reddit, "reddit")
    youtube_themes = extract_themes(ranked_youtube, "youtube")
    news_themes = extract_themes(ranked_news, "google_news")
    
    # Analyze sentiment
    reddit_sentiment = analyze_sentiment(ranked_reddit, "reddit")
    youtube_sentiment = analyze_sentiment(ranked_youtube, "youtube")
    news_sentiment = analyze_sentiment(ranked_news, "google_news")
    
    # Detect trends
    reddit_trends = detect_trends(ranked_reddit, "reddit")
    youtube_trends = detect_trends(ranked_youtube, "youtube")
    news_trends = detect_trends(ranked_news, "google_news")
    
    # Find correlations
    correlations = find_cross_source_correlations(ranked_reddit, ranked_youtube, ranked_news)
    
    # Try AI-powered summary first if enabled
    if use_ai_summary:
        ai_summary = generate_ai_powered_summary(
            ranked_items={
                "reddit": ranked_reddit,
                "youtube": ranked_youtube,
                "news": ranked_news
            },
            themes={
                "reddit": reddit_themes,
                "youtube": youtube_themes,
                "news": news_themes
            },
            sentiment={
                "reddit": reddit_sentiment,
                "youtube": youtube_sentiment,
                "news": news_sentiment
            },
            trends={
                "reddit": reddit_trends,
                "youtube": youtube_trends,
                "news": news_trends
            },
            correlations=correlations,
            topic=topic
        )
        
        if ai_summary:
            # Combine AI summary with structured data
            summary = f"TRENDING TOPICS ANALYSIS: {topic}\n"
            summary += "=" * 70 + "\n\n"
            summary += "AI-GENERATED INTELLIGENT SUMMARY:\n"
            summary += "-" * 70 + "\n"
            summary += ai_summary
            summary += "\n\n" + "=" * 70 + "\n\n"
            summary += "DETAILED BREAKDOWN:\n\n"
        else:
            # Fall back to rule-based summary
            summary = ""
    else:
        summary = ""
    
    # Build structured summary (rule-based or as supplement to AI summary)
    if not use_ai_summary or not ai_summary:
        summary = f"TRENDING TOPICS ANALYSIS: {topic}\n"
        summary += "=" * 70 + "\n\n"
    
    # Key Themes
    all_keywords = set()
    all_keywords.update(reddit_themes.get("top_keywords", []))
    all_keywords.update(youtube_themes.get("top_keywords", []))
    all_keywords.update(news_themes.get("top_keywords", []))
    
    summary += f"KEY THEMES & KEYWORDS:\n"
    summary += f"- Top trending keywords: {', '.join(list(all_keywords)[:10])}\n"
    if correlations.get("correlations"):
        summary += f"- Cross-source correlations found: {len(correlations['correlations'])} connections\n"
    summary += "\n"
    
    # Trend Analysis
    summary += "TREND ANALYSIS:\n"
    summary += "-" * 70 + "\n"
    
    # Emerging Trends
    all_emerging = []
    all_emerging.extend(reddit_trends.get("emerging_trends", [])[:2])
    all_emerging.extend(youtube_trends.get("emerging_trends", [])[:2])
    all_emerging.extend(news_trends.get("emerging_trends", [])[:2])
    if all_emerging:
        summary += "🌱 EMERGING TRENDS (New topics gaining attention):\n"
        for trend in all_emerging[:5]:
            summary += f"- {trend.get('title', '')}\n"
        summary += "\n"
    
    # Gaining Traction
    all_gaining = []
    all_gaining.extend(reddit_trends.get("gaining_traction", [])[:2])
    all_gaining.extend(youtube_trends.get("gaining_traction", [])[:2])
    all_gaining.extend(news_trends.get("gaining_traction", [])[:2])
    if all_gaining:
        summary += "📈 GAINING TRACTION (Rapidly growing topics):\n"
        for trend in all_gaining[:5]:
            summary += f"- {trend.get('title', '')}\n"
        summary += "\n"
    
    # Unique Angles
    all_unique = []
    all_unique.extend(reddit_trends.get("unique_angles", [])[:2])
    all_unique.extend(youtube_trends.get("unique_angles", [])[:2])
    all_unique.extend(news_trends.get("unique_angles", [])[:2])
    if all_unique:
        summary += "💡 UNIQUE ANGLES (Niche perspectives worth exploring):\n"
        for angle in all_unique[:5]:
            summary += f"- {angle.get('title', '')}\n"
            if angle.get('insight'):
                summary += f"  {angle.get('insight', '')}\n"
        summary += "\n"
    
    # Reddit Insights
    if ranked_reddit:
        summary += "REDDIT DISCUSSIONS (Community Insights):\n"
        for i, item in enumerate(ranked_reddit[:3], 1):
            summary += f"{i}. {item.get('title', '')}\n"
            if item.get('selftext'):
                summary += f"   Content: {item.get('selftext', '')[:150]}...\n"
            if item.get('top_comments'):
                top_comment = item['top_comments'][0]
                summary += f"   Top comment: \"{top_comment.get('text', '')[:100]}...\" ({top_comment.get('score', 0)} upvotes)\n"
            summary += f"   Engagement: {item.get('score', 0)} upvotes, {item.get('num_comments', 0)} comments\n"
            summary += f"   Subreddit: r/{item.get('subreddit', '')}\n"
        summary += f"Sentiment: {reddit_sentiment.get('sentiment', 'neutral')}\n\n"
    
    # YouTube Insights
    if ranked_youtube:
        summary += "YOUTUBE TRENDING VIDEOS (Popular Content):\n"
        for i, item in enumerate(ranked_youtube[:3], 1):
            summary += f"{i}. {item.get('title', '')}\n"
            if item.get('description'):
                summary += f"   About: {item.get('description', '')[:150]}...\n"
            summary += f"   Views: {item.get('view_count', 0):,} | Engagement: {item.get('engagement_ratio', 0):.2f}%\n"
            summary += f"   Channel: {item.get('channel_title', 'Unknown')}\n"
            if item.get('tags'):
                summary += f"   Tags: {', '.join(item.get('tags', [])[:5])}\n"
        summary += f"Sentiment: {youtube_sentiment.get('sentiment', 'neutral')}\n\n"
    
    # News Insights
    if ranked_news:
        summary += "RECENT NEWS (Current Events):\n"
        for i, item in enumerate(ranked_news[:3], 1):
            summary += f"{i}. {item.get('title', '')}\n"
            if item.get('description'):
                summary += f"   Summary: {item.get('description', '')[:150]}...\n"
            summary += f"   Source: {item.get('source', 'Unknown')}"
            if item.get('is_major_outlet'):
                summary += " (Major Outlet)"
            summary += "\n"
            if item.get('age_hours'):
                summary += f"   Published: {item.get('age_hours', 0):.1f} hours ago\n"
        summary += f"Sentiment: {news_sentiment.get('sentiment', 'neutral')}\n\n"
    
    # Cross-source Correlations
    if correlations.get("correlations"):
        summary += "CROSS-SOURCE INSIGHTS:\n"
        for corr in correlations["correlations"][:3]:
            summary += f"- {corr.get('insight', '')}\n"
            summary += f"  Keywords: {', '.join(corr.get('keywords', [])[:5])}\n"
        summary += "\n"
    
    # Overall Sentiment
    sentiments = [reddit_sentiment.get('sentiment'), youtube_sentiment.get('sentiment'), news_sentiment.get('sentiment')]
    overall_sentiment = max(set(sentiments), key=sentiments.count) if sentiments else "neutral"
    summary += f"OVERALL SENTIMENT: {overall_sentiment}\n"
    
    return summary

