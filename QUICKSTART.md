# 🚀 Quick Start Guide - MockStar Speech Processing

Get your transcription service running in under 5 minutes!

## 📋 Prerequisites Checklist

- [ ] Python 3.9+ installed (`python --version`)
- [ ] FFmpeg installed (required by Whisper)

### Install FFmpeg (if needed)

```bash
# macOS
brew install ffmpeg

# Ubuntu/Debian
sudo apt install ffmpeg

# Verify installation
ffmpeg -version
```

## ⚡ Quick Setup (3 steps)

### 1. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# OR
venv\Scripts\activate  # Windows
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** First installation will take 3-5 minutes as it downloads:
- PyTorch (~2GB)
- Whisper model (~140MB for base model)
- Other dependencies

### 3. Run the Service

```bash
python main.py
```

You should see:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Loading Whisper model: base
INFO:     Whisper model loaded successfully
```

## ✅ Verify It's Working

### Option 1: Browser

Open http://localhost:8000/docs in your browser to see interactive API documentation.

### Option 2: Test Script

```bash
# Test health check only
python test_api.py

# Test with your audio file
python test_api.py path/to/your/audio.mp3
```

### Option 3: cURL

```bash
# Health check
curl http://localhost:8000/health

# Transcribe (replace with your audio file)
curl -X POST "http://localhost:8000/transcribe" \
  -F "audio_file=@sample.mp3"
```

## 📝 Example Response

```json
{
  "session_id": "a8b9c0d1-e2f3-4a5b-6c7d-8e9f0a1b2c3d",
  "transcript": "Hello, this is a test of the transcription service.",
  "language": "en",
  "duration": 1.23,
  "confidence": null,
  "timestamp": "2024-01-15T10:30:00.123456"
}
```

## 🎯 Common Use Cases

### 1. Single File Transcription

```python
import requests

response = requests.post(
    "http://localhost:8000/transcribe",
    files={"audio_file": open("interview.mp3", "rb")}
)

result = response.json()
print(result["transcript"])
```

### 2. Batch Processing

```python
import asyncio
from example_client import MockStarTranscriptionClient

async def process_multiple():
    client = MockStarTranscriptionClient()
    files = ["interview1.mp3", "interview2.mp3", "interview3.mp3"]

    tasks = [client.transcribe(f) for f in files]
    results = await asyncio.gather(*tasks)

    for result in results:
        print(result["transcript"])

asyncio.run(process_multiple())
```

### 3. Frontend Integration (React)

```javascript
async function transcribeAudio(audioFile) {
  const formData = new FormData();
  formData.append('audio_file', audioFile);

  const response = await fetch('http://localhost:8000/transcribe', {
    method: 'POST',
    body: formData
  });

  const result = await response.json();
  return result.transcript;
}
```

## ⚙️ Configuration

### Change Whisper Model Size

```bash
# Set environment variable
export WHISPER_MODEL_SIZE=small  # Options: tiny, base, small, medium, large

# Then run
python main.py
```

### Production Deployment

```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 🐛 Troubleshooting

### Issue: "FFmpeg not found"
**Solution:** Install FFmpeg (see Prerequisites)

### Issue: Slow transcription
**Solutions:**
1. Use smaller model: `tiny` or `base`
2. Enable GPU acceleration (if you have NVIDIA GPU)
3. Consider cloud APIs for production

### Issue: Out of memory
**Solutions:**
1. Use `tiny` model
2. Reduce max file size
3. Add more RAM or use cloud service

### Issue: Port 8000 already in use
**Solution:**
```bash
# Use different port
uvicorn main:app --port 8080
```

## 📊 Performance Expectations

| Model | Speed | Quality | Recommended For |
|-------|-------|---------|-----------------|
| tiny  | ~32x realtime | Basic | Quick tests |
| **base** | ~16x realtime | Good | **Development** |
| small | ~6x realtime | Better | Production |
| medium | ~2x realtime | Great | High quality |
| large | ~1x realtime | Best | Maximum accuracy |

*Speed relative to audio duration (e.g., 16x = 60s audio processes in ~4s)*

## 🎓 Next Steps

1. **Read the Full Documentation:** Check [README.md](README.md)
2. **Explore API Docs:** Visit http://localhost:8000/docs
3. **Try Examples:** Run code in [example_client.py](example_client.py)
4. **Production Setup:** See README for scaling strategies

## 📚 Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [OpenAI Whisper GitHub](https://github.com/openai/whisper)
- [Whisper Model Card](https://github.com/openai/whisper/blob/main/model-card.md)

## 💡 Tips

1. **Use GPU for production:** Install CUDA-enabled PyTorch
2. **Implement caching:** Store common transcriptions
3. **Add authentication:** Protect your API in production
4. **Monitor usage:** Track API calls and costs
5. **Consider cloud APIs:** For scale, use OpenAI/AssemblyAI APIs

---

**Need help?** Check README.md for detailed documentation!

**Ready for production?** See deployment strategies in README.md!
