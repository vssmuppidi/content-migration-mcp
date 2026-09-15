"""D-ID API integration for video generation from images and audio."""

import os
import time
import logging
import requests
from typing import Dict, Any, Optional

from ..config import config

# Setup logging to file
logging.basicConfig(
    filename='/tmp/did_debug.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DIDVideo:
    """D-ID API client for creating talking head videos."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize D-ID API client.
        
        Args:
            api_key: D-ID API key (defaults to config value)
        """
        self.api_key = api_key or config.did_api_key
        if not self.api_key:
            raise ValueError("D-ID API key is required. Set DID_API_KEY environment variable.")
        
        self.base_url = "https://api.d-id.com"
        self.headers = {
            "Authorization": f"Basic {self.api_key}",
            "Content-Type": "application/json"
        }
        
        logger.info("D-ID API client initialized")
    
    def create_talking_head(
        self,
        image_path: str,
        audio_path: str,
        output_path: str,
        max_wait_seconds: int = 120
    ) -> str:
        """
        Create a talking head video from an image and audio file.
        
        This method handles the full workflow:
        1. Upload image
        2. Upload audio
        3. Create talk request
        4. Poll for completion
        5. Download video
        
        Args:
            image_path: Path to the image file (jpg/png)
            audio_path: Path to the audio file (mp3/wav)
            output_path: Path where the video will be saved
            max_wait_seconds: Maximum time to wait for video generation (default: 120s)
        
        Returns:
            Path to the generated video file
            
        Raises:
            Exception: If video generation fails or times out
        """
        try:
            logger.info(f"Starting talking head creation: image={image_path}, audio={audio_path}")
            
            # Step 1: Upload image
            image_url = self._upload_image(image_path)
            logger.info(f"Image uploaded: {image_url}")
            
            # Step 2: Upload audio
            audio_url = self._upload_audio(audio_path)
            logger.info(f"Audio uploaded: {audio_url}")
            
            # Step 3: Create talk
            talk_id = self._create_talk(image_url, audio_url)
            logger.info(f"Talk created with ID: {talk_id}")
            
            # Step 4: Poll for completion
            video_url = self._wait_for_completion(talk_id, max_wait_seconds)
            logger.info(f"Video ready: {video_url}")
            
            # Step 5: Download video
            result_path = self._download_video(video_url, output_path)
            logger.info(f"Video downloaded to: {result_path}")
            
            return result_path
            
        except Exception as e:
            error_msg = f"Failed to create talking head video: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise Exception(error_msg)
    
    def _upload_image(self, image_path: str) -> str:
        """
        Upload an image to D-ID and get the URL.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            URL of the uploaded image
        """
        try:
            with open(image_path, 'rb') as image_file:
                files = {'image': image_file}
                headers = {"Authorization": f"Basic {self.api_key}"}
                
                response = requests.post(
                    f"{self.base_url}/images",
                    headers=headers,
                    files=files,
                    timeout=30
                )
                response.raise_for_status()
                
                result = response.json()
                return result['url']
                
        except Exception as e:
            logger.error(f"Image upload failed: {str(e)}")
            raise Exception(f"Failed to upload image: {str(e)}")
    
    def _upload_audio(self, audio_path: str) -> str:
        """
        Upload an audio file to D-ID and get the URL.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            URL of the uploaded audio
        """
        try:
            with open(audio_path, 'rb') as audio_file:
                files = {'audio': audio_file}
                headers = {"Authorization": f"Basic {self.api_key}"}
                
                response = requests.post(
                    f"{self.base_url}/audios",
                    headers=headers,
                    files=files,
                    timeout=30
                )
                
                # Log response details before raising for status
                logger.info(f"D-ID audio upload response status: {response.status_code}")
                logger.info(f"D-ID audio upload response body: {response.text}")
                
                response.raise_for_status()
                
                result = response.json()
                return result['url']
                
        except Exception as e:
            logger.error(f"Audio upload failed: {str(e)}")
            logger.error(f"Audio file path: {audio_path}")
            logger.error(f"Audio file size: {os.path.getsize(audio_path)} bytes")
            raise Exception(f"Failed to upload audio: {str(e)}")
    
    def _create_talk(self, image_url: str, audio_url: str) -> str:
        """
        Create a talk (video generation request) on D-ID.
        
        Args:
            image_url: URL of the uploaded image
            audio_url: URL of the uploaded audio
            
        Returns:
            Talk ID for polling status
        """
        try:
            payload = {
                "source_url": image_url,
                "script": {
                    "type": "audio",
                    "audio_url": audio_url
                },
                "config": {
                    "fluent": True,
                    "pad_audio": 0.0
                }
            }
            
            response = requests.post(
                f"{self.base_url}/talks",
                headers=self.headers,
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            return result['id']
            
        except Exception as e:
            logger.error(f"Talk creation failed: {str(e)}")
            raise Exception(f"Failed to create talk: {str(e)}")
    
    def check_video_status(self, talk_id: str) -> Dict[str, Any]:
        """
        Check the status of a video generation.
        
        Args:
            talk_id: The talk ID to check
            
        Returns:
            Dictionary with status information:
            - status: 'created', 'processing', 'done', 'error'
            - result_url: URL of the video (if done)
            - error: Error message (if error)
        """
        try:
            response = requests.get(
                f"{self.base_url}/talks/{talk_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            
            result = response.json()
            
            status_info = {
                'status': result.get('status', 'unknown'),
                'result_url': result.get('result_url'),
                'error': result.get('error')
            }
            
            logger.debug(f"Status check for {talk_id}: {status_info['status']}")
            return status_info
            
        except Exception as e:
            logger.error(f"Status check failed: {str(e)}")
            raise Exception(f"Failed to check video status: {str(e)}")
    
    def _wait_for_completion(self, talk_id: str, max_wait_seconds: int = 120) -> str:
        """
        Poll for video completion.
        
        Args:
            talk_id: The talk ID to monitor
            max_wait_seconds: Maximum time to wait
            
        Returns:
            URL of the completed video
            
        Raises:
            Exception: If timeout or error occurs
        """
        start_time = time.time()
        poll_interval = 3  # seconds
        
        logger.info(f"Waiting for video completion (max {max_wait_seconds}s)")
        
        while time.time() - start_time < max_wait_seconds:
            status_info = self.check_video_status(talk_id)
            
            if status_info['status'] == 'done':
                return status_info['result_url']
            elif status_info['status'] == 'error':
                error_msg = status_info.get('error', 'Unknown error')
                raise Exception(f"Video generation failed: {error_msg}")
            
            # Still processing, wait before next check
            time.sleep(poll_interval)
        
        # Timeout
        raise Exception(f"Video generation timed out after {max_wait_seconds} seconds")
    
    def download_video(self, video_url: str, output_path: str) -> str:
        """
        Download a video from D-ID.
        
        Args:
            video_url: URL of the video to download
            output_path: Path where to save the video
            
        Returns:
            Path to the downloaded video
        """
        return self._download_video(video_url, output_path)
    
    def _download_video(self, video_url: str, output_path: str) -> str:
        """
        Internal method to download video.
        
        Args:
            video_url: URL of the video
            output_path: Path to save the video
            
        Returns:
            Path to the saved video
        """
        try:
            logger.info(f"Downloading video from: {video_url}")
            
            response = requests.get(video_url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Ensure output directory exists
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            # Download and save
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Video saved to: {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Video download failed: {str(e)}")
            raise Exception(f"Failed to download video: {str(e)}")

