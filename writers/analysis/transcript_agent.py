#!/usr/bin/env python3
"""
Transcript Agent - The Sound Department
One job: Get the words. Captions or Whisper. That's it.

Usage:
    from transcript_agent import get_transcript, transcribe_audio
"""

import os
import subprocess
import tempfile

# Whisper model - can upgrade to "medium" or "large-v3" for accuracy
WHISPER_MODEL = "base"


def get_captions(url: str, work_dir: str = None) -> str:
    """Try to get existing captions from YouTube"""
    if work_dir is None:
        work_dir = tempfile.mkdtemp(prefix="transcript_")

    try:
        caption_file = os.path.join(work_dir, "captions")
        cmd = [
            "yt-dlp",
            "--write-auto-sub",
            "--sub-lang", "en",
            "--skip-download",
            "--convert-subs", "srt",
            "-o", caption_file,
            url
        ]

        subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Find the caption file
        for f in os.listdir(work_dir):
            if f.endswith('.srt') or f.endswith('.vtt'):
                caption_path = os.path.join(work_dir, f)
                with open(caption_path, 'r', encoding='utf-8', errors='ignore') as cf:
                    content = cf.read()
                    # Clean SRT format - remove timestamps and numbers
                    lines = []
                    for line in content.split('\n'):
                        line = line.strip()
                        if line and not line.isdigit() and '-->' not in line:
                            lines.append(line)
                    return ' '.join(lines)

        return ""

    except Exception as e:
        print(f"[SOUND] Caption fetch failed: {e}")
        return ""


def transcribe_audio(audio_path: str) -> str:
    """Transcribe audio file with Whisper"""
    try:
        from faster_whisper import WhisperModel

        print(f"[SOUND] Transcribing with Whisper ({WHISPER_MODEL})...")

        model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        segments, info = model.transcribe(audio_path, beam_size=5)

        transcript_parts = []
        for segment in segments:
            transcript_parts.append(segment.text)

        transcript = ' '.join(transcript_parts)
        print(f"[SOUND] Transcribed {len(transcript)} chars")
        return transcript

    except Exception as e:
        print(f"[SOUND] Whisper error: {e}")
        return ""


def get_transcript(url: str = None, audio_path: str = None, video_path: str = None, work_dir: str = None) -> str:
    """
    Get transcript - tries captions first, falls back to Whisper

    Provide either:
    - url: YouTube URL (tries captions first)
    - audio_path: Direct path to audio file
    - video_path: Path to video file (will extract audio)
    """

    # Try captions first if URL provided
    if url:
        print("[SOUND] Checking for captions...")
        transcript = get_captions(url, work_dir)
        if transcript:
            print(f"[SOUND] Got captions: {len(transcript)} chars")
            return transcript
        print("[SOUND] No captions, need Whisper...")

    # If we have video but no audio, extract it
    if video_path and not audio_path:
        if work_dir is None:
            work_dir = tempfile.mkdtemp(prefix="transcript_")
        audio_path = os.path.join(work_dir, "audio.wav")

        print("[SOUND] Extracting audio from video...")
        cmd = [
            "ffmpeg", "-i", video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
            audio_path, "-y"
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)

        if not os.path.exists(audio_path):
            print("[SOUND] Audio extraction failed")
            return ""

    # Transcribe with Whisper
    if audio_path and os.path.exists(audio_path):
        return transcribe_audio(audio_path)

    return ""


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        # If it's a URL
        if sys.argv[1].startswith('http'):
            print(get_transcript(url=sys.argv[1]))
        else:
            # Assume it's an audio file
            print(get_transcript(audio_path=sys.argv[1]))
