"""Audio utilities for video-to-audio extraction and validation."""

import os
import tempfile
from typing import Optional
import ffmpeg
from pydub import AudioSegment
from pydub.utils import mediainfo


def extract_audio_from_video(video_path: str, output_format: str = "mp3") -> str:
    """
    Extract audio from a video file.
    
    Args:
        video_path: Path to the video file
        output_format: Audio format (default: mp3)
        
    Returns:
        Path to the extracted audio file
        
    Raises:
        FileNotFoundError: If video file doesn't exist
        Exception: If extraction fails
    """
    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")
    
    try:
        # Create temporary file for audio output
        temp_dir = tempfile.gettempdir()
        temp_audio = os.path.join(
            temp_dir,
            f"audio_extract_{os.getpid()}_{os.path.basename(video_path).split('.')[0]}.{output_format}"
        )
        
        # Extract audio using ffmpeg
        (
            ffmpeg
            .input(video_path)
            .output(temp_audio, acodec='libmp3lame' if output_format == 'mp3' else 'pcm_s16le', ar='44100')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        
        return temp_audio
        
    except ffmpeg.Error as e:
        error_message = e.stderr.decode() if e.stderr else str(e)
        raise Exception(f"Failed to extract audio from video: {error_message}")
    except Exception as e:
        raise Exception(f"Error extracting audio: {str(e)}")


def validate_audio_file(audio_path: str, min_duration: float = 1.0, max_duration: float = 600.0) -> tuple[bool, str]:
    """
    Validate an audio file for voice cloning.
    
    Note: These are minimal checks. ElevenLabs can handle a wide range of audio lengths.
    Optimal is typically 10-30 seconds, but 1 second to 10 minutes will work.
    
    Args:
        audio_path: Path to audio file
        min_duration: Minimum acceptable duration in seconds (default: 1)
        max_duration: Maximum acceptable duration in seconds (default: 600/10 min)
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not os.path.exists(audio_path):
        return False, f"Audio file not found: {audio_path}"
    
    try:
        # Get audio info
        audio = AudioSegment.from_file(audio_path)
        duration_seconds = len(audio) / 1000.0  # pydub returns milliseconds
        
        # Only reject extremely short audio (less than 1 second is useless)
        if duration_seconds < min_duration:
            return False, f"Audio too short ({duration_seconds:.1f}s). Need at least {min_duration}s of audio."
        
        if duration_seconds > max_duration:
            return False, f"Audio too long ({duration_seconds:.1f}s). Maximum {max_duration}s supported."
        
        return True, f"Audio valid ({duration_seconds:.1f}s)"
        
    except Exception as e:
        return False, f"Error validating audio: {str(e)}"


def cleanup_temp_audio(audio_path: str) -> None:
    """
    Safely delete a temporary audio file.
    
    Args:
        audio_path: Path to temporary audio file
    """
    try:
        if audio_path and os.path.exists(audio_path):
            # Only delete files in temp directory for safety
            if tempfile.gettempdir() in audio_path:
                os.remove(audio_path)
    except Exception:
        # Silent fail - don't break workflow if cleanup fails
        pass


def get_audio_duration(audio_path: str) -> Optional[float]:
    """
    Get the duration of an audio file in seconds.
    
    Args:
        audio_path: Path to audio file
        
    Returns:
        Duration in seconds, or None if error
    """
    try:
        audio = AudioSegment.from_file(audio_path)
        return len(audio) / 1000.0  # Convert milliseconds to seconds
    except Exception:
        return None

