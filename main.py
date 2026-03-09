"""
MockStar - AI Interview Preparation Platform
Speech Processing Pipeline using FastAPI and OpenAI Whisper

This service provides audio transcription capabilities with support for:
- Asynchronous file processing
- Multiple audio formats (WAV, M4A, MP3, FLAC, OGG)
- Session tracking
- Error handling and validation
"""

import os
import uuid
import logging
from pathlib import Path
from typing import Optional
import asyncio
from datetime import datetime

import whisper
from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiofiles

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="MockStar Speech Processing API",
    description="Audio transcription service for AI interview preparation",
    version="1.0.0"
)

# CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Supported audio formats
SUPPORTED_FORMATS = {".wav", ".m4a", ".mp3", ".flac", ".ogg", ".webm"}
MAX_FILE_SIZE = 25 * 1024 * 1024  # 25 MB limit

# Whisper model configuration
# Options: "tiny", "base", "small", "medium", "large"
# Trade-off: larger models = better accuracy but slower processing
WHISPER_MODEL_SIZE = os.getenv("WHISPER_MODEL_SIZE", "base")

# Global model instance (loaded once at startup)
whisper_model = None


# Response models
class TranscriptionResponse(BaseModel):
    session_id: str
    transcript: str
    language: Optional[str] = None
    duration: Optional[float] = None
    confidence: Optional[float] = None
    timestamp: str


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    model_size: str


# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Load Whisper model at startup to avoid cold start delays"""
    global whisper_model
    try:
        logger.info(f"Loading Whisper model: {WHISPER_MODEL_SIZE}")
        # Run model loading in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        whisper_model = await loop.run_in_executor(
            None,
            whisper.load_model,
            WHISPER_MODEL_SIZE
        )
        logger.info("Whisper model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load Whisper model: {str(e)}")
        raise


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down service")
    # Clean up temporary files if needed
    cleanup_old_uploads()


# Helper functions
def validate_audio_file(filename: str) -> bool:
    """Validate if the uploaded file has a supported audio format"""
    file_ext = Path(filename).suffix.lower()
    return file_ext in SUPPORTED_FORMATS


def cleanup_old_uploads(max_age_hours: int = 24):
    """Remove upload files older than max_age_hours"""
    try:
        current_time = datetime.now().timestamp()
        for file_path in UPLOAD_DIR.glob("*"):
            if file_path.is_file():
                file_age = current_time - file_path.stat().st_mtime
                if file_age > max_age_hours * 3600:
                    file_path.unlink()
                    logger.info(f"Deleted old file: {file_path.name}")
    except Exception as e:
        logger.error(f"Error during cleanup: {str(e)}")


async def save_upload_file(upload_file: UploadFile, destination: Path) -> None:
    """Asynchronously save uploaded file to disk"""
    try:
        async with aiofiles.open(destination, 'wb') as out_file:
            # Read and write in chunks to handle large files
            while content := await upload_file.read(1024 * 1024):  # 1MB chunks
                await out_file.write(content)
    except Exception as e:
        logger.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail="Error saving uploaded file")


async def transcribe_audio(file_path: Path) -> dict:
    """
    Asynchronously transcribe audio file using Whisper

    Args:
        file_path: Path to the audio file

    Returns:
        Dictionary containing transcription results
    """
    try:
        logger.info(f"Starting transcription for: {file_path.name}")

        # Run Whisper transcription in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            whisper_model.transcribe,
            str(file_path),
            # Additional Whisper parameters for better results
            {
                "fp16": False,  # Use FP32 for CPU, FP16 for GPU
                "language": None,  # Auto-detect language
                "task": "transcribe",  # Options: "transcribe" or "translate"
                "verbose": False,
            }
        )

        logger.info(f"Transcription completed for: {file_path.name}")

        return {
            "text": result["text"].strip(),
            "language": result.get("language", "unknown"),
            "segments": result.get("segments", []),
        }

    except Exception as e:
        logger.error(f"Transcription error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")


def cleanup_file(file_path: Path):
    """Background task to clean up temporary file"""
    try:
        if file_path.exists():
            file_path.unlink()
            logger.info(f"Cleaned up file: {file_path.name}")
    except Exception as e:
        logger.error(f"Error cleaning up file {file_path}: {str(e)}")


