#!/usr/bin/env python3
"""
YouTube Analyst - The Editor
Coordinates the army. Doesn't do their jobs - calls the specialists.

Agents in the army:
- visual_agent: LLaVA frame analysis (Lighting Dept)
- transcript_agent: Captions/Whisper (Sound Dept)
- audio_agent: Mood/energy analysis (Post-Sound Dept)

Usage: python youtube_analyst.py <youtube_url> [--interval N] [--store]

Frame logic: Every Nth frame (default 15)
- At 24fps: every 15th = ~1.6 frames/sec
- At 30fps: every 15th = 2 frames/sec
7900 XT can push harder. Designated seconds for precision.

LLaVA 13b solo. Push the GPU. No conservative bullshit.
"""

import sys
import os
import json
import tempfile
import shutil
import subprocess
from datetime import datetime
import argparse

# Add agents directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# The army
from visual_agent import analyze_frames_batch
from transcript_agent import get_transcript
from audio_agent import analyze_audio

# Frame extraction (Camera Dept - stays here, it's just file ops)
import cv2
from PIL import Image

# Database
import psycopg2

# Config
PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}


class YouTubeAnalyst:
    """The Editor - coordinates, doesn't do the work"""

    def __init__(self, url: str, frame_interval: int = None, target_fps: float = 1.0):
        """
        frame_interval: Manual override for frame extraction interval.
        target_fps: Target analysis frames per second (default 1.0 = 1 frame/sec).
        If frame_interval is None, it is calculated from video FPS / target_fps.
        """
        self.url = url
        self.frame_interval = frame_interval
        self.target_fps = target_fps
        # DIT (Digital Image Transfer) - where downloaded media lives
        dit_base = "/mnt/Wolf-code/Wolf-Ai-Enterptises/camera/dit"
        self.work_dir = tempfile.mkdtemp(prefix="yt_", dir=dit_base)
        self.video_path = None
        self.audio_path = None
        self.metadata = {}

    def cleanup(self):
        if os.path.exists(self.work_dir):
            shutil.rmtree(self.work_dir)

    def download(self) -> bool:
        """Download video - Grip work"""
        print("\n[GRIP] Downloading video...")

        try:
            # Check if URL is a local file path
            if self.url.startswith("file://"):
                local_path = self.url.replace("file://", "")
                if os.path.exists(local_path):
                    self.video_path = local_path
                    self.metadata = {
                        "title": os.path.basename(os.path.dirname(local_path)),
                        "duration": 0
                    }
                    print(f"[GRIP] Using existing file: {os.path.getsize(local_path) / 1024 / 1024:.1f}MB")
                    return True
                else:
                    print(f"[GRIP] Local file not found: {local_path}")
                    return False

            # Get metadata
            meta_cmd = ["yt-dlp", "--dump-json", "--no-download", self.url]
            result = subprocess.run(meta_cmd, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                self.metadata = json.loads(result.stdout)
                print(f"[GRIP] Title: {self.metadata.get('title', 'Unknown')}")
                print(f"[GRIP] Duration: {self.metadata.get('duration', 0)}s")

            # Download
            video_file = os.path.join(self.work_dir, "video.mp4")
            download_cmd = [
                "yt-dlp",
                "-f", "bestvideo[height<=720]+bestaudio/best[height<=720]/best",
                "--merge-output-format", "mp4",
                "-o", video_file,
                "--no-playlist",
                self.url
            ]

            result = subprocess.run(download_cmd, capture_output=True, text=True, timeout=300)

            if os.path.exists(video_file):
                self.video_path = video_file
                print(f"[GRIP] Downloaded: {os.path.getsize(video_file) / 1024 / 1024:.1f}MB")
                return True

            print(f"[GRIP] Download failed")
            return False

        except Exception as e:
            print(f"[GRIP] Error: {e}")
            return False

    def extract_frames(self) -> list:
        """Extract frames based on target FPS - Camera work"""
        
        frames = []
        try:
            cap = cv2.VideoCapture(self.video_path)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)

            # Calculate interval if not manually set
            if self.frame_interval is None:
                if fps > 0:
                    self.frame_interval = max(1, int(fps / self.target_fps))
                else:
                    self.frame_interval = 30 # Fallback
            
            print(f"\n[CAMERA] Video: {total_frames} total frames @ {fps:.1f}fps")
            print(f"[CAMERA] Target: {self.target_fps} fps -> Extracting every {self.frame_interval}th frame")
            print(f"[CAMERA] Extracting ~{total_frames // self.frame_interval} frames total")

            # Extract frames
            frame_num = 0
            extracted = 0

            while True:
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
                ret, frame = cap.read()

                if not ret:
                    break

                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w = frame_rgb.shape[:2]
                scale = 512 / max(h, w)
                new_size = (int(w * scale), int(h * scale))
                frame_resized = cv2.resize(frame_rgb, new_size)

                img = Image.fromarray(frame_resized)
                frame_path = os.path.join(self.work_dir, f"frame_{extracted:04d}.jpg")
                img.save(frame_path, "JPEG", quality=85)

                timestamp = frame_num / fps if fps > 0 else 0
                frames.append({
                    "path": frame_path,
                    "position": extracted + 1,
                    "frame_num": frame_num,
                    "timestamp": timestamp,
                    "timestamp_str": f"{int(timestamp // 60)}:{int(timestamp % 60):02d}"
                })

                extracted += 1
                frame_num += self.frame_interval

            cap.release()
            print(f"[CAMERA] Extracted {len(frames)} frames (every {self.frame_interval}th)")

        except Exception as e:
            print(f"[CAMERA] Error: {e}")

        return frames

    def extract_audio(self) -> str:
        """Extract audio for agents - just file ops"""
        audio_path = os.path.join(self.work_dir, "audio.wav")
        cmd = [
            "ffmpeg", "-i", self.video_path,
            "-vn", "-acodec", "pcm_s16le", "-ar", "22050", "-ac", "1",
            audio_path, "-y"
        ]
        subprocess.run(cmd, capture_output=True, timeout=120)
        if os.path.exists(audio_path):
            self.audio_path = audio_path
            return audio_path
        return None

    def store_to_pgai(self, report: dict) -> bool:
        """Store in pgai - Archive"""
        print("\n[ARCHIVE] Storing to pgai...")

        try:
            conn = psycopg2.connect(**PG_CONFIG)
            now = datetime.now()

            content = f"""YouTube Analysis: {report['title']}

TRANSCRIPT:
{report.get('transcript', '')[:5000]}

VISUAL ANALYSIS:
{json.dumps(report.get('frame_analyses', []), indent=2)[:3000]}

AUDIO: {json.dumps(report.get('audio_analysis', {}))}
"""

            metadata = {
                "source": "youtube_analyst",
                "url": report['url'],
                "title": report['title'],
                "channel": report['channel'],
                "duration": report['duration'],
                "analyzed_at": report['analyzed_at'],
                "namespace": "youtube_analysis"
            }

            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    "youtube_analyst",
                    content,
                    json.dumps(metadata),
                    "media_analysis",
                    "youtube",
                    now, now
                ))

            conn.commit()
            conn.close()
            print("[ARCHIVE] Stored successfully")
            return True

        except Exception as e:
            print(f"[ARCHIVE] Error: {e}")
            return False

    def run(self, store: bool = False) -> dict:
        """Coordinate the army - Editor's job"""
        print("=" * 60)
        print("YOUTUBE ANALYST - Coordinating the Army")
        print("=" * 60)
        print(f"URL: {self.url}")
        print("=" * 60)

        try:
            # GRIP: Download
            if not self.download():
                return {"error": "Download failed"}

            # CAMERA: Extract frames (just file ops)
            frames = self.extract_frames()

            # Extract audio for agents
            self.extract_audio()

            # DEPLOY THE ARMY
            from concurrent.futures import ThreadPoolExecutor

            results = {}

            with ThreadPoolExecutor(max_workers=3) as executor:
                # Sound Dept: Get transcript
                transcript_future = executor.submit(
                    get_transcript,
                    url=self.url,
                    video_path=self.video_path,
                    work_dir=self.work_dir
                )

                # Post-Sound Dept: Audio analysis
                audio_future = None
                if self.audio_path:
                    audio_future = executor.submit(analyze_audio, self.audio_path)

                # Lighting Dept: Visual analysis (LLaVA 13b solo)
                # Workers default to 6 in visual_agent - push the 7900 XT
                visual_future = executor.submit(analyze_frames_batch, frames)

                # Gather results
                results['transcript'] = transcript_future.result()
                results['frame_analyses'] = visual_future.result()
                if audio_future:
                    results['audio_analysis'] = audio_future.result()
                else:
                    results['audio_analysis'] = {}

            # EDITOR: Compile the report
            report = {
                "url": self.url,
                "title": self.metadata.get('title', 'Unknown'),
                "channel": self.metadata.get('channel', 'Unknown'),
                "duration": self.metadata.get('duration', 0),
                "analyzed_at": datetime.now().isoformat(),
                "transcript": results['transcript'],
                "frame_analyses": results['frame_analyses'],
                "audio_analysis": results['audio_analysis']
            }

            # ARCHIVE: Store if requested
            if store:
                self.store_to_pgai(report)

            # Print summary
            print("\n" + "=" * 60)
            print("ANALYSIS COMPLETE")
            print("=" * 60)
            print(f"Title: {report['title']}")
            print(f"Transcript: {len(report['transcript'])} chars")
            print(f"Frames analyzed: {len(report['frame_analyses'])}")
            print(f"Audio: {report['audio_analysis'].get('energy_profile', 'N/A')} energy")
            print("=" * 60)

            return report

        finally:
            self.cleanup()


def main():
    parser = argparse.ArgumentParser(description='YouTube Analyst - Coordinate the Army')
    parser.add_argument('url', help='YouTube URL')
    parser.add_argument('--interval', type=int, default=None, help='Extract every Nth frame (overrides --target-fps)')
    parser.add_argument('--target-fps', type=float, required=True, help='Target analysis frames per second (e.g., 1.0 for 1 frame/sec)')
    parser.add_argument('--store', action='store_true', help='Store in pgai')
    parser.add_argument('--output', type=str, help='Save report to JSON')

    args = parser.parse_args()

    analyst = YouTubeAnalyst(args.url, frame_interval=args.interval, target_fps=args.target_fps)
    report = analyst.run(store=args.store)

    if args.output and 'error' not in report:
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        print(f"\nReport saved: {args.output}")

    return 0 if 'error' not in report else 1


if __name__ == "__main__":
    sys.exit(main())
