"""
Test script for MockStar Speech Processing API

This script demonstrates how to interact with the transcription API
"""

import requests
import sys
from pathlib import Path


def test_health_check(base_url: str = "http://localhost:8000"):
    """Test the health check endpoint"""
    print("🏥 Testing health check...")
    try:
        response = requests.get(f"{base_url}/health")
        response.raise_for_status()
        data = response.json()

        print(f"✅ Status: {data['status']}")
        print(f"✅ Model Loaded: {data['model_loaded']}")
        print(f"✅ Model Size: {data['model_size']}")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {str(e)}")
        return False


def test_transcription(audio_file_path: str, base_url: str = "http://localhost:8000"):
    """Test the transcription endpoint"""
    print(f"\n🎤 Testing transcription with: {audio_file_path}")

    # Check if file exists
    if not Path(audio_file_path).exists():
        print(f"❌ File not found: {audio_file_path}")
        return False

    try:
        # Open and send file
        with open(audio_file_path, 'rb') as audio_file:
            files = {'audio_file': audio_file}
            response = requests.post(f"{base_url}/transcribe", files=files)
            response.raise_for_status()

        # Parse response
        data = response.json()

        print("\n📝 Transcription Results:")
        print(f"Session ID: {data['session_id']}")
        print(f"Language: {data['language']}")
        print(f"Duration: {data['duration']:.2f}s")
        print(f"Timestamp: {data['timestamp']}")
        print(f"\nTranscript:\n{'-' * 50}")
        print(data['transcript'])
        print('-' * 50)

        return True

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if e.response:
            print(f"Response: {e.response.json()}")
        return False
    except Exception as e:
        print(f"❌ Transcription failed: {str(e)}")
        return False


def main():
    """Main test function"""
    print("=" * 60)
    print("MockStar Speech Processing API - Test Suite")
    print("=" * 60)

    base_url = "http://localhost:8000"

    # Test 1: Health Check
    if not test_health_check(base_url):
        print("\n⚠️  Service not available. Make sure the API is running:")
        print("   python main.py")
        sys.exit(1)

    # Test 2: Transcription
    if len(sys.argv) > 1:
        audio_file = sys.argv[1]
        test_transcription(audio_file, base_url)
    else:
        print("\n💡 To test transcription, run:")
        print("   python test_api.py path/to/audio/file.mp3")
        print("\nSupported formats: .wav, .m4a, .mp3, .flac, .ogg, .webm")

    print("\n✨ Testing complete!")


if __name__ == "__main__":
    main()
