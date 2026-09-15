"""Query analysis engine for understanding user intent and context needs."""

import json
import re
from typing import Dict, List, Any, Optional
import requests

from ..config import config


# Query analysis system prompt
QUERY_ANALYSIS_SYSTEM_PROMPT = """You are an expert query analyzer for a content creation MCP server.

Analyze the user's query and determine:
1. Intent: What does the user want? Choose from: trending_topics, script_generation, video_creation, voice_cloning, audio_generation, general_query
2. Topics: What subjects are mentioned? Extract all topics/subjects
3. Context Needs: What external data is needed? Choose from: reddit, youtube, news, all, none
4. Implicit Requirements: Duration (in seconds), style, voice preferences, video preferences, etc.

Return ONLY valid JSON with this exact structure:
{
    "intent": "trending_topics",
    "topics": ["AI", "machine learning"],
    "context_sources": ["reddit", "youtube", "news"],
    "requirements": {
        "duration": 60,
        "style": "informative",
        "voice_name": null,
        "video_path": null
    },
    "confidence": 0.95
}

Intent types:
- trending_topics: User wants to know what's trending, current events, what's happening
- script_generation: User wants to generate a script or monologue
- video_creation: User wants to create a video
- voice_cloning: User wants to clone a voice
- audio_generation: User wants to generate audio
- general_query: General question that might need context

Context sources:
- reddit: Need Reddit data
- youtube: Need YouTube data
- news: Need news data
- all: Need all sources
- none: No external context needed
"""


def analyze_query_intent(query: str, use_ai: bool = True) -> Dict[str, Any]:
    """
    Analyze a user query to determine intent, topics, and context needs.
    
    Args:
        query: The user's query string
        use_ai: Whether to use AI for analysis (default: True, falls back to rule-based)
    
    Returns:
        Dictionary with:
        - intent: One of trending_topics, script_generation, video_creation, voice_cloning, audio_generation, general_query
        - topics: List of extracted topics
        - context_sources: List of required sources (reddit, youtube, news, all, none)
        - requirements: Dict with duration, style, voice_name, video_path, etc.
        - confidence: Confidence score (0.0 to 1.0)
    """
    # Always try AI first if OpenRouter is configured
    if use_ai:
        if config.validate_openrouter_config():
            try:
                return _analyze_with_ai(query)
            except Exception as e:
                print(f"Warning: AI query analysis failed: {str(e)}, falling back to rule-based")
        else:
            print("Warning: OpenRouter API key not configured, using rule-based analysis")
    
    # Fallback to rule-based analysis
    return _analyze_with_rules(query)


def _analyze_with_ai(query: str) -> Dict[str, Any]:
    """Analyze query using AI (OpenRouter only)."""
    # Use OpenRouter for query analysis
    if not config.validate_openrouter_config():
        raise Exception("OpenRouter API key not configured")
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {config.openrouter_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": config.openrouter_model,
                "messages": [
                    {"role": "system", "content": QUERY_ANALYSIS_SYSTEM_PROMPT + "\n\nIMPORTANT: Return ONLY valid JSON, no other text."},
                    {"role": "user", "content": f'Analyze this query: "{query}"'}
                ],
                "temperature": 0.3
            },
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        
        if data.get("choices") and data["choices"][0].get("message", {}).get("content"):
            content = data["choices"][0]["message"]["content"].strip()
            # Try to extract JSON if wrapped in markdown code blocks
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()
            result = json.loads(content)
            return _normalize_analysis_result(result, query)
        else:
            raise Exception("No content in OpenRouter response")
    except Exception as e:
        print(f"OpenRouter analysis failed: {str(e)}")
        raise Exception(f"AI analysis failed: {str(e)}, falling back to rules")


