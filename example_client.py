"""
Example client for integrating MockStar Speech Processing API
into a frontend or another service
"""

import asyncio
import aiohttp
from pathlib import Path
from typing import Optional, Dict


class MockStarTranscriptionClient:
    """
    Async client for MockStar Speech Processing API

    Example usage:
        client = MockStarTranscriptionClient("http://localhost:8000")
        result = await client.transcribe("interview_audio.mp3")
        print(result["transcript"])
    """

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")

    async def health_check(self) -> Dict:
        """Check if the service is healthy"""
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{self.base_url}/health") as response:
                response.raise_for_status()
                return await response.json()

    async def transcribe(self, audio_file_path: str) -> Optional[Dict]:
        """
        Transcribe an audio file

        Args:
            audio_file_path: Path to the audio file

        Returns:
            Dictionary with transcription results or None if failed
        """
        file_path = Path(audio_file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_file_path}")

        async with aiohttp.ClientSession() as session:
            # Create form data
            data = aiohttp.FormData()
            data.add_field(
                'audio_file',
                open(file_path, 'rb'),
                filename=file_path.name,
                content_type='audio/mpeg'  # Adjust based on file type
            )

            # Send request
            async with session.post(
                f"{self.base_url}/transcribe",
                data=data
            ) as response:
                response.raise_for_status()
                return await response.json()

    async def transcribe_with_progress(
        self,
        audio_file_path: str,
        progress_callback=None
    ) -> Optional[Dict]:
        """
        Transcribe with upload progress tracking

        Args:
            audio_file_path: Path to the audio file
            progress_callback: Function to call with progress (0-100)

        Returns:
            Dictionary with transcription results
        """
        file_path = Path(audio_file_path)
        file_size = file_path.stat().st_size

        async with aiohttp.ClientSession() as session:
            with open(file_path, 'rb') as f:
                # Wrap file for progress tracking
                class ProgressFile:
                    def __init__(self, file_obj):
                        self.file = file_obj
                        self.bytes_read = 0

                    def read(self, size=-1):
                        chunk = self.file.read(size)
                        self.bytes_read += len(chunk)

                        if progress_callback:
                            progress = (self.bytes_read / file_size) * 100
                            progress_callback(progress)

                        return chunk

                progress_file = ProgressFile(f)

                data = aiohttp.FormData()
                data.add_field(
                    'audio_file',
                    progress_file,
                    filename=file_path.name
                )

                async with session.post(
                    f"{self.base_url}/transcribe",
                    data=data
                ) as response:
                    response.raise_for_status()
                    return await response.json()


# Example usage functions
async def example_basic_transcription():
    """Basic transcription example"""
    client = MockStarTranscriptionClient()

    # Check service health
    health = await client.health_check()
    print(f"Service status: {health['status']}")

    # Transcribe audio file
    result = await client.transcribe("sample_audio.mp3")

    if result:
        print(f"Session ID: {result['session_id']}")
        print(f"Transcript: {result['transcript']}")
        print(f"Language: {result['language']}")


async def example_with_progress():
    """Transcription with progress tracking"""
    client = MockStarTranscriptionClient()

    def on_progress(percent: float):
        print(f"Upload progress: {percent:.1f}%", end='\r')

    result = await client.transcribe_with_progress(
        "large_audio_file.mp3",
        progress_callback=on_progress
    )

    print(f"\nTranscript: {result['transcript']}")


async def example_batch_processing():
    """Process multiple audio files"""
    client = MockStarTranscriptionClient()

    audio_files = [
        "interview_1.mp3",
        "interview_2.mp3",
        "interview_3.mp3"
    ]

    # Process all files concurrently
    tasks = [client.transcribe(file) for file in audio_files]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for file, result in zip(audio_files, results):
        if isinstance(result, Exception):
            print(f"❌ {file}: {result}")
        else:
            print(f"✅ {file}: {result['transcript'][:100]}...")


async def example_error_handling():
    """Demonstrate error handling"""
    client = MockStarTranscriptionClient()

    try:
        result = await client.transcribe("nonexistent.mp3")
    except FileNotFoundError as e:
        print(f"File error: {e}")
    except aiohttp.ClientResponseError as e:
        print(f"API error: {e.status} - {e.message}")
    except Exception as e:
        print(f"Unexpected error: {e}")


# Integration with web frameworks
class FastAPIIntegrationExample:
    """
    Example: Using the client in a FastAPI application
    """

    def __init__(self):
        self.transcription_client = MockStarTranscriptionClient()

    async def process_interview_recording(self, user_id: str, audio_path: str):
        """Process interview recording and store results"""

        # Transcribe
        result = await self.transcription_client.transcribe(audio_path)

        # Store in database (example)
        interview_data = {
            "user_id": user_id,
            "session_id": result["session_id"],
            "transcript": result["transcript"],
            "language": result["language"],
            "timestamp": result["timestamp"]
        }

        # Save to database
        # await db.interviews.insert_one(interview_data)

        return interview_data


class ReactIntegrationExample:
    """
    Example: JavaScript/React frontend integration

    ```javascript
    // React component example
    async function uploadAndTranscribe(audioFile) {
        const formData = new FormData();
        formData.append('audio_file', audioFile);

        try {
            const response = await fetch('http://localhost:8000/transcribe', {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const result = await response.json();
            console.log('Transcript:', result.transcript);
            console.log('Session ID:', result.session_id);

            return result;
        } catch (error) {
            console.error('Transcription failed:', error);
            throw error;
        }
    }

    // Usage in React component
    function InterviewRecorder() {
        const [transcript, setTranscript] = useState('');
        const [isProcessing, setIsProcessing] = useState(false);

        const handleFileUpload = async (event) => {
            const file = event.target.files[0];
            setIsProcessing(true);

            try {
                const result = await uploadAndTranscribe(file);
                setTranscript(result.transcript);
            } catch (error) {
                alert('Transcription failed');
            } finally {
                setIsProcessing(false);
            }
        };

        return (
            <div>
                <input
                    type="file"
                    accept="audio/*"
                    onChange={handleFileUpload}
                    disabled={isProcessing}
                />
                {isProcessing && <p>Processing...</p>}
                {transcript && <p>Transcript: {transcript}</p>}
            </div>
        );
    }
    ```
    """
    pass


if __name__ == "__main__":
    # Run example
    print("MockStar Transcription Client Examples")
    print("=" * 50)
    print("\nUncomment the example you want to run:\n")

    # asyncio.run(example_basic_transcription())
    # asyncio.run(example_with_progress())
    # asyncio.run(example_batch_processing())
    # asyncio.run(example_error_handling())

    print("Edit example_client.py to run specific examples")
