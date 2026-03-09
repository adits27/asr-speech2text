# MockStar - Speech Processing Pipeline

AI-powered audio transcription service for the MockStar interview preparation platform.

## Features

- **Asynchronous Processing**: Non-blocking audio transcription using FastAPI
- **Multiple Audio Formats**: Support for WAV, M4A, MP3, FLAC, OGG, WebM
- **OpenAI Whisper Integration**: State-of-the-art speech recognition
- **Session Tracking**: Unique session IDs for each transcription request
- **Error Handling**: Comprehensive validation and error management
- **Production Ready**: CORS, logging, health checks, and cleanup mechanisms

## Quick Start

### Prerequisites

- Python 3.9 or higher
- FFmpeg (required by Whisper)

#### Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg
```

**Windows:**
Download from [ffmpeg.org](https://ffmpeg.org/download.html)

### Installation

1. **Clone the repository:**
```bash
cd /Users/adithyasubramaniam/Desktop/capstone/asr-speech2text
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

### Running the Service

**Development mode:**
```bash
python main.py
```

**Or using uvicorn directly:**
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Production mode (with Gunicorn):**
```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- **Interactive API docs (Swagger)**: http://localhost:8000/docs
- **Alternative docs (ReDoc)**: http://localhost:8000/redoc

### Endpoints

#### `POST /transcribe`

Transcribe an audio file.

**Request:**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "audio_file=@/path/to/audio.mp3"
```

**Response:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "transcript": "This is the transcribed text from the audio file.",
  "language": "en",
  "duration": 2.45,
  "confidence": null,
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

#### `GET /health`

Check service health status.

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_size": "base"
}
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Whisper model size: tiny, base, small, medium, large
WHISPER_MODEL_SIZE=base

# Server configuration
HOST=0.0.0.0
PORT=8000

# File upload limits (bytes)
MAX_FILE_SIZE=26214400  # 25MB
```

### Model Selection

Choose Whisper model based on your requirements:

| Model  | Parameters | Speed    | Accuracy | Use Case                    |
|--------|-----------|----------|----------|-----------------------------|
| tiny   | 39M       | ~32x     | Basic    | Real-time, low resource     |
| base   | 74M       | ~16x     | Good     | **Recommended for most**    |
| small  | 244M      | ~6x      | Better   | Higher accuracy needed      |
| medium | 769M      | ~2x      | Great    | Production quality          |
| large  | 1550M     | 1x       | Best     | Maximum accuracy            |

## Batch vs. Streaming Processing

### Current Implementation: Batch Upload

- User uploads complete audio file
- Server processes and returns full transcript
- Best for: Post-interview analysis, recorded sessions

### Future: WebSocket Streaming (Lower Latency)

For real-time transcription during live interviews:

```python
# Example WebSocket implementation (see main.py comments)
@app.websocket("/transcribe/stream")
async def transcribe_stream(websocket: WebSocket):
    # Stream audio chunks
    # Process incrementally
    # Return partial transcripts
```

**Benefits of streaming:**
- Lower perceived latency
- Real-time feedback during interviews
- Better user experience

**Trade-offs:**
- More complex implementation
- Requires chunking and buffering
- May reduce accuracy at chunk boundaries

## Performance Optimization

### For Production Use

1. **GPU Acceleration:**
```bash
# Install PyTorch with CUDA support
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

2. **Use Cloud APIs** (for scale):
   - OpenAI Whisper API
   - AssemblyAI
   - Google Speech-to-Text
   - AWS Transcribe

3. **Implement Task Queue** (Celery + Redis):
```bash
pip install celery redis
```

4. **Caching**:
   - Cache common audio patterns
   - Store processed transcripts

5. **Load Balancing**:
   - Multiple worker instances
   - Nginx reverse proxy
   - Kubernetes for container orchestration

## Testing

### Manual Testing with cURL

```bash
# Test with sample audio
curl -X POST "http://localhost:8000/transcribe" \
  -F "audio_file=@test_audio.mp3"

# Health check
curl http://localhost:8000/health
```

### Python Script Example

```python
import requests

url = "http://localhost:8000/transcribe"
files = {"audio_file": open("interview_recording.mp3", "rb")}

response = requests.post(url, files=files)
print(response.json())
```

## Project Structure

```
asr-speech2text/
├── main.py              # FastAPI application
├── requirements.txt     # Python dependencies
├── README.md           # This file
├── uploads/            # Temporary audio files (auto-created)
└── .env               # Environment variables (create this)
```

## Troubleshooting

### Common Issues

**1. FFmpeg not found:**
```
RuntimeError: ffmpeg not found
```
**Solution:** Install FFmpeg (see Prerequisites)

**2. Model download fails:**
```
ConnectionError: Unable to download model
```
**Solution:** Check internet connection, model will download on first run

**3. Out of memory:**
```
RuntimeError: CUDA out of memory
```
**Solution:** Use smaller model (tiny/base) or increase system RAM

**4. Slow transcription:**
- Use GPU acceleration
- Choose smaller Whisper model
- Consider cloud API for production

## Future Enhancements

- Implement WebSocket streaming for real-time transcription
- Add authentication (JWT tokens)
- Integrate with database for session persistence
- Add support for speaker diarization
- Implement transcript confidence scores
- Add language translation capabilities
- Build frontend client
- Deploy to cloud (AWS/GCP/Azure)

## License

MIT License

## Support

For issues or questions:
- Check the [FastAPI documentation](https://fastapi.tiangolo.com/)
- Review [OpenAI Whisper docs](https://github.com/openai/whisper)
- Open an issue in your repository

---

MockStar Interview Preparation Platform - Speech Processing Pipeline
