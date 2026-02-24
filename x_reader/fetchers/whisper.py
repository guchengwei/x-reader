# -*- coding: utf-8 -*-
"""
Shared audio transcription helpers used by youtube.py and twitter.py.

Transcription strategy:
  1. Local mlx-whisper (Apple Silicon, USE_LOCAL_WHISPER=true)
  2. Groq Whisper API fallback (GROQ_API_KEY required)
"""

import os
import subprocess
import time
import requests
from loguru import logger


def _get_audio_duration(audio_path: str) -> float | None:
    """Return audio duration in seconds via ffprobe, or None if unavailable."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet", "-show_entries",
                "format=duration", "-of", "default=noprint_wrappers=1:nokey=1",
                audio_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        return None


def transcribe_local(audio_path: str) -> str:
    """Transcribe audio using mlx-whisper on Apple Silicon. Returns transcript or empty string."""
    try:
        import mlx_whisper
        model = os.getenv("MLX_WHISPER_MODEL", "mlx-community/whisper-large-v3-mlx")
        language = os.getenv("WHISPER_LANGUAGE") or None

        audio_duration = _get_audio_duration(audio_path)
        if audio_duration:
            logger.info(f"[whisper] audio duration: {audio_duration:.1f}s ({audio_duration / 60:.1f}min)")

        lang_hint = f", language={language}" if language else " (auto-detect language)"
        logger.info(f"[whisper] transcribing locally with {model}{lang_hint}")

        t0 = time.monotonic()
        kwargs: dict = dict(
            path_or_hf_repo=model,
            word_timestamps=False,
            condition_on_previous_text=False,
        )
        if language:
            kwargs["language"] = language

        result = mlx_whisper.transcribe(audio_path, **kwargs)
        elapsed = time.monotonic() - t0

        if not isinstance(result, dict):
            logger.warning(f"[whisper] mlx_whisper returned unexpected type: {type(result)}")
            return ""

        text = result.get("text", "").strip()
        if audio_duration and audio_duration > 0:
            rt_factor = audio_duration / elapsed
            logger.info(
                f"[whisper] transcription done in {elapsed:.1f}s "
                f"({rt_factor:.1f}x real-time), {len(text)} chars"
            )
        else:
            logger.info(f"[whisper] transcription done in {elapsed:.1f}s, {len(text)} chars")
        return text
    except Exception as e:
        logger.warning(f"[whisper] local transcription failed: {e}")
        return ""


def transcribe_via_groq(audio_path: str) -> str:
    """
    Transcribe audio via Groq Whisper API.

    Requires GROQ_API_KEY env var.
    Groq Whisper limit: 25MB audio file.
    Returns transcript text, or empty string if unavailable.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        logger.warning("[whisper] GROQ_API_KEY not set — no Groq transcription available")
        return ""

    file_size = os.path.getsize(audio_path)
    logger.info(f"[whisper] transcribing {file_size // 1024}KB via Groq Whisper...")

    try:
        with open(audio_path, "rb") as f:
            response = requests.post(
                "https://api.groq.com/openai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {api_key}"},
                files={"file": (os.path.basename(audio_path), f, "audio/mp4")},
                data={"model": "whisper-large-v3", "response_format": "text"},
                timeout=120,
            )
        if response.status_code == 200:
            transcript = response.text.strip()
            logger.info(f"[whisper] Groq transcript: {len(transcript)} chars")
            return transcript
        else:
            logger.warning(f"[whisper] Groq API error: {response.status_code} {response.text[:200]}")
            return ""
    except Exception as e:
        logger.warning(f"[whisper] Groq transcription failed: {e}")
        return ""


def transcribe_audio(audio_path: str) -> str:
    """
    Transcribe audio file, trying local mlx-whisper first if USE_LOCAL_WHISPER=true,
    falling back to Groq Whisper API.
    """
    use_local = os.getenv("USE_LOCAL_WHISPER", "false").lower() == "true"
    if use_local:
        transcript = transcribe_local(audio_path)
        if transcript:
            return transcript
        logger.info("[whisper] local transcription empty, falling back to Groq")
    return transcribe_via_groq(audio_path)
