"""ElevenLabs API integration for voice cloning and text-to-speech."""

import os
import logging
from typing import Dict, Any, Optional
from elevenlabs import VoiceSettings
from elevenlabs.client import ElevenLabs
from ..config import config

# Setup logging to file
logging.basicConfig(
    filename='/tmp/elevenlabs_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ElevenLabsVoice:
    """Wrapper for ElevenLabs API interactions."""
    
    def __init__(self):
        """Initialize ElevenLabs API client."""
        if not config.validate_elevenlabs_config():
            logger.error("ElevenLabs API key not configured")
            raise ValueError(
                "ElevenLabs API key not configured. "
                "Please set ELEVENLABS_API_KEY environment variable."
            )
        
        self.client = ElevenLabs(api_key=config.elevenlabs_api_key)
        logger.info("ElevenLabs client initialized successfully")
    
    def clone_voice_from_audio(
        self,
        audio_path: str,
        voice_name: Optional[str] = None
    ) -> str:
        """
        Clone a voice from an audio sample using ElevenLabs.
        
        Args:
            audio_path: Path to audio file for voice cloning
            voice_name: Optional name for the cloned voice
            
        Returns:
            voice_id: ID of the cloned voice
            
        Raises:
            Exception: If voice cloning fails
        """
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        try:
            # Generate voice name if not provided
            if not voice_name:
                voice_name = f"cloned_voice_{os.path.basename(audio_path).split('.')[0]}"
            
            # Add voice using instant voice cloning (IVC)
            with open(audio_path, 'rb') as audio_file:
                voice = self.client.voices.ivc.create(
                    name=voice_name,
                    files=[audio_file],
                )
            
            return voice.voice_id
            
        except Exception as e:
            # Log the full error details for debugging
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "audio_path": audio_path,
                "voice_name": voice_name
            }
            # Try to get more details from API errors
            if hasattr(e, 'response'):
                error_details["response_status"] = getattr(e.response, 'status_code', None)
                error_details["response_body"] = getattr(e.response, 'text', None)
            
            import json
            raise Exception(f"Failed to clone voice: {json.dumps(error_details, indent=2)}")
    
    def generate_audio_from_text(
        self,
        text: str,
        voice_id: str,
        output_path: str,
        model: str = "eleven_v3"
    ) -> str:
        """
        Generate audio from text using a cloned voice.
        
        Args:
            text: Text to convert to speech
            voice_id: ID of the voice to use
            output_path: Path to save the generated audio
            model: ElevenLabs model to use (default: eleven_v3 for emotional tag support)
            
        Returns:
            Path to the generated audio file
            
        Raises:
            Exception: If audio generation fails
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")
        
        try:
            logger.info(f"Generating audio with voice_id={voice_id}, text_length={len(text)}, model={model}")
            
            # Generate audio using text-to-speech
            audio_generator = self.client.text_to_speech.convert(
                voice_id=voice_id,
                text=text,
                model_id=model,
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )
            
            logger.debug(f"Audio generator created, writing to {output_path}")
            
            # Save audio to file
            with open(output_path, 'wb') as audio_file:
                for chunk in audio_generator:
                    audio_file.write(chunk)
            
            file_size = os.path.getsize(output_path)
            logger.info(f"Audio generation complete! File: {output_path}, Size: {file_size} bytes")
            return output_path
            
        except Exception as e:
            # Log the full error details for debugging
            error_details = {
                "error_type": type(e).__name__,
                "error_message": str(e),
                "voice_id": voice_id,
                "text_length": len(text) if text else 0
            }
            # Try to get more details from API errors
            if hasattr(e, 'response'):
                error_details["response_status"] = getattr(e.response, 'status_code', None)
                error_details["response_body"] = getattr(e.response, 'text', None)
            
            import json
            error_json = json.dumps(error_details, indent=2)
            logger.error(f"Audio generation failed: {error_json}")
            raise Exception(f"Failed to generate audio: {error_json}")
    
    def clone_and_generate(
        self,
        audio_sample_path: str,
        script_text: str,
        output_path: str,
        voice_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Combined operation: clone voice from sample and generate audio from script.
        
        Args:
            audio_sample_path: Path to audio sample for voice cloning
            script_text: Script text to convert to speech
            output_path: Path to save the generated audio
            voice_name: Optional name for the cloned voice
            
        Returns:
            Dictionary containing:
            - success: Boolean indicating success
            - voice_id: ID of the cloned voice
            - audio_path: Path to generated audio file
            - metadata: Additional metadata
            - error: Error message if failed
        """
        try:
            # Step 1: Clone voice
            voice_id = self.clone_voice_from_audio(audio_sample_path, voice_name)
            
            # Step 2: Generate audio from script
            audio_path = self.generate_audio_from_text(
                text=script_text,
                voice_id=voice_id,
                output_path=output_path
            )
            
            # Get audio file size
            audio_size = os.path.getsize(audio_path) if os.path.exists(audio_path) else 0
            
            return {
                "success": True,
                "voice_id": voice_id,
                "audio_path": audio_path,
                "metadata": {
                    "audio_size_bytes": audio_size,
                    "sample_audio": audio_sample_path,
                    "script_length": len(script_text)
                }
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "voice_id": None,
                "audio_path": None
            }
    
    def list_voices(self) -> list[Dict[str, Any]]:
        """
        List all voices in the ElevenLabs account.
        
        Returns:
            List of voice dictionaries with voice_id, name, description, etc.
        """
        try:
            voices_response = self.client.voices.get_all()
            voices = []
            
            for voice in voices_response.voices:
                voices.append({
                    "voice_id": voice.voice_id,
                    "name": voice.name,
                    "category": getattr(voice, "category", "cloned"),
                    "description": getattr(voice, "description", ""),
                    "labels": getattr(voice, "labels", {}),
                })
            
            return voices
        except Exception as e:
            raise Exception(f"Failed to list voices: {str(e)}")
    
    def get_voice_by_name(self, name: str) -> Optional[str]:
        """
        Find a voice by name (case-insensitive).
        
        Args:
            name: Name of the voice to find
            
        Returns:
            voice_id if found, None otherwise
        """
        try:
            logger.info(f"Searching for voice by name: '{name}'")
            voices = self.list_voices()
            logger.debug(f"Found {len(voices)} total voices in account")
            
            # Case-insensitive search
            name_lower = name.lower()
            for voice in voices:
                if voice["name"].lower() == name_lower:
                    logger.info(f"Voice '{name}' found with ID: {voice['voice_id']}")
                    return voice["voice_id"]
            
            logger.warning(f"Voice '{name}' not found in account")
            return None
        except Exception as e:
            logger.error(f"Error searching for voice '{name}': {str(e)}")
            return None
    
    def get_voice_by_id(self, voice_id: str) -> Optional[Dict[str, Any]]:
        """
        Get voice details by ID.
        
        Args:
            voice_id: ID of the voice to retrieve
            
        Returns:
            Voice dictionary if found, None otherwise
        """
        try:
            voice = self.client.voices.get(voice_id)
            
            return {
                "voice_id": voice.voice_id,
                "name": voice.name,
                "category": getattr(voice, "category", "cloned"),
                "description": getattr(voice, "description", ""),
                "labels": getattr(voice, "labels", {}),
            }
        except Exception:
            return None
    
    def delete_voice(self, voice_id: str) -> bool:
        """
        Delete a cloned voice from ElevenLabs.
        
        Args:
            voice_id: ID of the voice to delete
            
        Returns:
            Boolean indicating success
        """
        try:
            self.client.voices.delete(voice_id)
            return True
        except Exception:
            return False


# Module-level function for easy access
def generate_voice_audio(
    audio_sample_path: str,
    script_text: str,
    output_path: str
) -> Dict[str, Any]:
    """
    Convenience function to clone voice and generate audio.
    
    Args:
        audio_sample_path: Path to audio sample for voice cloning
        script_text: Script text to convert to speech
        output_path: Path to save the generated audio
        
    Returns:
        Dictionary with result and metadata
    """
    try:
        voice_service = ElevenLabsVoice()
        return voice_service.clone_and_generate(
            audio_sample_path,
            script_text,
            output_path
        )
    except ValueError as e:
        # Return error if not configured
        return {
            "success": False,
            "error": str(e),
            "voice_id": None,
            "audio_path": None
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Voice generation error: {str(e)}",
            "voice_id": None,
            "audio_path": None
        }

