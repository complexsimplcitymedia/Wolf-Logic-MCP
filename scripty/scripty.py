#!/usr/bin/env python3
"""
Scripty - Session Stenographer & Summarizer
Captures Claude Code sessions, writes to dailys, and summarizes context using llama3.2:1b.
"""
import os
import json
import time
import ollama
from datetime import datetime
from pathlib import Path

# Configuration - relative to project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
DAILYS_DIR = PROJECT_ROOT / "data" / "client-dumps(scripty global)"
MODEL = "llama3.2:1b"
POLL_INTERVAL = 30  # seconds

DAILYS_DIR.mkdir(parents=True, exist_ok=True)

def get_session_file():
    """Find the most recent Claude session file"""
    claude_dir = Path.home() / ".claude"
    projects_dir = claude_dir / "projects"
    if not projects_dir.exists():
        return None

    session_files = list(projects_dir.glob("**/*.jsonl"))
    # Filter out agent files if any
    session_files = [f for f in session_files if not f.name.startswith('agent-')]

    if session_files:
        return max(session_files, key=lambda p: p.stat().st_mtime)
    return None

def get_output_file():
    """Get today's output file"""
    today = datetime.now().strftime("%Y%m%d")
    return DAILYS_DIR / f"scripty_{today}.jsonl"

def extract_text_content(content_blocks):
    """Extract text from content blocks"""
    if isinstance(content_blocks, str):
        return content_blocks

    parts = []
    if isinstance(content_blocks, list):
        for block in content_blocks:
            if isinstance(block, dict):
                if block.get('type') == 'text':
                    parts.append(block.get('text', ''))
                elif block.get('type') == 'tool_use':
                    tool_name = block.get('name', 'unknown')
                    parts.append(f"[TOOL: {tool_name}]")
    
    return '\n'.join(parts) if parts else ''

def read_session_entries(session_file):
    """Read all entries from session file"""
    entries = []
    try:
        with open(session_file, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except Exception:
        pass
    return entries

def summarize_chunk(text_chunk):
    """Summarize a chunk of text using llama3.2:1b"""
    if not text_chunk.strip():
        return None
        
    try:
        prompt = f"Summarize this conversation update in 1 sentence:\n\n{text_chunk}"
        response = ollama.chat(model=MODEL, messages=[
            {'role': 'user', 'content': prompt}
        ])
        return response['message']['content'].strip()
    except Exception as e:
        print(f"[{datetime.now()}] Summarization error: {e}")
        return None

def watch_session():
    """Watch Claude session, write transcripts, and summarize"""
    print(f"[{datetime.now()}] Starting scripty with {MODEL}...")

    last_position = 0
    current_session_id = None

    while True:
        try:
            session_file = get_session_file()
            if not session_file:
                time.sleep(5)
                continue

            # Detect session change
            session_id = session_file.stem
            if session_id != current_session_id:
                print(f"[{datetime.now()}] New session: {session_id}")
                current_session_id = session_id
                last_position = 0

            entries = read_session_entries(session_file)

            if len(entries) > last_position:
                output_file = get_output_file()
                new_text_buffer = ""
                
                # Process new entries
                for i in range(last_position, len(entries)):
                    entry = entries[i]
                    entry_type = entry.get('type')

                    transcript_data = {
                        'timestamp': datetime.now().isoformat(),
                        'session': session_id,
                        'transcript': ''
                    }

                    if entry_type == 'user':
                        msg = entry.get('message', {})
                        content = msg.get('content', '')
                        text = f"USER: {content}"
                        transcript_data['transcript'] = text
                        new_text_buffer += text + "\n"

                    elif entry_type == 'assistant':
                        msg = entry.get('message', {})
                        content_blocks = msg.get('content', [])
                        assistant_text = extract_text_content(content_blocks)
                        text = f"ASSISTANT: {assistant_text}"
                        transcript_data['transcript'] = text
                        new_text_buffer += text + "\n"

                    elif entry_type == 'tool_result':
                        tool_result = str(entry.get('tool_result', ''))[:500]
                        text = f"TOOL_RESULT: {tool_result}"
                        transcript_data['transcript'] = text
                        # Don't add tool results to summary buffer to save tokens/noise

                    # Write to dailys
                    if transcript_data['transcript']:
                        with open(output_file, 'a') as f:
                            f.write(json.dumps(transcript_data) + '\n')

                # Summarize the new interaction
                if new_text_buffer:
                    summary = summarize_chunk(new_text_buffer)
                    if summary:
                        print(f"[{datetime.now()}] Summary: {summary}")
                        # Append summary to daily file as a system note
                        summary_data = {
                            'timestamp': datetime.now().isoformat(),
                            'session': session_id,
                            'transcript': f"SYSTEM_SUMMARY: {summary}"
                        }
                        with open(output_file, 'a') as f:
                            f.write(json.dumps(summary_data) + '\n')

                last_position = len(entries)
                print(f"[{datetime.now()}] Processed {len(entries)} entries")

            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Stopping scripty")
            break
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    watch_session()
