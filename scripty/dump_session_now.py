#!/usr/bin/env python3
"""
Manual Session Dump - Save current session on demand
Use when you want to end the session before hitting 90%
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

DUMP_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/memory-dumps")
DUMP_DIR.mkdir(parents=True, exist_ok=True)


def get_session_file():
    """Find current Claude session file"""
    claude_dir = Path.home() / ".claude"
    session_files = list(claude_dir.glob("**/session*.json"))

    if session_files:
        return max(session_files, key=lambda p: p.stat().st_mtime)
    return None


def dump_session():
    """Save current session immediately"""
    session_file = get_session_file()

    if not session_file or not session_file.exists():
        print("❌ No active session file found")
        return False

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dump_file = DUMP_DIR / f"manual_dump_{timestamp}.jsonl"

    print(f"📝 Dumping current session...")
    print(f"   Source: {session_file}")
    print(f"   Target: {dump_file}")

    try:
        # Copy session file
        shutil.copy2(session_file, dump_file)

        # Get session size
        size_mb = dump_file.stat().st_size / (1024 * 1024)

        print(f"✓ Session saved successfully")
        print(f"   Size: {size_mb:.2f} MB")
        print(f"   Location: {dump_file}")

        # Check if we should ingest it
        ingest = input("\n🔄 Ingest into memory system now? [y/N]: ").lower()

        if ingest == 'y':
            print("\n📥 Triggering ingestion...")
            import subprocess
            messiah_python = Path.home() / "anaconda3/envs/messiah/bin/python"
            ingest_script = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/writers/ingest_agent.py")

            result = subprocess.run(
                [str(messiah_python), str(ingest_script), str(dump_file)],
                capture_output=True,
                text=True
            )

            if result.returncode == 0:
                print("✓ Ingestion complete")
            else:
                print(f"✗ Ingestion failed: {result.stderr}")

        return True

    except Exception as e:
        print(f"❌ Dump failed: {e}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("MANUAL SESSION DUMP")
    print("=" * 60)
    print("This will save the current session to:")
    print(f"  {DUMP_DIR}")
    print()

    proceed = input("Continue? [Y/n]: ").lower()

    if proceed in ['', 'y', 'yes']:
        dump_session()
    else:
        print("Cancelled.")
