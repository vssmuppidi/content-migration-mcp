"""Test suite for video generation workflow."""

import os
import sys
from pathlib import Path

# Add src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from utils.video import extract_frame_from_video, validate_image_file, get_video_info
from utils.audio import extract_audio_from_video
from sources.did_video import DIDVideo
from tools.video import (
    generate_video_from_image_audio,
    generate_video_from_video,
    generate_complete_video
)


def test_frame_extraction():
    """Test extracting a frame from a video."""
    print("\n" + "="*60)
    print("TEST: Frame Extraction from Video")
    print("="*60)
    
    video_path = input("Enter path to test video file: ").strip().strip('"')
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        return False
    
    try:
        # Get video info
        print("\nFetching video information...")
        video_info = get_video_info(video_path)
        print(f"✓ Video info: {video_info['width']}x{video_info['height']}, "
              f"{video_info['duration']:.2f}s, {video_info['codec']}")
        
        # Extract frame at 2 seconds
        print("\nExtracting frame at 2 seconds...")
        frame_path = extract_frame_from_video(video_path, timestamp=2.0)
        print(f"✓ Frame extracted to: {frame_path}")
        
        # Validate the frame
        print("\nValidating extracted frame...")
        is_valid, error_msg = validate_image_file(frame_path)
        if is_valid:
            print("✓ Frame validation passed")
            return True
        else:
            print(f"✗ Frame validation failed: {error_msg}")
            return False
            
    except Exception as e:
        print(f"✗ Frame extraction failed: {str(e)}")
        return False


def test_audio_validation():
    """Test audio and image file validation."""
    print("\n" + "="*60)
    print("TEST: Audio and Image Validation")
    print("="*60)
    
    video_path = input("Enter path to test video file (for audio extraction): ").strip().strip('"')
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        return False
    
    try:
        # Extract audio
        print("\nExtracting audio from video...")
        audio_path = extract_audio_from_video(video_path)
        print(f"✓ Audio extracted to: {audio_path}")
        
        # Check audio file exists
        if os.path.exists(audio_path):
            print(f"✓ Audio file exists ({os.path.getsize(audio_path)} bytes)")
            return True
        else:
            print("✗ Audio file does not exist")
            return False
            
    except Exception as e:
        print(f"✗ Audio validation failed: {str(e)}")
        return False


def test_did_api_connection():
    """Test D-ID API connectivity."""
    print("\n" + "="*60)
    print("TEST: D-ID API Connection")
    print("="*60)
    
    try:
        # Initialize D-ID client
        print("\nInitializing D-ID client...")
        did_client = DIDVideo()
        print("✓ D-ID client initialized successfully")
        
        print("\n⚠ Note: Full API test requires uploading files and generating a video.")
        print("⚠ This will be tested in the complete workflow test.")
        
        return True
        
    except ValueError as e:
        print(f"✗ D-ID API key missing: {str(e)}")
        print("Please set DID_API_KEY in your .env file")
        return False
    except Exception as e:
        print(f"✗ D-ID client initialization failed: {str(e)}")
        return False


def test_video_from_video():
    """Test generating a talking head video from a source video."""
    print("\n" + "="*60)
    print("TEST: Generate Video from Video (Frame + Audio Extraction)")
    print("="*60)
    
    video_path = input("Enter path to test video file: ").strip().strip('"')
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        return False
    
    print("\n⚠ This test will:")
    print("  1. Extract a frame from the video (at 2 seconds)")
    print("  2. Extract audio from the video")
    print("  3. Upload both to D-ID")
    print("  4. Generate a talking head video")
    print("  5. Download the result to output/video/")
    print("\n⚠ This may take 30-60 seconds and will use D-ID API credits.")
    
    confirm = input("\nProceed with test? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Test skipped.")
        return None
    
    try:
        print("\nGenerating talking head video...")
        result = generate_video_from_video(
            video_path=video_path,
            audio_path=None,  # Will extract from video
            frame_timestamp=2.0
        )
        
        if result.get("success"):
            print("\n✓ Video generation successful!")
            print(f"  Video path: {result['video_path']}")
            print(f"  Frame used: {result['frame_path']}")
            print(f"  Audio used: {result['audio_path']}")
            print(f"\nMetadata: {result.get('metadata', {})}")
            return True
        else:
            print(f"\n✗ Video generation failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Video generation failed: {str(e)}")
        return False


