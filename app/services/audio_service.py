import os
import uuid
from typing import Optional
from fastapi import HTTPException
from app.core.config import settings

class AudioService:
    def __init__(self):
        # We use OpenAI for STT and TTS if a key is provided
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                from openai import AsyncOpenAI
                self.client = AsyncOpenAI(api_key=self.api_key)
            except ImportError:
                print("OpenAI library not installed.")

    async def transcribe_audio(self, file_path: str) -> str:
        """Convert speech to text using OpenAI Whisper."""
        if not self.client:
            print("AudioService: No OpenAI API Key, using mock transcription.")
            return "This is a mock transcription because OpenAI is not configured."
            
        try:
            with open(file_path, "rb") as audio_file:
                transcript = await self.client.audio.transcriptions.create(
                    model="whisper-1", 
                    file=audio_file
                )
            return transcript.text
        except Exception as e:
            print(f"STT Error: {e}")
            raise HTTPException(status_code=500, detail=f"Transcription failed: {str(e)}")

    async def synthesize_speech(self, text: str) -> str:
        """Convert text to speech using OpenAI TTS. Returns the file path to the audio."""
        if not self.client:
            print("AudioService: No OpenAI API Key, using mock synthesis.")
            raise HTTPException(status_code=501, detail="TTS not configured (requires OpenAI API key)")
            
        try:
            response = await self.client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=text
            )
            
            # Save audio to storage
            os.makedirs(settings.STORAGE_PATH, exist_ok=True)
            filename = f"tts_{uuid.uuid4().hex}.mp3"
            file_path = os.path.join(settings.STORAGE_PATH, filename)
            
            if hasattr(response, "write_to_file"):
                response.write_to_file(file_path)
            elif hasattr(response, "aread"):
                content = await response.aread()
                with open(file_path, "wb") as f:
                    f.write(content)
            elif hasattr(response, "read"):
                with open(file_path, "wb") as f:
                    f.write(response.read())
            elif hasattr(response, "stream_to_file"):
                response.stream_to_file(file_path)
            else:
                with open(file_path, "wb") as f:
                    f.write(await response.response.aread())
            return file_path
        except Exception as e:
            print(f"TTS Error: {e}")
            raise HTTPException(status_code=500, detail=f"Speech synthesis failed: {str(e)}")

audio_service = AudioService()