def _analyze_with_rules(query: str) -> Dict[str, Any]:
    """Fallback rule-based query analysis."""
    query_lower = query.lower()
    
    # Determine intent
    intent = "general_query"
    if any(word in query_lower for word in ["trending", "what's happening", "current", "latest", "news", "what's going on"]):
        intent = "trending_topics"
    elif any(word in query_lower for word in ["script", "monologue", "write", "content"]):
        intent = "script_generation"
    elif any(word in query_lower for word in ["video", "talking head", "d-id"]):
        intent = "video_creation"
    elif any(word in query_lower for word in ["voice", "clone", "mimic"]):
        intent = "voice_cloning"
    elif any(word in query_lower for word in ["audio", "speech", "tts"]):
        intent = "audio_generation"
    
    # Extract topics (simple keyword extraction)
    topics = extract_topics(query)
    
    # Determine context sources
    context_sources = ["reddit", "youtube", "news"]  # Default to all sources
    if intent == "trending_topics":
        context_sources = ["reddit", "youtube", "news"]
    elif intent == "script_generation":
        context_sources = ["reddit", "youtube", "news"]  # Scripts need all sources for context
    elif intent in ["voice_cloning", "audio_generation"]:
        context_sources = ["none"]  # Don't need external context
    elif intent == "video_creation":
        context_sources = ["reddit", "youtube", "news"]  # Videos need trends for content
    
    # Extract requirements
    requirements = detect_implicit_requirements(query)
    
    return {
        "intent": intent,
        "topics": topics,
        "context_sources": context_sources,
        "requirements": requirements,
        "confidence": 0.7  # Lower confidence for rule-based
    }


def extract_topics(query: str) -> List[str]:
    """
    Extract topics/subjects from a query.
    
    Args:
        query: The user's query
    
    Returns:
        List of extracted topics
    """
    # Remove common stop words
    stop_words = {"what", "is", "are", "the", "a", "an", "about", "for", "to", "with", "how", "when", "where", "why"}
    
    # Simple extraction: look for capitalized words or quoted phrases
    topics = []
    
    # Extract quoted strings
    quoted = re.findall(r'"([^"]+)"', query)
    topics.extend(quoted)
    
    # Extract capitalized words/phrases (likely proper nouns or important terms)
    words = query.split()
    current_topic = []
    for word in words:
        # Remove punctuation
        clean_word = re.sub(r'[^\w\s]', '', word)
        if clean_word and clean_word.lower() not in stop_words:
            if clean_word[0].isupper() or len(clean_word) > 4:
                current_topic.append(clean_word)
            else:
                if current_topic:
                    topics.append(" ".join(current_topic))
                    current_topic = []
    
    if current_topic:
        topics.append(" ".join(current_topic))
    
    # If no topics found, try to extract meaningful phrases
    if not topics:
        # Look for common topic patterns
        topic_patterns = [
            r'(?:about|on|regarding)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)',  # Multi-word capitalized phrases
        ]
        for pattern in topic_patterns:
            matches = re.findall(pattern, query)
            topics.extend(matches)
    
    # Clean and deduplicate
    topics = [t.strip() for t in topics if len(t.strip()) > 2]
    topics = list(set(topics))
    
    # If still no topics, use the query itself (limited)
    if not topics:
        # Take first few meaningful words
        words = [w for w in query.split() if w.lower() not in stop_words and len(w) > 2]
        if words:
            topics.append(" ".join(words[:3]))
    
    return topics[:5]  # Limit to 5 topics


def detect_implicit_requirements(query: str) -> Dict[str, Any]:
    """
    Detect implicit requirements from query (duration, style, etc.).
    
    Args:
        query: The user's query
    
    Returns:
        Dictionary with detected requirements
    """
    query_lower = query.lower()
    requirements = {
        "duration": None,
        "style": None,
        "voice_name": None,
        "video_path": None
    }
    
    # Extract duration
    duration_patterns = [
        r'(\d+)\s*(?:second|sec|minute|min)',
        r'(\d+)\s*s(?:ec)?',
        r'(\d+)\s*m(?:in)?',
        r'for\s+(\d+)',
    ]
    for pattern in duration_patterns:
        match = re.search(pattern, query_lower)
        if match:
            duration = int(match.group(1))
            # Convert minutes to seconds
            if "min" in match.group(0) or "minute" in query_lower[match.start():match.end()+10]:
                duration *= 60
            requirements["duration"] = duration
            break
    
    # Extract style
    style_keywords = {
        "informative": ["informative", "educational", "factual"],
        "engaging": ["engaging", "exciting", "captivating"],
        "funny": ["funny", "humorous", "comedy"],
        "serious": ["serious", "formal", "professional"],
        "casual": ["casual", "relaxed", "conversational"],
    }
    for style, keywords in style_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            requirements["style"] = style
            break
    
    # Extract voice name (look for quoted strings or "voice" + name)
    voice_match = re.search(r'voice["\s]+(?:named|called|is)?["\s]*([A-Za-z_][A-Za-z0-9_]*)', query)
    if voice_match:
        requirements["voice_name"] = voice_match.group(1)
    
    # Extract video path (look for file paths)
    path_match = re.search(r'([/\\][\w/\\]+\.(?:mp4|mov|avi))', query)
    if path_match:
        requirements["video_path"] = path_match.group(1)
    
    return requirements


