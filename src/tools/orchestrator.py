"""
Smart orchestrator tool that handles natural language queries.
Takes any query, analyzes it, and executes the appropriate workflow.
"""
import json
from typing import Any, Dict

from ..utils.query_analyzer import analyze_query_intent
from .ideas import generate_ideas
from .script import generate_complete_script
from .voice import generate_audio_from_script, generate_script_with_audio, generate_complete_content
from .video import generate_video_from_image_audio, generate_video_from_video, generate_complete_video


def process_natural_query(query: str) -> Dict[str, Any]:
    """
    Master orchestrator: Takes a natural language query and executes the complete workflow.
    
    This is the "smart" entry point for the MCP server. It:
    1. Analyzes the query to understand intent
    2. Determines what actions are needed
    3. Orchestrates internal tool calls
    4. Returns the final result
    
    Args:
        query: Natural language query from user
        
    Returns:
        Dict with the final result and metadata
        
    Examples:
        - "What's trending about AI?" → Returns trending topics
        - "Generate a 30 sec script about Pluribus Reactions" → Returns script
        - "Create content about AI using my 'test' voice" → Returns audio file
    """
    try:
        # Step 1: Analyze the query
        analysis = analyze_query_intent(query)
        
        intent = analysis.get("intent")
        topics = analysis.get("topics", [])
        requirements = analysis.get("requirements", {})
        
        result = {
            "query": query,
            "analysis": analysis,
            "intent": intent,
            "topics": topics,
            "requirements": requirements
        }
        
        # Step 2: Execute based on intent
        if intent == "trending_topics":
            # User wants to know what's trending
            if not topics:
                return {
                    **result,
                    "error": "No topic specified. Please provide a topic.",
                    "success": False
                }
            
            topic = topics[0]
            limit = requirements.get("limit", 5)
            
            trending_data = generate_ideas(topic=topic, limit=limit)
            
            return {
                **result,
                "success": True,
                "data": trending_data,
                "message": f"Retrieved {limit} trending topics about '{topic}'"
            }
        
        elif intent == "script_generation":
            # User wants a script
            if not topics:
                return {
                    **result,
                    "error": "No topic specified. Please provide a topic.",
                    "success": False
                }
            
            # Combine multiple topics if present (e.g., "Pluribus Reactions")
            topic = " ".join(topics[:2]) if len(topics) > 1 else topics[0]
            duration = requirements.get("duration", 60)
            style = requirements.get("style", "informative and engaging")
            
            script_data = generate_complete_script(
                topic=topic,
                duration_seconds=duration,
                style=style
            )
            
            return {
                **result,
                "success": True,
                "data": script_data,
                "message": f"Generated {duration}-second script about '{topic}'"
            }
        
        elif intent == "audio_generation":
            # User wants audio (with or without voice cloning)
            video_path = requirements.get("video_path")
            voice_name = requirements.get("voice_name")
            voice_id = requirements.get("voice_id")
            script = requirements.get("script")
            
            if not topics and not script:
                return {
                    **result,
                    "error": "No topic or script specified.",
                    "success": False
                }
            
            # If they have a script already
            if script:
                audio_data = generate_audio_from_script(
                    script=script,
                    video_path=video_path,
                    voice_name=voice_name,
                    voice_id=voice_id
                )
                return {
                    **result,
                    "success": True,
                    "data": audio_data,
                    "message": "Generated audio from script"
                }
            
            # If they want script + audio
            elif topics:
                topic = " ".join(topics[:2]) if len(topics) > 1 else topics[0]
                duration = requirements.get("duration", 60)
                style = requirements.get("style", "informative and engaging")
                
                if video_path or voice_name or voice_id:
                    # Generate script and audio with voice cloning/reuse
                    audio_data = generate_script_with_audio(
                        topic=topic,
                        duration_seconds=duration,
                        style=style,
                        video_path=video_path,
                        voice_name=voice_name,
                        voice_id=voice_id
                    )
                else:
                    # Full workflow: ideas → script → audio
                    audio_data = generate_complete_content(
                        subject=topic,
                        video_path=video_path,
                        voice_name=voice_name,
                        voice_id=voice_id,
                        duration_seconds=duration,
                        style=style
                    )
                
                return {
                    **result,
                    "success": True,
                    "data": audio_data,
                    "message": f"Generated audio content about '{topic}'"
                }
        
        elif intent == "video_creation":
            # User wants a video
            video_path = requirements.get("video_path")
            image_path = requirements.get("image_path")
            audio_path = requirements.get("audio_path")
            script = requirements.get("script")
            
            # If they have image + audio already
            if image_path and audio_path:
                video_data = generate_video_from_image_audio(
                    image_path=image_path,
                    audio_path=audio_path
                )
                return {
                    **result,
                    "success": True,
                    "data": video_data,
                    "message": "Generated video from image and audio"
                }
            
            # If they have a video (for voice cloning) + script or topic
            elif video_path:
                if not topics and not script:
                    return {
                        **result,
                        "error": "Need either a topic or script to generate video content.",
                        "success": False
                    }
                
                if script:
                    # Video + script → talking head video
                    video_data = generate_video_from_video(
                        video_path=video_path,
                        script=script
                    )
                else:
                    # Full workflow: topic → script → audio → video
                    topic = " ".join(topics[:2]) if len(topics) > 1 else topics[0]
                    duration = requirements.get("duration", 60)
                    style = requirements.get("style", "informative and engaging")
                    voice_name = requirements.get("voice_name")
                    
                    video_data = generate_complete_video(
                        video_path=video_path,
                        topic=topic,
                        duration_seconds=duration,
                        style=style,
                        voice_name=voice_name
                    )
                
                return {
                    **result,
                    "success": True,
                    "data": video_data,
                    "message": f"Generated video content"
                }
            
            else:
                return {
                    **result,
                    "error": "Need either (image + audio) or (video + topic/script) to generate video.",
                    "success": False
                }
        
        elif intent == "voice_cloning":
            # User wants to clone a voice
            video_path = requirements.get("video_path")
            voice_name = requirements.get("voice_name", "cloned_voice")
            
            if not video_path:
                return {
                    **result,
                    "error": "Need a video file to clone voice from.",
                    "success": False
                }
            
            # Clone voice (will be done as part of audio generation)
            return {
                **result,
                "success": True,
                "message": f"To clone voice, use audio/video generation with video_path parameter.",
                "hint": "Try: 'Generate audio about [topic] using [video_path] as voice sample'"
            }
        
        else:
            # Unknown intent
            return {
                **result,
                "success": False,
                "error": f"Could not determine how to handle query with intent: {intent}",
                "suggestion": "Try being more specific, e.g., 'Generate a script about X' or 'What's trending about Y?'"
            }
    
    except Exception as e:
        return {
            "query": query,
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__
        }