def test_complete_workflow():
    """Test the complete end-to-end workflow."""
    print("\n" + "="*60)
    print("TEST: Complete Video Generation Workflow")
    print("="*60)
    print("\nThis test will:")
    print("  1. Research trending topics on a subject")
    print("  2. Generate a script")
    print("  3. Clone voice from video")
    print("  4. Generate audio")
    print("  5. Extract frame from video")
    print("  6. Generate talking head video")
    
    video_path = input("\nEnter path to test video file: ").strip().strip('"')
    
    if not os.path.exists(video_path):
        print(f"✗ Video file not found: {video_path}")
        return False
    
    topic = input("Enter topic to research (e.g., 'artificial intelligence'): ").strip()
    if not topic:
        topic = "artificial intelligence"
        print(f"Using default topic: {topic}")
    
    print("\n⚠ This test will:")
    print("  - Fetch data from Reddit, YouTube, and Google News")
    print("  - Use AI to generate a script (Groq/OpenRouter)")
    print("  - Use ElevenLabs to clone voice and generate audio")
    print("  - Use D-ID to generate video")
    print("  - This may take 60-120 seconds and will use API credits")
    
    confirm = input("\nProceed with complete workflow test? (yes/no): ").strip().lower()
    if confirm != "yes":
        print("Test skipped.")
        return None
    
    try:
        print("\nStarting complete workflow...")
        print("This may take a while, please be patient...\n")
        
        result = generate_complete_video(
            topic=topic,
            duration_seconds=15,  # Short duration for testing
            video_path=video_path,
            style="informative and engaging",
            limit=2  # Fewer sources for faster testing
        )
        
        if result.get("success"):
            print("\n" + "="*60)
            print("✓ COMPLETE WORKFLOW SUCCESS!")
            print("="*60)
            print(f"\nScript ({len(result['script'].split())} words):")
            print("-" * 60)
            print(result['script'])
            print("-" * 60)
            print(f"\nGenerated files:")
            print(f"  Audio: {result['audio_path']}")
            print(f"  Video: {result['video_path']}")
            print(f"  Frame: {result['frame_path']}")
            print(f"\nVoice ID: {result.get('voice_id')}")
            print(f"\nTrending topics used:")
            for i, topic_item in enumerate(result.get('trending_topics', [])[:3], 1):
                print(f"  {i}. {topic_item.get('title', 'N/A')}")
            
            return True
        else:
            print(f"\n✗ Complete workflow failed: {result.get('error')}")
            return False
            
    except Exception as e:
        print(f"✗ Complete workflow failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("VIDEO GENERATION TEST SUITE")
    print("="*60)
    print("\nThis test suite will verify the video generation functionality.")
    print("You will need:")
    print("  - A test video file (10-20 seconds recommended)")
    print("  - D-ID API key set in .env")
    print("  - ElevenLabs API key set in .env (for complete workflow)")
    print("  - Groq or OpenRouter API key set in .env (for complete workflow)")
    
    tests = [
        ("Frame Extraction", test_frame_extraction),
        ("Audio Validation", test_audio_validation),
        ("D-ID API Connection", test_did_api_connection),
        ("Video from Video", test_video_from_video),
        ("Complete Workflow", test_complete_workflow),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except KeyboardInterrupt:
            print("\n\nTest suite interrupted by user.")
            break
        except Exception as e:
            print(f"\n✗ Unexpected error in {test_name}: {str(e)}")
            results[test_name] = False
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    for test_name, result in results.items():
        if result is True:
            status = "✓ PASS"
        elif result is False:
            status = "✗ FAIL"
        else:
            status = "⊘ SKIP"
        print(f"{status:8} {test_name}")
    
    passed = sum(1 for r in results.values() if r is True)
    failed = sum(1 for r in results.values() if r is False)
    skipped = sum(1 for r in results.values() if r is None)
    
    print(f"\nTotal: {passed} passed, {failed} failed, {skipped} skipped")


if __name__ == "__main__":
    main()

