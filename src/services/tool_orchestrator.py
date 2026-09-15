"""Tool orchestration service for intelligent tool chaining."""

from typing import Dict, List, Any, Optional
from ..utils.query_analyzer import analyze_query_intent, determine_context_needs


def orchestrate_complete_workflow(
    intent: str,
    topics: List[str],
    requirements: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Determine the optimal tool sequence for a complete workflow.
    
    Args:
        intent: Query intent
        topics: List of topics
        requirements: Detected requirements (duration, style, etc.)
    
    Returns:
        Dictionary with recommended tool sequence and parameters
    """
    orchestration = {
        "tool_sequence": [],
        "parameters": {},
        "auto_context": True
    }
    
    if intent == "trending_topics":
        # For trending queries, use prompts or resources (no tool calls needed)
        orchestration["tool_sequence"] = []
        orchestration["recommendation"] = "Use 'trending_analysis' prompt or 'trending://topics/{topic}' resource"
        orchestration["auto_context"] = True
    
    elif intent == "script_generation":
        # For script generation, use composite tool that does everything
        orchestration["tool_sequence"] = ["generate_complete_script"]
        orchestration["parameters"] = {
            "topic": topics[0] if topics else "general",
            "duration_seconds": requirements.get("duration", 60),
            "style": requirements.get("style", "informative and engaging")
        }
        orchestration["auto_context"] = True
        orchestration["note"] = "This tool automatically fetches trends internally"
    
    elif intent == "video_creation":
        # For video creation, use complete video tool
        orchestration["tool_sequence"] = ["generate_complete_video"]
        orchestration["parameters"] = {
            "topic": topics[0] if topics else "general",
            "duration_seconds": requirements.get("duration", 60),
            "video_path": requirements.get("video_path"),
            "style": requirements.get("style", "informative and engaging")
        }
        orchestration["auto_context"] = True
        orchestration["note"] = "This tool automatically fetches trends, generates script, and creates video"
    
    elif intent == "voice_cloning":
        # For voice cloning, use audio generation tool
        orchestration["tool_sequence"] = ["generate_audio_from_script"]
        orchestration["parameters"] = {
            "video_path": requirements.get("video_path"),
            "voice_name": requirements.get("voice_name")
        }
        orchestration["auto_context"] = False  # No external context needed
    
    else:
        # General query - recommend using prompts/resources
        orchestration["tool_sequence"] = []
        orchestration["recommendation"] = "Use 'query_with_context' prompt for automatic context injection"
        orchestration["auto_context"] = True
    
    return orchestration


def should_chain_tools(intent: str) -> bool:
    """
    Determine if tools should be chained for this intent.
    
    Args:
        intent: Query intent
    
    Returns:
        True if tools should be chained, False if composite tool should be used
    """
    # For most intents, we use composite tools that do everything
    # Only chain if explicitly needed (which we don't do in this implementation)
    return False


def get_recommended_approach(intent: str, topics: List[str]) -> str:
    """
    Get recommended approach (prompt, resource, or tool) for an intent.
    
    Args:
        intent: Query intent
        topics: List of topics
    
    Returns:
        Recommended approach description
    """
    if intent == "trending_topics":
        topic = topics[0] if topics else "{topic}"
        return f"Use 'trending_analysis' prompt with topic='{topic}' OR read resource 'trending://topics/{topic}'"
    
    elif intent == "script_generation":
        return "Use 'script_generation' prompt OR call 'generate_complete_script' tool (auto-fetches context)"
    
    elif intent == "video_creation":
        return "Use 'generate_complete_video' tool (auto-fetches context and does everything)"
    
    elif intent == "voice_cloning":
        return "Use 'generate_audio_from_script' tool"
    
    else:
        return "Use 'query_with_context' prompt for automatic context injection"

