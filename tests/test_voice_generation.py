#!/usr/bin/env python3
"""
Test script for voice generation functionality.
Tests audio extraction, ElevenLabs integration, and voice generation tools.
"""

import os
import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_audio_extraction():
    """Test audio extraction from video."""
    print("=" * 70)
    print("TEST 1: Audio Extraction from Video")
    print("=" * 70)
    
    try:
        from src.utils.audio import extract_audio_from_video, validate_audio_file, cleanup_temp_audio
        
        # Note: This test requires a sample video file
        # Users should provide their own video for testing
        sample_video = input("\nEnter path to a sample video file (or press Enter to skip): ").strip()
        
        if not sample_video:
            print("⚠ Skipped - no video provided")
            return False
        
        if not os.path.exists(sample_video):
            print(f"✗ Video file not found: {sample_video}")
            return False
        
        print(f"\n  Extracting audio from: {sample_video}")
        audio_path = extract_audio_from_video(sample_video)
        print(f"  ✓ Audio extracted to: {audio_path}")
        
        # Validate audio
        is_valid, message = validate_audio_file(audio_path)
        if is_valid:
            print(f"  ✓ Audio validation passed: {message}")
        else:
            print(f"  ⚠ Audio validation warning: {message}")
        
        # Cleanup
        cleanup_temp_audio(audio_path)
        print("  ✓ Temporary audio cleaned up")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        return False


