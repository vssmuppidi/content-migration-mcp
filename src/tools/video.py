"""Video generation tools combining image, audio, and D-ID API."""

import os
import tempfile
from typing import Dict, Any, Optional
from datetime import datetime

from .voice import generate_complete_content
from ..utils.audio import extract_audio_from_video, cleanup_temp_audio
from ..utils.video import (
    extract_frame_from_video,
    extract_best_frame,
    validate_image_file,
    cleanup_temp_image
)
from ..sources.did_video import DIDVideo


def generate_video_from_image_audio(
    image_path: str,
    audio_path: str,
    output_video_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate talking head video from image and audio.
    
    This is the most basic video generation tool. It takes an existing
    image and audio file and creates a talking head video using D-ID.
    
    Args:
        image_path: Path to image file (jpg/png)
        audio_path: Path to audio file (mp3/wav)
        output_video_path: Optional output path (default: output/video/)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - video_path: Path to the generated video
        - metadata: Additional information about the generation
        - error: Error message if failed
    """
    try:
        # Validate image
        is_valid, error_msg = validate_image_file(image_path)
        if not is_valid:
            return {
                "success": False,
                "error": f"Image validation failed: {error_msg}"
            }
        
        # Validate audio exists
        if not os.path.exists(audio_path):
            return {
                "success": False,
                "error": f"Audio file not found: {audio_path}"
            }
        
        # Generate output path if not provided
        if not output_video_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.path.dirname(__file__), "../../output/video")
            os.makedirs(output_dir, exist_ok=True)
            output_video_path = os.path.join(output_dir, f"talking_head_{timestamp}.mp4")
        else:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        # Initialize D-ID client
        did_client = DIDVideo()
        
        # Generate video
        result_path = did_client.create_talking_head(
            image_path=image_path,
            audio_path=audio_path,
            output_path=output_video_path,
            max_wait_seconds=120
        )
        
        return {
            "success": True,
            "video_path": result_path,
            "metadata": {
                "image_path": image_path,
                "audio_path": audio_path,
                "generation_method": "d-id_api"
            }
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Video generation failed: {str(e)}"
        }


def generate_video_from_video(
    video_path: str,
    audio_path: Optional[str] = None,
    output_video_path: Optional[str] = None,
    frame_timestamp: float = 2.0
) -> Dict[str, Any]:
    """
    Generate talking head video by extracting frame from video.
    
    This tool extracts a frame from a video to use as the image,
    and optionally uses the video's audio or a provided audio file.
    
    Args:
        video_path: Path to source video
        audio_path: Optional audio file (if None, extracts from video)
        output_video_path: Optional output path (default: output/video/)
        frame_timestamp: Timestamp to extract frame (default: 2.0s)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - video_path: Path to the generated video
        - frame_path: Path to the extracted frame
        - audio_path: Path to the audio used
        - metadata: Additional information
        - error: Error message if failed
    """
    temp_frame_path = None
    temp_audio_path = None
    
    try:
        # Validate source video exists
        if not os.path.exists(video_path):
            return {
                "success": False,
                "error": f"Video file not found: {video_path}"
            }
        
        # Extract frame from video
        temp_frame_path = extract_frame_from_video(video_path, timestamp=frame_timestamp)
        
        # Validate extracted frame
        is_valid, error_msg = validate_image_file(temp_frame_path)
        if not is_valid:
            cleanup_temp_image(temp_frame_path)
            return {
                "success": False,
                "error": f"Extracted frame validation failed: {error_msg}"
            }
        
        # Handle audio
        if audio_path is None:
            # Extract audio from the same video
            temp_audio_path = extract_audio_from_video(video_path)
            audio_to_use = temp_audio_path
        else:
            # Use provided audio
            if not os.path.exists(audio_path):
                cleanup_temp_image(temp_frame_path)
                return {
                    "success": False,
                    "error": f"Audio file not found: {audio_path}"
                }
            audio_to_use = audio_path
        
        # Generate output path if not provided
        if not output_video_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.path.dirname(__file__), "../../output/video")
            os.makedirs(output_dir, exist_ok=True)
            output_video_path = os.path.join(output_dir, f"talking_head_{timestamp}.mp4")
        else:
            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        # Initialize D-ID client
        did_client = DIDVideo()
        
        # Generate video
        result_path = did_client.create_talking_head(
            image_path=temp_frame_path,
            audio_path=audio_to_use,
            output_path=output_video_path,
            max_wait_seconds=120
        )
        
        return {
            "success": True,
            "video_path": result_path,
            "frame_path": temp_frame_path,
            "audio_path": audio_to_use,
            "metadata": {
                "source_video": video_path,
                "frame_timestamp": frame_timestamp,
                "audio_source": "extracted" if audio_path is None else "provided",
                "generation_method": "d-id_api"
            }
        }
        
    except Exception as e:
        # Cleanup temp files on error
        if temp_frame_path:
            cleanup_temp_image(temp_frame_path)
        if temp_audio_path:
            cleanup_temp_audio(temp_audio_path)
        
        return {
            "success": False,
            "error": f"Video generation failed: {str(e)}"
        }


def generate_complete_video(
    topic: str,
    duration_seconds: int,
    video_path: str,
    provider: Optional[str] = None,
    style: Optional[str] = "informative and engaging",
    limit: int = 3,
    model: Optional[str] = None,
    voice_name: Optional[str] = None,
    voice_id: Optional[str] = None,
    output_video_path: Optional[str] = None,
    frame_timestamp: float = 2.0
) -> Dict[str, Any]:
    """
    Complete end-to-end workflow for content video generation.
    
    This is the most comprehensive tool. It orchestrates the entire process:
    1. Research trending topics from Reddit, YouTube, and Google News
    2. Generate a script based on the trending data
    3. Clone voice from the video (or reuse existing voice)
    4. Generate audio from the script
    5. Extract a frame from the video
    6. Generate talking head video with D-ID
    
    Perfect for agents - complete content creation from topic to video.
    
    Args:
        topic: The topic to research and create content about
        duration_seconds: Target duration of the script/video in seconds
        video_path: Source video for voice cloning and face extraction
        provider: Inference provider - "groq" or "openrouter" (default: from config)
        style: Script style/tone (default: "informative and engaging")
        limit: Number of items to fetch per source (default: 3)
        model: Model to use (default: from config based on provider)
        voice_name: Optional voice name to search for and reuse
        voice_id: Optional existing voice ID to reuse
        output_video_path: Optional path for output video (default: output/video/)
        frame_timestamp: Timestamp to extract frame (default: 2.0s)
    
    Returns:
        Dictionary containing:
        - success: Boolean indicating if generation succeeded
        - script: The generated script text
        - audio_path: Path to the generated audio file
        - video_path: Path to the generated video file
        - frame_path: Path to the extracted frame
        - voice_id: ID of the cloned/used voice
        - trending_topics: The trending topics used for the script
        - metadata: Additional information about the generation process
        - error: Error message if failed
    """
    temp_frame_path = None
    
    try:
        # Step 1-4: Generate content with audio (ideas, script, voice cloning, audio)
        audio_result = generate_complete_content(
            topic=topic,
            duration_seconds=duration_seconds,
            video_path=video_path,
            provider=provider,
            style=style,
            limit=limit,
            model=model,
            voice_id=voice_id,
            voice_name=voice_name
        )
        
        if not audio_result.get("success"):
            return {
                "success": False,
                "error": f"Audio generation failed: {audio_result.get('error', 'Unknown error')}"
            }
        
        # Step 5: Extract frame from video
        temp_frame_path = extract_frame_from_video(video_path, timestamp=frame_timestamp)
        
        # Validate extracted frame
        is_valid, error_msg = validate_image_file(temp_frame_path)
        if not is_valid:
            cleanup_temp_image(temp_frame_path)
            return {
                "success": False,
                "error": f"Frame extraction/validation failed: {error_msg}"
            }
        
        # Step 6: Generate video with D-ID
        if not output_video_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_dir = os.path.join(os.path.dirname(__file__), "../../output/video")
            os.makedirs(output_dir, exist_ok=True)
            # Use topic in filename (sanitized)
            safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:30]
            output_video_path = os.path.join(output_dir, f"content_{safe_topic}_{timestamp}.mp4")
        else:
            os.makedirs(os.path.dirname(output_video_path), exist_ok=True)
        
        # Initialize D-ID client
        did_client = DIDVideo()
        
        # Generate video
        video_path_result = did_client.create_talking_head(
            image_path=temp_frame_path,
            audio_path=audio_result["audio_path"],
            output_path=output_video_path,
            max_wait_seconds=120
        )
        
        return {
            "success": True,
            "script": audio_result["script"],
            "audio_path": audio_result["audio_path"],
            "video_path": video_path_result,
            "frame_path": temp_frame_path,
            "voice_id": audio_result.get("voice_id"),
            "trending_topics": audio_result.get("trending_topics", []),
            "metadata": {
                "topic": topic,
                "duration_seconds": duration_seconds,
                "source_video": video_path,
                "frame_timestamp": frame_timestamp,
                "script_style": style,
                "inference_provider": provider,
                "model": model,
                "generation_method": "complete_workflow"
            }
        }
        
    except Exception as e:
        # Cleanup temp files on error
        if temp_frame_path:
            cleanup_temp_image(temp_frame_path)
        
        return {
            "success": False,
            "error": f"Complete video generation failed: {str(e)}"
        }

