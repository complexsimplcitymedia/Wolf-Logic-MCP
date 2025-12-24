#!/usr/bin/env python3
"""
Swarm Intake Processor
Watches client_dump directory for incoming text streams
Performs keyword categorization and sentiment analysis
Hands off to pgai for embedding and database insertion
"""

import os
import json
import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# CONFIGURATION
# ============================================================================

INTAKE_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/client_dump")
PROCESSED_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/processed_intake")
PGAI_HANDOFF_DIR = Path("/mnt/Wolf-code/Wolf-Ai-Enterptises/data/pgai_queue")

# Ollama configuration
OLLAMA_BASE = "http://localhost:11434"
SENTIMENT_MODEL = "mistral:latest"

# Ensure directories exist
INTAKE_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
PGAI_HANDOFF_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================================
# KEYWORD CATEGORIZATION
# ============================================================================

KEYWORD_CATEGORIES = {
    "development": [
        "code", "programming", "debug", "error", "function", "class", "variable",
        "api", "endpoint", "database", "query", "sql", "python", "java", "javascript",
        "git", "commit", "merge", "branch", "deploy", "build", "test"
    ],
    "infrastructure": [
        "server", "docker", "kubernetes", "container", "cloud", "aws", "azure",
        "network", "firewall", "security", "ssl", "certificate", "dns", "load balancer",
        "nginx", "apache", "postgres", "redis", "mongodb"
    ],
    "project_management": [
        "task", "deadline", "milestone", "sprint", "backlog", "priority", "status",
        "meeting", "standup", "retrospective", "planning", "estimate", "blocker"
    ],
    "documentation": [
        "readme", "docs", "documentation", "guide", "tutorial", "explanation",
        "architecture", "design", "specification", "requirement", "manual"
    ],
    "personal": [
        "note", "reminder", "todo", "idea", "thought", "observation", "reflection",
        "journal", "log", "diary"
    ],
    "ai_model": [
        "llm", "model", "embedding", "vector", "semantic", "prompt", "inference",
        "training", "fine-tune", "transformer", "ollama", "mistral", "llama"
    ],
    "system": [
        "memory", "cpu", "disk", "process", "thread", "performance", "monitor",
        "log", "trace", "metric", "alert", "health"
    ]
}


def categorize_text(text: str) -> List[str]:
    """
    Categorize text based on keyword matching
    Returns list of matching categories
    """
    text_lower = text.lower()
    categories = []
    
    for category, keywords in KEYWORD_CATEGORIES.items():
        # Check if any keyword appears in text
        if any(keyword in text_lower for keyword in keywords):
            categories.append(category)
    
    # Default to 'general' if no categories matched
    if not categories:
        categories.append("general")
    
    return categories


# ============================================================================
# SENTIMENT ANALYSIS
# ============================================================================

def analyze_sentiment(text: str) -> Dict[str, any]:
    """
    Analyze sentiment using mistral:latest
    Returns sentiment score (1-5) and explanation
    """
    prompt = f"""Analyze the sentiment of the following text and rate it on a scale of 1-5:
1 = Very Negative (angry, frustrated, critical)
2 = Negative (disappointed, concerned)
3 = Neutral (factual, objective)
4 = Positive (satisfied, constructive)
5 = Very Positive (enthusiastic, excited)

Text: {text}

Respond ONLY with a JSON object in this exact format:
{{"score": <number 1-5>, "reasoning": "<brief explanation>"}}"""

    try:
        response = requests.post(
            f"{OLLAMA_BASE}/api/generate",
            json={
                "model": SENTIMENT_MODEL,
                "prompt": prompt,
                "stream": False,
                "temperature": 0.3
            },
            timeout=30
        )
        response.raise_for_status()
        
        result = response.json()
        response_text = result.get("response", "").strip()
        
        # Parse JSON from response
        # Handle potential markdown formatting
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        sentiment_data = json.loads(response_text)
        
        # Validate score
        score = sentiment_data.get("score", 3)
        if not isinstance(score, (int, float)) or score < 1 or score > 5:
            logger.warning(f"Invalid sentiment score {score}, defaulting to 3")
            score = 3
        
        return {
            "score": int(score),
            "reasoning": sentiment_data.get("reasoning", "No explanation provided"),
            "model": SENTIMENT_MODEL
        }
        
    except Exception as e:
        logger.error(f"Sentiment analysis failed: {e}")
        return {
            "score": 3,
            "reasoning": f"Analysis failed: {str(e)}",
            "model": SENTIMENT_MODEL,
            "error": str(e)
        }


