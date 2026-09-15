import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from tools.video import generate_video_from_video

# Test with your files
result = generate_video_from_video(
    video_path="test_content/test.mp4",
    audio_path="test_content/generated_content_57679.mp3",
    frame_timestamp=2.0  # Extract frame at 2 seconds
)

if result.get("success"):
    print(f"✓ Success!")
    print(f"Video saved to: {result['video_path']}")
    print(f"Frame extracted: {result['frame_path']}")
else:
    print(f"✗ Failed: {result.get('error')}")