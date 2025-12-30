#!/usr/bin/env python3
"""
Ingestion Agent - Button-Ready Version
API-friendly JSON output for button integration
"""

import sys
import os
import json
import psycopg2
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from pathlib import Path

# PDF processing
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

# Config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Thread-safe printing
print_lock = threading.Lock()
messages = []


def log_message(msg, json_mode=False):
    """Log message (collect for JSON or print immediately)"""
    if json_mode:
        messages.append(msg)
    else:
        with print_lock:
            print(msg)


def extract_pdf_pages(filepath: str) -> list:
    """Extract text from PDF"""
    if not PDF_SUPPORT:
        raise Exception("PDF support not available - install pdfplumber")

    pages = []
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({
                    "page": i + 1,
                    "content": text,
                    "char_count": len(text)
                })
    return pages


def chunk_text(text: str, chunk_size: int = 1000, overlap: int = 100) -> list:
    """Split text into overlapping chunks"""
    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end]
        if chunk.strip():
            chunks.append(chunk)
        start = end - overlap
    return chunks


def store_chunk(chunk: str, metadata: dict) -> bool:
    """Store chunk in pgai"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        now = datetime.now()

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                "thewolfwalksalone",
                chunk,
                json.dumps(metadata),
                metadata.get("type", "document"),
                metadata.get("namespace", "ingested"),
                now,
                now
            ))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        return False


def ingest_pdf(filepath: str, json_mode=False):
    """Ingest PDF file"""
    filename = os.path.basename(filepath)

    log_message(f"Ingesting PDF: {filename}", json_mode)

    try:
        pages = extract_pdf_pages(filepath)
        log_message(f"Extracted {len(pages)} pages", json_mode)

        total_stored = 0
        for page in pages:
            chunks = chunk_text(page["content"], chunk_size=800, overlap=100)

            for i, chunk in enumerate(chunks):
                metadata = {
                    "source_file": filename,
                    "page": page["page"],
                    "chunk": i + 1,
                    "type": "document",
                    "namespace": "ingested",
                    "ingested_at": datetime.now().isoformat()
                }
                if store_chunk(chunk, metadata):
                    total_stored += 1

        return {
            "success": True,
            "message": f"PDF ingested successfully: {filename}",
            "pages_processed": len(pages),
            "chunks_stored": total_stored,
            "file": filename,
            "file_type": "pdf"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"PDF ingestion failed: {e}",
            "error": str(e),
            "file": filename
        }


def ingest_text(filepath: str, json_mode=False):
    """Ingest text file"""
    filename = os.path.basename(filepath)

    log_message(f"Ingesting text file: {filename}", json_mode)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        chunks = chunk_text(content, chunk_size=800, overlap=100)
        log_message(f"Split into {len(chunks)} chunks", json_mode)

        total_stored = 0
        for i, chunk in enumerate(chunks):
            metadata = {
                "source_file": filename,
                "chunk": i + 1,
                "total_chunks": len(chunks),
                "type": "document",
                "namespace": "ingested",
                "ingested_at": datetime.now().isoformat()
            }
            if store_chunk(chunk, metadata):
                total_stored += 1

        return {
            "success": True,
            "message": f"Text file ingested successfully: {filename}",
            "chunks_stored": total_stored,
            "file": filename,
            "file_type": "text"
        }

    except Exception as e:
        return {
            "success": False,
            "message": f"Text ingestion failed: {e}",
            "error": str(e),
            "file": filename
        }


def ingest_jsonl(filepath: str, json_mode=False):
    """Ingest JSONL file"""
    filename = os.path.basename(filepath)

    log_message(f"Ingesting JSONL: {filename}", json_mode)

    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        lines = content.strip().split('\n')

        # Try parsing as JSONL
        json_objects = []
        for line in lines:
            if line.strip():
                try:
                    obj = json.loads(line)
                    json_objects.append(obj)
                except json.JSONDecodeError:
                    break

        if json_objects:
            # Valid JSONL
            total_stored = 0
            for i, obj in enumerate(json_objects):
                chunk_content = obj.get('content') or obj.get('text') or json.dumps(obj)
                metadata = {
                    "source_file": filename,
                    "record": i + 1,
                    "type": "jsonl_record",
                    "namespace": "session_recovery",
                    "ingested_at": datetime.now().isoformat()
                }
                if store_chunk(str(chunk_content), metadata):
                    total_stored += 1

            return {
                "success": True,
                "message": f"JSONL ingested successfully: {filename}",
                "records_stored": total_stored,
                "file": filename,
                "file_type": "jsonl"
            }
        else:
            # Fallback to text
            return ingest_text(filepath, json_mode)

    except Exception as e:
        return {
            "success": False,
            "message": f"JSONL ingestion failed: {e}",
            "error": str(e),
            "file": filename
        }


def ingest_file(filepath: str, json_mode=False):
    """Main ingestion dispatcher"""
    if not os.path.exists(filepath):
        return {
            "success": False,
            "message": f"File not found: {filepath}",
            "error": "file_not_found"
        }

    ext = Path(filepath).suffix.lower()

    if ext == '.pdf':
        if not PDF_SUPPORT:
            return {
                "success": False,
                "message": "PDF support not available",
                "error": "missing_dependency"
            }
        return ingest_pdf(filepath, json_mode)
    elif ext in ['.jsonl', '.json']:
        return ingest_jsonl(filepath, json_mode)
    elif ext in ['.txt', '.md', '.text', '.markdown']:
        return ingest_text(filepath, json_mode)
    else:
        return {
            "success": False,
            "message": f"Unsupported file type: {ext}",
            "error": "unsupported_file_type"
        }


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Ingestion Agent - Button Ready')
    parser.add_argument('filepath', help='File to ingest')
    parser.add_argument('--json', action='store_true', help='Output JSON for API integration')

    args = parser.parse_args()

    result = ingest_file(args.filepath, json_mode=args.json)

    if args.json:
        result["logs"] = messages
        print(json.dumps(result, indent=2))

    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