# ============================================================================
# FILE PROCESSING
# ============================================================================

def process_intake_file(file_path: Path) -> bool:
    """
    Process a single intake file:
    1. Load JSON
    2. Categorize keywords
    3. Analyze sentiment
    4. Write to pgai handoff queue
    5. Move to processed directory
    """
    try:
        logger.info(f"Processing: {file_path.name}")
        
        # Read intake file
        with open(file_path, 'r') as f:
            intake_data = json.load(f)
        
        text = intake_data.get("text", "")
        if not text:
            logger.warning(f"Empty text in {file_path.name}, skipping")
            return False
        
        # Step 1: Keyword categorization
        logger.info("Running keyword categorization...")
        categories = categorize_text(text)
        
        # Step 2: Sentiment analysis
        logger.info("Running sentiment analysis...")
        sentiment = analyze_sentiment(text)
        
        # Build processed data structure
        processed_data = {
            "source_file": file_path.name,
            "username": intake_data.get("username", "unknown"),
            "user_email": intake_data.get("user_email", ""),
            "text": text,
            "categories": categories,
            "sentiment": sentiment,
            "metadata": intake_data.get("metadata", {}),
            "intake_timestamp": intake_data.get("timestamp"),
            "processed_timestamp": datetime.now().isoformat(),
            "file_id": intake_data.get("file_id"),
            "namespace": "client_intake"  # pgai will use this
        }
        
        # Write to pgai handoff queue
        handoff_file = PGAI_HANDOFF_DIR / f"pgai_{file_path.name}"
        with open(handoff_file, 'w') as f:
            json.dump(processed_data, f, indent=2)
        
        logger.info(f"Handoff created: {handoff_file.name}")
        
        # Move original to processed directory
        processed_path = PROCESSED_DIR / file_path.name
        file_path.rename(processed_path)
        
        logger.info(f"✓ Processed: {file_path.name} -> Categories: {categories}, Sentiment: {sentiment['score']}/5")
        return True
        
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path.name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to process {file_path.name}: {e}")
        return False


def process_existing_files():
    """Process any existing files in intake directory"""
    files = sorted(INTAKE_DIR.glob("*.json"))
    if files:
        logger.info(f"Found {len(files)} existing files to process")
        for file_path in files:
            process_intake_file(file_path)
    else:
        logger.info("No existing files in intake directory")


# ============================================================================
# FILE WATCHER
# ============================================================================

class IntakeFileHandler(FileSystemEventHandler):
    """Watch for new files in intake directory"""
    
    def on_created(self, event):
        """Handle new file creation"""
        if event.is_directory:
            return
        
        file_path = Path(event.src_path)
        
        # Only process JSON files
        if file_path.suffix != ".json":
            return
        
        # Wait briefly for file to be fully written
        time.sleep(0.5)
        
        # Process the file
        process_intake_file(file_path)


def start_watching():
    """Start watching intake directory for new files"""
    logger.info(f"Starting swarm intake processor...")
    logger.info(f"Watching: {INTAKE_DIR}")
    logger.info(f"Handoff to: {PGAI_HANDOFF_DIR}")
    logger.info(f"Sentiment model: {SENTIMENT_MODEL}")
    
    # Process existing files first
    process_existing_files()
    
    # Start file watcher
    event_handler = IntakeFileHandler()
    observer = Observer()
    observer.schedule(event_handler, str(INTAKE_DIR), recursive=False)
    observer.start()
    
    logger.info("✓ Swarm processor active - waiting for files...")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        observer.stop()
    
    observer.join()


# ============================================================================
# STATS
# ============================================================================

def get_stats() -> Dict[str, any]:
    """Get processing statistics"""
    intake_files = list(INTAKE_DIR.glob("*.json"))
    processed_files = list(PROCESSED_DIR.glob("*.json"))
    handoff_files = list(PGAI_HANDOFF_DIR.glob("pgai_*.json"))
    
    return {
        "intake_queue": len(intake_files),
        "processed_count": len(processed_files),
        "pgai_queue": len(handoff_files),
        "timestamp": datetime.now().isoformat()
    }


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        # Print stats and exit
        stats = get_stats()
        print(json.dumps(stats, indent=2))
    else:
        # Start watching
        start_watching()
