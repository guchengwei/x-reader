# -*- coding: utf-8 -*-
"""
YouTube video fetcher — extracts subtitles via yt-dlp, falls back to Jina.

Priority: auto-subtitles (full transcript) > Jina (page description only).
Requires: yt-dlp installed (brew install yt-dlp / pip install yt-dlp)
"""

import re
import os
import subprocess
import tempfile
from loguru import logger
from typing import Dict, Any

from x_reader.fetchers.jina import fetch_via_jina


def _extract_video_id(url: str) -> str:
    """Extract video ID from YouTube URL."""
    match = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return match.group(1) if match else ""


def _get_subtitles_via_ytdlp(url: str, lang: str = "en") -> str:
    """
    Download auto-generated subtitles using yt-dlp.
    Returns subtitle text, or empty string if unavailable.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "sub")

        # Try auto-generated subtitles first, then manual subs
        cmd = [
            "yt-dlp",
            "--write-auto-sub",
            "--write-sub",
            "--sub-lang", lang,
            "--sub-format", "srt",
            "--skip-download",
            "-o", output_path,
            url,
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except FileNotFoundError:
            logger.warning("yt-dlp not found. Install with: brew install yt-dlp")
            return ""
        except subprocess.TimeoutExpired:
            logger.warning("yt-dlp subtitle download timed out")
            return ""

        # Look for the subtitle file
        for ext in [f".{lang}.srt", f".{lang}.vtt"]:
            sub_file = output_path + ext
            if os.path.exists(sub_file):
                return _parse_srt(sub_file)

    return ""


def _parse_srt(filepath: str) -> str:
    """Parse SRT file into clean text (strip timestamps and sequence numbers)."""
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    text_lines = []
    seen = set()

    for line in lines:
        line = line.strip()
        # Skip sequence numbers, timestamps, empty lines
        if not line:
            continue
        if line.isdigit():
            continue
        if '-->' in line:
            continue
        # Skip [Music] etc.
        if line.startswith('[') and line.endswith(']'):
            continue
        # Dedup overlapping subtitle segments
        if line not in seen:
            seen.add(line)
            text_lines.append(line)

    return " ".join(text_lines)


async def fetch_youtube(url: str, sub_lang: str = "en") -> Dict[str, Any]:
    """
    Fetch YouTube video content.

    Strategy:
    1. Try yt-dlp to get auto-generated subtitles (full transcript)
    2. Fall back to Jina Reader (page description only)

    Args:
        url: YouTube video URL
        sub_lang: Subtitle language code (default: "en")

    Returns:
        Dict with: title, description, author, url, transcript
    """
    logger.info(f"Fetching YouTube: {url}")
    video_id = _extract_video_id(url)

    # Step 1: Get metadata via Jina (fast, always works)
    jina_data = fetch_via_jina(url)
    title = jina_data["title"]

    # Step 2: Try to get full transcript via yt-dlp
    logger.info(f"Extracting subtitles ({sub_lang})...")
    transcript = _get_subtitles_via_ytdlp(url, lang=sub_lang)

    if transcript:
        logger.info(f"Got transcript: {len(transcript)} chars")
        content = transcript
        has_transcript = True
    else:
        logger.info("No subtitles available, using page description")
        content = jina_data["content"]
        has_transcript = False

    return {
        "title": title,
        "description": content,
        "author": jina_data.get("author", ""),
        "url": url,
        "video_id": video_id,
        "has_transcript": has_transcript,
        "platform": "youtube",
    }
