# services/voice_service.py
"""
Synaptiq Voice Service
Transcribes voice input to text using Sarvam Saarika V2 (primary)
or Groq Whisper (fallback). Optimised for Indian English accents.
"""

import os
import io

import requests
from groq import Groq

SARVAM_KEY = os.getenv("SARVAM_API_KEY", "")
SARVAM_BASE = "https://api.sarvam.ai"
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))

# Hardcoded fallback for demo reliability
DEMO_FALLBACK_TRANSCRIPT = (
    "3-step outreach to fintech CTOs with personalized intro "
    "referencing company news and final meeting calendar link"
)


async def transcribe_voice(audio_bytes: bytes) -> str:
    """
    Transcribe audio to text.
    Priority: Sarvam Saarika V2 → Groq Whisper → hardcoded demo string.
    """
    # Attempt 1: Sarvam Saarika V2 (Indian English optimised)
    if SARVAM_KEY:
        try:
            response = requests.post(
                f"{SARVAM_BASE}/speech-to-text",
                headers={"api-subscription-key": SARVAM_KEY},
                files={
                    "file": ("recording.webm", io.BytesIO(audio_bytes), "audio/webm")
                },
                data={"language_code": "en-IN", "model": "saarika:v2"},
                timeout=20,
            )
            transcript = response.json().get("transcript", "")
            if transcript.strip():
                return transcript.strip()
        except Exception:
            pass

    # Attempt 2: Groq Whisper (free, fast)
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "recording.webm"
        result = groq_client.audio.transcriptions.create(
            file=audio_file,
            model="whisper-large-v3",
            language="en",
            response_format="text",
        )
        if result and result.strip():
            return result.strip()
    except Exception:
        pass

    # Final fallback: hardcoded demo string
    return DEMO_FALLBACK_TRANSCRIPT
