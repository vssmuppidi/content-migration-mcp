"""Voice generation tools combining script generation with ElevenLabs voice cloning."""

import os
import re
import tempfile
from typing import Dict, Any, Optional, List
from .script import generate_complete_script, generate_script_from_ideas
from ..utils.audio import extract_audio_from_video, validate_audio_file, cleanup_temp_audio
from ..sources.elevenlabs_voice import ElevenLabsVoice


def sanitize_filename(text: str) -> str:
    """
    Sanitize text for use in filenames by removing special characters.
    
    Args:
        text: Text to sanitize
        
    Returns:
        Sanitized text safe for filenames
    """
    # Remove or replace special characters
    text = re.sub(r'[^\w\s-]', '', text)  # Remove anything not alphanumeric, space, dash, or underscore
    text = re.sub(r'[-\s]+', '_', text)    # Replace spaces and dashes with underscore
    text = text.strip('_')                  # Remove leading/trailing underscores
    return text


def generate_complete_content(
    topic: str,
    duration_seconds: int,
    video_path: Optional[str] = None,
    provider: Optional[str] = None,
    style: Optional[str] = "informative and engaging",
    limit: int = 3,
    model: Optional[str] = None,
    output_audio_path: Optional[str] = None,
    voice_id: Optional[str] = None,
    voice_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Complete workflow: Generate ideas, script, and audio with voice cloning.
    
    This is the most comprehensive tool that handles everything:
    1. Fetches trending topics from Reddit, YouTube, and Google News
    2. Generates a script incorporating those topics
    3. Extracts audio from video sample (if needed)
    4. Clones voice or reuses existing voice
    5. Generates audio
    
    Perfect for agents - complete end-to-end content creation.
    
    Args:
        topic: The topic to research and write about
        duration_seconds: Target duration of the script in seconds
        video_path: Path to video file for voice cloning (optional if voice_id or voice_name provided)
        provider: Inference provider - "groq" or "openrouter" (default: from config)
        style: Script style/tone (default: "informative and engaging")
        limit: Number of items to fetch per source (default: 3)
        model: Model to use (default: from config based on provider)
        output_audio_path: Optional path for output audio (default: temp file)
        voice_id: Optional existing voice ID to reuse (skips cloning)
        voice_name: Optional voice name to search for and reuse (skips cloning if found)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - script: The generated script text
        - audio_path: Path to generated audio file
        - voice_id: ElevenLabs voice ID
        - script_metadata: Script metadata (provider, model, word count, etc.)
        - audio_metadata: Audio generation metadata
        - trending_data: The fetched trending topics data
        - topic: The input topic
        - error: Error message if failed
    """
    temp_audio_sample = None
    
    try:
        # Step 1: Generate script with trending data
        script_result = generate_complete_script(
            topic=topic,
            duration_seconds=duration_seconds,
            provider=provider,
            style=style,
            limit=limit,
            model=model
        )
        
        if not script_result.get("success"):
            return {
                "success": False,
                "error": f"Script generation failed: {script_result.get('error', 'Unknown error')}",
                "script": None,
                "audio_path": None,
                "voice_id": None
            }
        
        script_text = script_result.get("script")
        if not script_text:
            return {
                "success": False,
                "error": "Generated script is empty",
                "script": None,
                "audio_path": None,
                "voice_id": None
            }
        
        # Step 2: Determine voice to use
        voice_service = ElevenLabsVoice()
        use_voice_id = None
        
        if voice_id:
            # Use provided voice_id directly
            use_voice_id = voice_id
        elif voice_name:
            # Search for voice by name
            use_voice_id = voice_service.get_voice_by_name(voice_name)
            if not use_voice_id:
                # Voice not found - need to clone
                if not video_path or not os.path.exists(video_path):
                    return {
                        "success": False,
                        "error": f"Voice '{voice_name}' not found and no valid video_path provided for cloning",
                        "script": script_text,
                        "script_metadata": script_result.get("metadata"),
                        "trending_data": script_result.get("trending_data"),
                        "audio_path": None,
                        "voice_id": None
                    }
        
        # Step 3: Clone voice if needed
        if not use_voice_id:
            # Need to clone voice from video
            if not video_path or not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": f"Video file required for voice cloning: {video_path}",
                    "script": script_text,
                    "script_metadata": script_result.get("metadata"),
                    "trending_data": script_result.get("trending_data"),
                    "audio_path": None,
                    "voice_id": None
                }
            
            temp_audio_sample = extract_audio_from_video(video_path)
            
            # Validate audio
            is_valid, validation_message = validate_audio_file(temp_audio_sample)
            if not is_valid:
                cleanup_temp_audio(temp_audio_sample)
                return {
                    "success": False,
                    "error": f"Audio validation failed: {validation_message}",
                    "script": script_text,
                    "script_metadata": script_result.get("metadata"),
                    "trending_data": script_result.get("trending_data"),
                    "audio_path": None,
                    "voice_id": None
                }
            
            # Clone voice
            try:
                use_voice_id = voice_service.clone_voice_from_audio(temp_audio_sample, voice_name)
            finally:
                cleanup_temp_audio(temp_audio_sample)
        
        # Step 4: Generate output audio path if not provided
        if not output_audio_path:
            output_dir = os.path.join(os.path.dirname(__file__), "../../output/audio")
            os.makedirs(output_dir, exist_ok=True)
            safe_topic = sanitize_filename(topic)[:20]  # Sanitize and limit length
            output_audio_path = os.path.join(
                output_dir,
                f"generated_audio_{safe_topic}_{os.getpid()}.mp3"
            )
        
        # Step 5: Generate audio using voice
        audio_path = voice_service.generate_audio_from_text(
            text=script_text,
            voice_id=use_voice_id,
            output_path=output_audio_path
        )
        
        # Get audio file size
        audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
        
        audio_result = {
            "success": True,
            "voice_id": use_voice_id,
            "audio_path": audio_path,
            "metadata": {
                "audio_size_bytes": audio_size,
                "script_length": len(script_text)
            }
        }
        
        if not audio_result.get("success"):
            return {
                "success": False,
                "error": f"Audio generation failed: {audio_result.get('error', 'Unknown error')}",
                "script": script_text,
                "script_metadata": script_result.get("metadata"),
                "trending_data": script_result.get("trending_data"),
                "audio_path": None,
                "voice_id": None
            }
        
        # Return complete result
        return {
            "success": True,
            "script": script_text,
            "audio_path": audio_result.get("audio_path"),
            "voice_id": audio_result.get("voice_id"),
            "script_metadata": script_result.get("metadata"),
            "audio_metadata": audio_result.get("metadata"),
            "trending_data": script_result.get("trending_data"),
            "topic": topic
        }
        
    except Exception as e:
        # Cleanup on error
        if temp_audio_sample:
            cleanup_temp_audio(temp_audio_sample)
        
        return {
            "success": False,
            "error": f"Error in generate_complete_content: {str(e)}",
            "script": None,
            "audio_path": None,
            "voice_id": None,
            "topic": topic
        }


def generate_script_with_audio(
    ideas_data: Dict[str, Any],
    duration_seconds: int,
    video_path: Optional[str] = None,
    provider: Optional[str] = None,
    style: Optional[str] = "informative and engaging",
    model: Optional[str] = None,
    output_audio_path: Optional[str] = None,
    voice_id: Optional[str] = None,
    voice_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate script from trending data and create audio with voice cloning.
    
    This tool takes trending topics data and:
    1. Generates a script incorporating the topics
    2. Extracts audio from video sample (if needed)
    3. Clones voice or reuses existing voice
    4. Generates audio
    
    Use when you already have trending topics data.
    
    Args:
        ideas_data: Output from generate_ideas() function
        duration_seconds: Target duration of the script in seconds
        video_path: Path to video file for voice cloning (optional if voice_id or voice_name provided)
        provider: Inference provider - "groq" or "openrouter" (default: from config)
        style: Script style/tone (default: "informative and engaging")
        model: Model to use (default: from config based on provider)
        output_audio_path: Optional path for output audio (default: temp file)
        voice_id: Optional existing voice ID to reuse (skips cloning)
        voice_name: Optional voice name to search for and reuse (skips cloning if found)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - script: The generated script text
        - audio_path: Path to generated audio file
        - voice_id: ElevenLabs voice ID
        - script_metadata: Script metadata
        - audio_metadata: Audio generation metadata
        - error: Error message if failed
    """
    temp_audio_sample = None
    
    try:
        # Step 1: Generate script from ideas
        script_result = generate_script_from_ideas(
            ideas_data=ideas_data,
            duration_seconds=duration_seconds,
            provider=provider,
            style=style,
            model=model
        )
        
        if not script_result.get("success"):
            return {
                "success": False,
                "error": f"Script generation failed: {script_result.get('error', 'Unknown error')}",
                "script": None,
                "audio_path": None,
                "voice_id": None
            }
        
        script_text = script_result.get("script")
        if not script_text:
            return {
                "success": False,
                "error": "Generated script is empty",
                "script": None,
                "audio_path": None,
                "voice_id": None
            }
        
        # Step 2: Determine voice to use
        voice_service = ElevenLabsVoice()
        use_voice_id = None
        
        if voice_id:
            # Use provided voice_id directly
            use_voice_id = voice_id
        elif voice_name:
            # Search for voice by name
            use_voice_id = voice_service.get_voice_by_name(voice_name)
            if not use_voice_id:
                # Voice not found - need to clone
                if not video_path or not os.path.exists(video_path):
                    return {
                        "success": False,
                        "error": f"Voice '{voice_name}' not found and no valid video_path provided for cloning",
                        "script": script_text,
                        "script_metadata": script_result.get("metadata"),
                        "audio_path": None,
                        "voice_id": None
                    }
        
        # Step 3: Clone voice if needed
        if not use_voice_id:
            # Need to clone voice from video
            if not video_path or not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": f"Video file required for voice cloning: {video_path}",
                    "script": script_text,
                    "script_metadata": script_result.get("metadata"),
                    "audio_path": None,
                    "voice_id": None
                }
            
            temp_audio_sample = extract_audio_from_video(video_path)
            
            # Validate audio
            is_valid, validation_message = validate_audio_file(temp_audio_sample)
            if not is_valid:
                cleanup_temp_audio(temp_audio_sample)
                return {
                    "success": False,
                    "error": f"Audio validation failed: {validation_message}",
                    "script": script_text,
                    "script_metadata": script_result.get("metadata"),
                    "audio_path": None,
                    "voice_id": None
                }
            
            # Clone voice
            try:
                use_voice_id = voice_service.clone_voice_from_audio(temp_audio_sample, voice_name)
            finally:
                cleanup_temp_audio(temp_audio_sample)
        
        # Step 4: Generate output audio path if not provided
        if not output_audio_path:
            output_dir = os.path.join(os.path.dirname(__file__), "../../output/audio")
            os.makedirs(output_dir, exist_ok=True)
            topic = ideas_data.get("topic", "content")
            safe_topic = sanitize_filename(topic)[:20]  # Sanitize and limit length
            output_audio_path = os.path.join(
                output_dir,
                f"generated_audio_{safe_topic}_{os.getpid()}.mp3"
            )
        
        # Step 5: Generate audio using voice
        audio_path = voice_service.generate_audio_from_text(
            text=script_text,
            voice_id=use_voice_id,
            output_path=output_audio_path
        )
        
        # Get audio file size
        audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
        
        audio_result = {
            "success": True,
            "voice_id": use_voice_id,
            "audio_path": audio_path,
            "metadata": {
                "audio_size_bytes": audio_size,
                "script_length": len(script_text)
            }
        }
        
        if not audio_result.get("success"):
            return {
                "success": False,
                "error": f"Audio generation failed: {audio_result.get('error', 'Unknown error')}",
                "script": script_text,
                "script_metadata": script_result.get("metadata"),
                "audio_path": None,
                "voice_id": None
            }
        
        # Return complete result
        return {
            "success": True,
            "script": script_text,
            "audio_path": audio_result.get("audio_path"),
            "voice_id": audio_result.get("voice_id"),
            "script_metadata": script_result.get("metadata"),
            "audio_metadata": audio_result.get("metadata")
        }
        
    except Exception as e:
        # Cleanup on error
        if temp_audio_sample:
            cleanup_temp_audio(temp_audio_sample)
        
        return {
            "success": False,
            "error": f"Error in generate_script_with_audio: {str(e)}",
            "script": None,
            "audio_path": None,
            "voice_id": None
        }


