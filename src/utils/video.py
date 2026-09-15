"""Video processing utilities for frame extraction and validation."""

import os
import tempfile
from typing import Tuple
from PIL import Image
import ffmpeg


def extract_frame_from_video(
    video_path: str,
    timestamp: float = 2.0,
    output_path: str = None
) -> str:
    """
    Extract a single frame from a video at a specific timestamp.
    
    Args:
        video_path: Path to the video file
        timestamp: Time in seconds where to extract the frame (default: 2.0)
        output_path: Optional output path for the frame (default: temp file)
    
    Returns:
        Path to the extracted frame image
        
    Raises:
        Exception: If frame extraction fails
    """
    try:
        # Generate output path if not provided
        if not output_path:
            temp_fd, output_path = tempfile.mkstemp(suffix='.jpg', prefix='frame_')
            os.close(temp_fd)
        
        # Ensure output directory exists
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
        
        # Extract frame using ffmpeg
        (
            ffmpeg
            .input(video_path, ss=timestamp)
            .output(output_path, vframes=1, format='image2', vcodec='mjpeg')
            .overwrite_output()
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
        
        # Verify the frame was created
        if not os.path.exists(output_path):
            raise Exception("Frame extraction completed but output file not found")
        
        return output_path
        
    except ffmpeg.Error as e:
        error_msg = e.stderr.decode() if e.stderr else str(e)
        raise Exception(f"FFmpeg frame extraction failed: {error_msg}")
    except Exception as e:
        raise Exception(f"Failed to extract frame from video: {str(e)}")


def extract_best_frame(video_path: str, output_path: str = None) -> str:
    """
    Extract the best frame from a video for use as a profile image.
    
    Extracts at 2 seconds to avoid intro/fade effects.
    
    Args:
        video_path: Path to the video file
        output_path: Optional output path for the frame
    
    Returns:
        Path to the extracted frame
    """
    return extract_frame_from_video(video_path, timestamp=2.0, output_path=output_path)


def validate_image_file(image_path: str) -> Tuple[bool, str]:
    """
    Validate an image file for use with D-ID.
    
    Checks:
    - File exists
    - Valid image format (jpg, png, jpeg)
    - Minimum resolution (256x256)
    
    Args:
        image_path: Path to the image file
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if image is valid, False otherwise
        - error_message: Empty string if valid, error description otherwise
    """
    # Check file exists
    if not os.path.exists(image_path):
        return False, f"Image file not found: {image_path}"
    
    # Check file extension
    valid_extensions = ['.jpg', '.jpeg', '.png']
    file_ext = os.path.splitext(image_path)[1].lower()
    if file_ext not in valid_extensions:
        return False, f"Invalid image format. Expected {', '.join(valid_extensions)}, got {file_ext}"
    
    try:
        # Open image and check resolution
        with Image.open(image_path) as img:
            width, height = img.size
            
            min_dimension = 256
            if width < min_dimension or height < min_dimension:
                return False, f"Image too small ({width}x{height}). Minimum resolution: {min_dimension}x{min_dimension}"
            
            # Check if image is valid (can be read)
            img.verify()
        
        return True, ""
        
    except Exception as e:
        return False, f"Invalid or corrupted image file: {str(e)}"


def cleanup_temp_image(image_path: str) -> None:
    """
    Safely delete a temporary image file.
    
    Args:
        image_path: Path to the image file to delete
    """
    try:
        if image_path and os.path.exists(image_path):
            # Only delete if it's in a temp directory to avoid accidental deletion
            if tempfile.gettempdir() in image_path:
                os.remove(image_path)
    except Exception:
        # Silently ignore cleanup errors
        pass


def get_video_info(video_path: str) -> dict:
    """
    Get information about a video file.
    
    Args:
        video_path: Path to the video file
    
    Returns:
        Dictionary with video information (duration, width, height, etc.)
    """
    try:
        probe = ffmpeg.probe(video_path)
        video_info = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        
        return {
            'duration': float(probe['format']['duration']),
            'width': int(video_info['width']),
            'height': int(video_info['height']),
            'fps': eval(video_info['r_frame_rate']),  # Frame rate as float
            'codec': video_info['codec_name']
        }
    except Exception as e:
        raise Exception(f"Failed to get video info: {str(e)}")