def determine_context_needs(intent: str, topics: List[str]) -> Dict[str, Any]:
    """
    Determine what context is needed based on intent and topics.
    
    Args:
        intent: The detected intent
        topics: List of extracted topics
    
    Returns:
        Dictionary with context needs:
        - sources: List of sources to fetch from
        - should_fetch: Whether to automatically fetch context
        - limit: Number of items per source
    """
    # Default context needs
    needs = {
        "sources": [],
        "should_fetch": False,
        "limit": 5
    }
    
    if intent == "trending_topics":
        needs["sources"] = ["reddit", "youtube", "news"]
        needs["should_fetch"] = True
        needs["limit"] = 10
    elif intent == "script_generation":
        needs["sources"] = ["reddit", "youtube", "news"]
        needs["should_fetch"] = True
        needs["limit"] = 5  # Fewer items for scripts (focus on quality)
    elif intent == "video_creation":
        needs["sources"] = ["reddit", "youtube", "news"]
        needs["should_fetch"] = True
        needs["limit"] = 5
    elif intent in ["voice_cloning", "audio_generation"]:
        needs["sources"] = []
        needs["should_fetch"] = False
    else:
        # General query - might need context if topics are mentioned
        if topics:
            needs["sources"] = ["reddit", "youtube", "news"]
            needs["should_fetch"] = True
            needs["limit"] = 3
    
    return needs


def _normalize_analysis_result(result: Dict[str, Any], query: str) -> Dict[str, Any]:
    """Normalize and validate AI analysis result."""
    # Ensure all required fields exist
    normalized = {
        "intent": result.get("intent", "general_query"),
        "topics": result.get("topics", extract_topics(query)),
        "context_sources": result.get("context_sources", ["all"]),
        "requirements": result.get("requirements", {}),
        "confidence": result.get("confidence", 0.8)
    }
    
    # Validate intent
    valid_intents = ["trending_topics", "script_generation", "video_creation", "voice_cloning", "audio_generation", "general_query"]
    if normalized["intent"] not in valid_intents:
        normalized["intent"] = "general_query"
    
    # Validate context sources
    valid_sources = ["reddit", "youtube", "news", "all", "none"]
    normalized["context_sources"] = [s for s in normalized["context_sources"] if s in valid_sources]
    
    # Override context sources based on intent if AI returned incorrect ones
    # Scripts and trending topics ALWAYS need context
    if normalized["intent"] in ["trending_topics", "script_generation", "video_creation"]:
        if "none" in normalized["context_sources"] or not normalized["context_sources"]:
            # Override: these intents need context
            normalized["context_sources"] = ["reddit", "youtube", "news"]
    elif normalized["intent"] in ["voice_cloning", "audio_generation"]:
        # These don't need external context
        normalized["context_sources"] = ["none"]
    
    # Final fallback
    if not normalized["context_sources"]:
        normalized["context_sources"] = ["reddit", "youtube", "news"]
    
    # Ensure topics is a list
    if not isinstance(normalized["topics"], list):
        if isinstance(normalized["topics"], str):
            normalized["topics"] = [normalized["topics"]]
        else:
            normalized["topics"] = extract_topics(query)
    
    # Ensure requirements is a dict
    if not isinstance(normalized["requirements"], dict):
        normalized["requirements"] = detect_implicit_requirements(query)
    else:
        # Merge with rule-based requirements to fill gaps
        rule_requirements = detect_implicit_requirements(query)
        normalized["requirements"] = {**rule_requirements, **normalized["requirements"]}
    
    # Validate confidence
    if not isinstance(normalized["confidence"], (int, float)) or not (0 <= normalized["confidence"] <= 1):
        normalized["confidence"] = 0.8
    
    return normalized