def generate_audio_from_script(
    script: str,
    video_path: Optional[str] = None,
    output_audio_path: Optional[str] = None,
    voice_id: Optional[str] = None,
    voice_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate audio from a script using voice cloning from video.
    
    This is the simplest tool - just takes a script:
    1. Extracts audio from video sample (if needed)
    2. Clones voice or reuses existing voice
    3. Generates audio from script
    
    Use when you already have a script ready.
    
    Args:
        script: The script text to convert to audio
        video_path: Path to video file for voice cloning (optional if voice_id or voice_name provided)
        output_audio_path: Optional path for output audio (default: temp file)
        voice_id: Optional existing voice ID to reuse (skips cloning)
        voice_name: Optional voice name to search for and reuse (skips cloning if found)
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - audio_path: Path to generated audio file
        - voice_id: ElevenLabs voice ID
        - metadata: Audio generation metadata
        - error: Error message if failed
    """
    try:
        # Validate script
        if not script or not script.strip():
            return {
                "success": False,
                "error": "Script cannot be empty",
                "audio_path": None,
                "voice_id": None
            }
        
        # Step 1: Determine voice to use
        voice_service = ElevenLabsVoice()
        use_voice_id = None
        
        if voice_id:
            # Use provided voice_id directly
            use_voice_id = voice_id
        elif voice_name:
            # Search for voice by name
            use_voice_id = voice_service.get_voice_by_name(voice_name)
            if not use_voice_id:
                # Voice not found - need to clone
                if not video_path or not os.path.exists(video_path):
                    return {
                        "success": False,
                        "error": f"Voice '{voice_name}' not found and no valid video_path provided for cloning",
                        "audio_path": None,
                        "voice_id": None
                    }
        
        # Step 2: Clone voice if needed
        if not use_voice_id:
            # Need to clone voice from video
            if not video_path or not os.path.exists(video_path):
                return {
                    "success": False,
                    "error": f"Video file required for voice cloning: {video_path}",
                    "audio_path": None,
                    "voice_id": None
                }
            
            temp_audio_sample = extract_audio_from_video(video_path)
            
            # Validate audio
            is_valid, validation_message = validate_audio_file(temp_audio_sample)
            if not is_valid:
                cleanup_temp_audio(temp_audio_sample)
                return {
                    "success": False,
                    "error": f"Audio validation failed: {validation_message}",
                    "audio_path": None,
                    "voice_id": None
                }
            
            # Clone voice
            try:
                use_voice_id = voice_service.clone_voice_from_audio(temp_audio_sample, voice_name)
            finally:
                cleanup_temp_audio(temp_audio_sample)
        
        # Step 3: Generate output audio path if not provided
        if not output_audio_path:
            output_dir = os.path.join(os.path.dirname(__file__), "../../output/audio")
            os.makedirs(output_dir, exist_ok=True)
            output_audio_path = os.path.join(
                output_dir,
                f"generated_audio_{os.getpid()}.mp3"
            )
        
        # Step 4: Generate audio using voice
        audio_path = voice_service.generate_audio_from_text(
            text=script,
            voice_id=use_voice_id,
            output_path=output_audio_path
        )
        
        # Get audio file size
        audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
        
        audio_result = {
            "success": True,
            "voice_id": use_voice_id,
            "audio_path": audio_path,
            "metadata": {
                "audio_size_bytes": audio_size,
                "script_length": len(script)
            }
        }
        
        if not audio_result.get("success"):
            return {
                "success": False,
                "error": f"Audio generation failed: {audio_result.get('error', 'Unknown error')}",
                "audio_path": None,
                "voice_id": None
            }
        
        # Return result
        return {
            "success": True,
            "audio_path": audio_result.get("audio_path"),
            "voice_id": audio_result.get("voice_id"),
            "metadata": audio_result.get("metadata")
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error in generate_audio_from_script: {str(e)}",
            "audio_path": None,
            "voice_id": None
        }


def list_all_voices() -> Dict[str, Any]:
    """
    List all voices in the ElevenLabs account.
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if listing succeeded
        - voices: List of voice dictionaries with voice_id, name, category, description
        - count: Number of voices found
        - error: Error message if failed
    """
    try:
        voice_service = ElevenLabsVoice()
        voices = voice_service.list_voices()
        
        return {
            "success": True,
            "voices": voices,
            "count": len(voices)
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "voices": [],
            "count": 0
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to list voices: {str(e)}",
            "voices": [],
            "count": 0
        }


def find_voice_by_name(voice_name: str) -> Dict[str, Any]:
    """
    Find a voice by name in the ElevenLabs account.
    
    Args:
        voice_name: Name of the voice to search for
        
    Returns:
        Dictionary containing:
        - success: Boolean indicating if voice was found
        - voice_id: ID of the found voice (if successful)
        - voice: Full voice details (if successful)
        - error: Error message if failed or not found
    """
    try:
        voice_service = ElevenLabsVoice()
        voice_id = voice_service.get_voice_by_name(voice_name)
        
        if voice_id:
            # Get full voice details
            voice_details = voice_service.get_voice_by_id(voice_id)
            
            return {
                "success": True,
                "voice_id": voice_id,
                "voice": voice_details
            }
        else:
            return {
                "success": False,
                "error": f"Voice '{voice_name}' not found",
                "voice_id": None,
                "voice": None
            }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "voice_id": None,
            "voice": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Failed to search for voice: {str(e)}",
            "voice_id": None,
            "voice": None
        }