def test_elevenlabs_connection():
    """Test ElevenLabs API connection."""
    print("\n" + "=" * 70)
    print("TEST 2: ElevenLabs API Connection")
    print("=" * 70)
    
    try:
        from src.sources.elevenlabs_voice import ElevenLabsVoice
        from src.config import config
        
        if not config.validate_elevenlabs_config():
            print("  ⚠ ElevenLabs API key not configured in .env")
            print("  ℹ Set ELEVENLABS_API_KEY to test voice generation")
            return False
        
        print("\n  Initializing ElevenLabs client...")
        voice_service = ElevenLabsVoice()
        print("  ✓ ElevenLabs client initialized successfully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        return False


def test_voice_cloning_workflow():
    """Test complete voice cloning workflow."""
    print("\n" + "=" * 70)
    print("TEST 3: Voice Cloning Workflow")
    print("=" * 70)
    
    try:
        from src.tools.voice import generate_audio_from_script
        from src.config import config
        
        if not config.validate_elevenlabs_config():
            print("  ⚠ Skipped - ElevenLabs API key not configured")
            return False
        
        # Get test inputs
        sample_video = input("\nEnter path to a sample video file (or press Enter to skip): ").strip()
        if not sample_video:
            print("  ⚠ Skipped - no video provided")
            return False
        
        if not os.path.exists(sample_video):
            print(f"  ✗ Video file not found: {sample_video}")
            return False
        
        # Test script
        test_script = "Hello! This is a test of the voice cloning system. If you can hear this in a cloned voice, everything is working correctly."
        
        print(f"\n  Testing voice cloning with:")
        print(f"  - Video: {sample_video}")
        print(f"  - Script: {test_script[:50]}...")
        
        # Generate audio
        print("\n  Generating audio (this may take a moment)...")
        result = generate_audio_from_script(
            script=test_script,
            video_path=sample_video
        )
        
        if result.get("success"):
            audio_path = result.get("audio_path")
            voice_id = result.get("voice_id")
            print(f"  ✓ Audio generated successfully!")
            print(f"  - Audio file: {audio_path}")
            print(f"  - Voice ID: {voice_id}")
            print(f"  - File size: {os.path.getsize(audio_path) / 1024:.1f} KB")
            print(f"\n  💡 Play the audio file to verify the voice cloning quality")
            return True
        else:
            print(f"  ✗ Audio generation failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_complete_workflow():
    """Test complete content generation workflow."""
    print("\n" + "=" * 70)
    print("TEST 4: Complete Content Generation Workflow")
    print("=" * 70)
    
    try:
        from src.tools.voice import generate_complete_content
        from src.config import config
        
        # Check all required configs
        missing = []
        if not config.validate_reddit_config():
            missing.append("Reddit API")
        if not config.validate_youtube_config():
            missing.append("YouTube API")
        if not config.has_inference_api():
            missing.append("Inference API (OpenRouter or Groq)")
        if not config.validate_elevenlabs_config():
            missing.append("ElevenLabs API")
        
        if missing:
            print(f"  ⚠ Skipped - Missing configuration: {', '.join(missing)}")
            return False
        
        sample_video = input("\nEnter path to a sample video file (or press Enter to skip): ").strip()
        if not sample_video:
            print("  ⚠ Skipped - no video provided")
            return False
        
        if not os.path.exists(sample_video):
            print(f"  ✗ Video file not found: {sample_video}")
            return False
        
        print(f"\n  Testing complete workflow:")
        print(f"  - Topic: 'artificial intelligence'")
        print(f"  - Duration: 20 seconds")
        print(f"  - Video: {sample_video}")
        
        print("\n  Generating content (this will take 30-60 seconds)...")
        print("  Steps: Fetch topics → Generate script → Clone voice → Generate audio")
        
        result = generate_complete_content(
            topic="artificial intelligence",
            duration_seconds=20,
            video_path=sample_video,
            provider="groq",
            limit=2  # Fewer items for faster testing
        )
        
        if result.get("success"):
            print(f"\n  ✓ Complete workflow succeeded!")
            print(f"\n  Script Preview:")
            script = result.get("script", "")
            print(f"  {script[:200]}...")
            print(f"\n  Audio Details:")
            print(f"  - Audio file: {result.get('audio_path')}")
            print(f"  - Voice ID: {result.get('voice_id')}")
            print(f"  - Trending sources: {result.get('trending_data', {}).get('summary', {}).get('total_items', 0)} items")
            print(f"\n  💡 Play the audio file to verify the complete workflow")
            return True
        else:
            print(f"  ✗ Workflow failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_list_voices():
    """Test listing all voices."""
    print("\n" + "=" * 70)
    print("TEST 5: List All Voices")
    print("=" * 70)
    
    try:
        from src.tools.voice import list_all_voices
        from src.config import config
        
        if not config.validate_elevenlabs_config():
            print("  ⚠ Skipped - ElevenLabs API key not configured")
            return False
        
        print("\n  Listing all voices in account...")
        result = list_all_voices()
        
        if result.get("success"):
            voices = result.get("voices", [])
            count = result.get("count", 0)
            print(f"  ✓ Found {count} voice(s)")
            
            if count > 0:
                print("\n  Voices:")
                for i, voice in enumerate(voices[:5], 1):  # Show first 5
                    print(f"  {i}. {voice.get('name')} (ID: {voice.get('voice_id')[:20]}...)")
                    print(f"     Category: {voice.get('category', 'N/A')}")
                
                if count > 5:
                    print(f"  ... and {count - 5} more")
            
            return True
        else:
            print(f"  ✗ Failed to list voices: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        return False


def test_find_voice_by_name():
    """Test finding a voice by name."""
    print("\n" + "=" * 70)
    print("TEST 6: Find Voice by Name")
    print("=" * 70)
    
    try:
        from src.tools.voice import list_all_voices, find_voice_by_name
        from src.config import config
        
        if not config.validate_elevenlabs_config():
            print("  ⚠ Skipped - ElevenLabs API key not configured")
            return False
        
        # First, list voices to get a name to search for
        list_result = list_all_voices()
        if not list_result.get("success") or list_result.get("count", 0) == 0:
            print("  ⚠ Skipped - No voices available to search")
            return False
        
        # Use the first voice name
        test_voice = list_result["voices"][0]
        test_name = test_voice["name"]
        
        print(f"\n  Searching for voice: '{test_name}'")
        result = find_voice_by_name(test_name)
        
        if result.get("success"):
            voice_id = result.get("voice_id")
            print(f"  ✓ Voice found!")
            print(f"  - Voice ID: {voice_id}")
            print(f"  - Name: {result.get('voice', {}).get('name')}")
            print(f"  - Category: {result.get('voice', {}).get('category')}")
            return True
        else:
            print(f"  ✗ Voice not found: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        return False


def test_reuse_existing_voice():
    """Test reusing an existing voice."""
    print("\n" + "=" * 70)
    print("TEST 7: Reuse Existing Voice")
    print("=" * 70)
    
    try:
        from src.tools.voice import generate_audio_from_script, list_all_voices
        from src.config import config
        
        if not config.validate_elevenlabs_config():
            print("  ⚠ Skipped - ElevenLabs API key not configured")
            return False
        
        # Get an existing voice
        list_result = list_all_voices()
        if not list_result.get("success") or list_result.get("count", 0) == 0:
            print("  ⚠ Skipped - No voices available to reuse")
            return False
        
        # Use the first voice
        test_voice = list_result["voices"][0]
        voice_id = test_voice["voice_id"]
        voice_name = test_voice["name"]
        
        print(f"\n  Reusing voice: '{voice_name}' (ID: {voice_id[:20]}...)")
        
        test_script = "This is a test of voice reuse. The system should use an existing voice without cloning a new one."
        
        print(f"  Generating audio with existing voice...")
        result = generate_audio_from_script(
            script=test_script,
            voice_id=voice_id  # Reuse existing voice by ID
        )
        
        if result.get("success"):
            print(f"  ✓ Audio generated successfully using existing voice!")
            print(f"  - Audio file: {result.get('audio_path')}")
            print(f"  - Voice ID: {result.get('voice_id')}")
            print(f"  - No new voice was cloned (reused existing)")
            return True
        else:
            print(f"  ✗ Audio generation failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def test_voice_name_search():
    """Test using voice_name parameter to find and reuse voice."""
    print("\n" + "=" * 70)
    print("TEST 8: Voice Name Search and Reuse")
    print("=" * 70)
    
    try:
        from src.tools.voice import generate_audio_from_script, list_all_voices
        from src.config import config
        
        if not config.validate_elevenlabs_config():
            print("  ⚠ Skipped - ElevenLabs API key not configured")
            return False
        
        # Get an existing voice
        list_result = list_all_voices()
        if not list_result.get("success") or list_result.get("count", 0) == 0:
            print("  ⚠ Skipped - No voices available")
            return False
        
        # Use the first voice name
        test_voice = list_result["voices"][0]
        voice_name = test_voice["name"]
        
        print(f"\n  Searching for voice by name: '{voice_name}'")
        
        test_script = "Testing voice reuse by name. This should find and use the existing voice."
        
        print(f"  Generating audio using voice name...")
        result = generate_audio_from_script(
            script=test_script,
            voice_name=voice_name  # Reuse by name instead of ID
        )
        
        if result.get("success"):
            print(f"  ✓ Audio generated successfully using voice name!")
            print(f"  - Audio file: {result.get('audio_path')}")
            print(f"  - Voice ID: {result.get('voice_id')}")
            print(f"  - Voice was found by name and reused")
            return True
        else:
            print(f"  ✗ Audio generation failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"  ✗ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all voice generation tests."""
    print("\n" + "=" * 70)
    print("VOICE GENERATION TEST SUITE")
    print("=" * 70)
    print("\nThis test suite verifies:")
    print("1. Audio extraction from video")
    print("2. ElevenLabs API connectivity")
    print("3. Voice cloning workflow")
    print("4. Complete content generation workflow")
    print("5. Listing all voices")
    print("6. Finding voice by name")
    print("7. Reusing existing voice by ID")
    print("8. Reusing existing voice by name")
    print("\nNote: You'll need a sample video file (10-60 seconds with clear speech)")
    print("=" * 70)
    
    results = []
    
    # Run tests
    results.append(("Audio Extraction", test_audio_extraction()))
    results.append(("ElevenLabs Connection", test_elevenlabs_connection()))
    results.append(("Voice Cloning", test_voice_cloning_workflow()))
    results.append(("Complete Workflow", test_complete_workflow()))
    results.append(("List Voices", test_list_voices()))
    results.append(("Find Voice by Name", test_find_voice_by_name()))
    results.append(("Reuse Voice by ID", test_reuse_existing_voice()))
    results.append(("Reuse Voice by Name", test_voice_name_search()))
    
    # Summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED/SKIPPED"
        print(f"{status} - {test_name}")
    
    passed_count = sum(1 for _, passed in results if passed)
    total_count = len(results)
    
    print(f"\nResults: {passed_count}/{total_count} tests passed")
    print("=" * 70)
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! Voice generation is working correctly.")
    elif passed_count > 0:
        print(f"\n⚠ Some tests were skipped or failed. Check configuration and try again.")
    else:
        print(f"\n✗ All tests failed or were skipped. Check your .env configuration.")
    
    return 0 if passed_count > 0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠ Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n✗ FATAL ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

