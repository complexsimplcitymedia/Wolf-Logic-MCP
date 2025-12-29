#!/usr/bin/env python3
"""
Swarm Intake Processor - Keyword Categorization & Sentiment Analysis
Watches camera/dailys/ for new transcripts and processes them.

Pipeline: dailys → categorize → sentiment → summarize → pgai-queue
"""
import os
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# Directories - watch both camera/dailys (local) and data/client-dumps (remote nodes)
DAILYS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/camera/dailys")
CLIENT_DUMPS_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/client-dumps")
HANDOFF_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/data/pgai-queue")
CLIENT_DUMPS_DIR.mkdir(parents=True, exist_ok=True)
HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

# Ollama endpoint
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"

# Track processed files
PROCESSED_LOG = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/Wolf-Logic-MCP/logs/swarm-intake-processed.txt")
PROCESSED_LOG.parent.mkdir(parents=True, exist_ok=True)

def load_processed():
    """Load set of processed file positions"""
    if PROCESSED_LOG.exists():
        with open(PROCESSED_LOG, 'r') as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def mark_processed(file_key):
    """Mark a file position as processed"""
    with open(PROCESSED_LOG, 'a') as f:
        f.write(f"{file_key}\n")

def ollama_generate(model, prompt):
    """Call Ollama API for generation"""
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": model,
            "prompt": prompt,
            "stream": False
        }, timeout=30)

        if response.status_code == 200:
            return response.json().get('response', '').strip()
    except Exception as e:
        print(f"[{datetime.now()}] Ollama error ({model}): {e}")
    return None

def categorize_keywords(text):
    """Extract keywords from text"""
    prompt = f"Extract 5-10 key topics/keywords from this conversation. Return only comma-separated keywords:\n\n{text[:2000]}"
    result = ollama_generate("llama3.2:1b", prompt)
    if result:
        keywords = [k.strip() for k in result.split(',')]
        return keywords[:10]
    return []

def analyze_sentiment(text):
    """Analyze sentiment using mistral"""
    prompt = f"Analyze the sentiment of this conversation. Rate from 1-5 (1=very negative, 5=very positive) and explain briefly:\n\n{text[:2000]}"
    result = ollama_generate("mistral:latest", prompt)

    # Extract score
    score = 3  # default neutral
    if result:
        for word in result.split():
            if word.isdigit() and 1 <= int(word) <= 5:
                score = int(word)
                break

    return {
        "score": score,
        "analysis": result if result else "neutral"
    }

def summarize_transcript(text):
    """Summarize transcript using llama3.2:1b"""
    prompt = f"Summarize this conversation in 2-3 sentences:\n\n{text[:3000]}"
    result = ollama_generate("llama3.2:1b", prompt)
    return result if result else "Conversation transcript"

def process_transcript(entry):
    """Process a single transcript entry"""
    transcript_text = entry.get('transcript', '')

    if len(transcript_text) < 20:
        return None

    # Extract keywords
    keywords = categorize_keywords(transcript_text)

    # Analyze sentiment
    sentiment = analyze_sentiment(transcript_text)

    # Summarize
    summary = summarize_transcript(transcript_text)

    return {
        "text": summary,
        "content": transcript_text,
        "namespace": "scripty",
        "username": "wolf",
        "session": entry.get('session', 'unknown'),
        "timestamp": entry.get('timestamp'),
        "keywords": keywords,
        "sentiment": sentiment,
        "source": "swarm-intake"
    }

def watch_directory(directory, prefix):
    """Watch a directory for JSONL files and process new entries"""
    processed = load_processed()

    # Get today's file
    today = datetime.now().strftime("%Y%m%d")
    target_file = directory / f"{prefix}_{today}.jsonl"

    if not target_file.exists():
        return processed

    # Read and process new entries
    with open(target_file, 'r') as f:
        lines = f.readlines()

    for i, line in enumerate(lines):
        file_key = f"{target_file.name}:{i}"

        if file_key in processed:
            continue

        try:
            entry = json.loads(line.strip())

            # Process transcript
            processed_data = process_transcript(entry)

            if processed_data:
                # Write to handoff queue
                handoff_file = HANDOFF_DIR / f"intake_{int(time.time()*1000)}_{i}.json"
                with open(handoff_file, 'w') as hf:
                    json.dump(processed_data, hf, indent=2)

                print(f"[{datetime.now()}] Processed: {file_key} → {handoff_file.name}")

            # Mark as processed
            mark_processed(file_key)
            processed.add(file_key)

        except json.JSONDecodeError:
            continue
        except Exception as e:
            print(f"[{datetime.now()}] Error processing {file_key}: {e}")

    return processed

def watch_dailys():
    """Watch both dailys and client-dumps directories"""
    print(f"[{datetime.now()}] Starting swarm-intake processor...")
    print(f"[{datetime.now()}] Watching: camera/dailys/ and data/client-dumps/")

    while True:
        try:
            # Watch camera/dailys for local scripty output
            watch_directory(DAILYS_DIR, "scripty")

            # Watch data/client-dumps for remote node drops
            watch_directory(CLIENT_DUMPS_DIR, "transcript")

            time.sleep(30)

        except KeyboardInterrupt:
            print(f"\n[{datetime.now()}] Stopping swarm-intake")
            break
        except Exception as e:
            print(f"[{datetime.now()}] Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    watch_dailys()