# API Endpoints
@app.get("/", response_model=HealthResponse)
async def root():
    """Health check endpoint"""
    return HealthResponse(
        status="online",
        model_loaded=whisper_model is not None,
        model_size=WHISPER_MODEL_SIZE
    )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check"""
    return HealthResponse(
        status="healthy" if whisper_model is not None else "degraded",
        model_loaded=whisper_model is not None,
        model_size=WHISPER_MODEL_SIZE
    )


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe(
    background_tasks: BackgroundTasks,
    audio_file: UploadFile = File(..., description="Audio file to transcribe")
):
    """
    Transcribe uploaded audio file

    **Batch Upload Approach (Current Implementation):**
    - Client uploads complete audio file
    - Server processes entire file and returns transcript
    - Suitable for: Post-interview analysis, file-based recordings
    - Pros: Simple, reliable, works with any audio length
    - Cons: Higher latency, user waits for complete upload + processing

    **Streaming Approach (WebSocket Alternative):**
    For lower latency real-time transcription, consider WebSocket implementation:

    ```python
    @app.websocket("/transcribe/stream")
    async def transcribe_stream(websocket: WebSocket):
        await websocket.accept()
        audio_buffer = bytearray()

        while True:
            # Receive audio chunks
            chunk = await websocket.receive_bytes()
            audio_buffer.extend(chunk)

            # Process when buffer reaches threshold (e.g., 5 seconds of audio)
            if len(audio_buffer) >= CHUNK_THRESHOLD:
                transcript = await process_chunk(audio_buffer)
                await websocket.send_json({"partial": transcript})
                audio_buffer.clear()
    ```

    **Optimization Strategies:**
    - Use Whisper with VAD (Voice Activity Detection) for streaming
    - Implement chunked processing with overlap for better accuracy
    - Use smaller models (tiny/base) for real-time, larger for final transcript
    - Consider cloud APIs (OpenAI Whisper API, AssemblyAI) for production scale
    - Implement caching for repeated audio patterns
    - Use GPU acceleration (CUDA) for faster processing
    """

    # Generate unique session ID
    session_id = str(uuid.uuid4())
    start_time = datetime.now()

    # Validate model is loaded
    if whisper_model is None:
        raise HTTPException(
            status_code=503,
            detail="Transcription service not ready. Model not loaded."
        )

    # Validate file format
    if not validate_audio_file(audio_file.filename):
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported formats: {', '.join(SUPPORTED_FORMATS)}"
        )

    # Validate file size
    file_size = 0
    temp_file_path = None

    try:
        # Create temporary file path with session ID
        file_extension = Path(audio_file.filename).suffix
        temp_file_path = UPLOAD_DIR / f"{session_id}{file_extension}"

        # Save uploaded file
        await save_upload_file(audio_file, temp_file_path)

        # Check file size after upload
        file_size = temp_file_path.stat().st_size
        if file_size > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )

        if file_size == 0:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty"
            )

        # Perform transcription
        transcription_result = await transcribe_audio(temp_file_path)

        # Calculate processing duration
        processing_duration = (datetime.now() - start_time).total_seconds()

        # Schedule file cleanup in background
        background_tasks.add_task(cleanup_file, temp_file_path)

        logger.info(f"Session {session_id}: Transcription successful ({processing_duration:.2f}s)")

        return TranscriptionResponse(
            session_id=session_id,
            transcript=transcription_result["text"],
            language=transcription_result.get("language"),
            duration=processing_duration,
            confidence=None,  # Whisper doesn't provide overall confidence score
            timestamp=datetime.now().isoformat()
        )

    except HTTPException:
        # Re-raise HTTP exceptions
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
        raise

    except Exception as e:
        logger.error(f"Session {session_id}: Unexpected error: {str(e)}")
        if temp_file_path and temp_file_path.exists():
            temp_file_path.unlink()
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error during transcription: {str(e)}"
        )


@app.delete("/cleanup")
async def manual_cleanup():
    """Manually trigger cleanup of old upload files"""
    cleanup_old_uploads(max_age_hours=1)
    return {"status": "cleanup completed"}


# Additional endpoint for batch processing (future enhancement)
@app.post("/transcribe/batch")
async def transcribe_batch(audio_files: list[UploadFile] = File(...)):
    """
    Process multiple audio files in batch
    Returns list of session IDs for tracking
    """
    session_ids = []

    for audio_file in audio_files:
        if not validate_audio_file(audio_file.filename):
            continue

        session_id = str(uuid.uuid4())
        session_ids.append({
            "filename": audio_file.filename,
            "session_id": session_id,
            "status": "queued"
        })

    # In production, implement actual batch processing with task queue (Celery, RQ)
    return {
        "batch_id": str(uuid.uuid4()),
        "sessions": session_ids,
        "message": "Batch processing queued"
    }


if __name__ == "__main__":
    import uvicorn

    # Run the application
    # For development: uvicorn main:app --reload --host 0.0.0.0 --port 8000
    # For production: Use gunicorn with uvicorn workers
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Disable in production
        log_level="info"
    )
