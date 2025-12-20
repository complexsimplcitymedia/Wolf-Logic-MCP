#!/usr/bin/env python3
"""
Ingestion Agent - The Librarian's Intake Department
Takes a file path, dismantles it, fans out to embedding fleet, stores in pgai.
Claude doesn't read the file. This agent does.

Usage: python ingest_agent.py /path/to/file.pdf
"""

import sys
import os
import json
import psycopg2
import subprocess
import tempfile
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# PDF processing
import pdfplumber

# Ollama for embeddings
import ollama

# Config
PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Embedding fleet - exclude nomic (reserved for librarian)
EMBED_FLEET = [
    "bge-large:latest",
    "mxbai-embed-large:latest",
    "snowflake-arctic-embed:137m",
    "jina/jina-embeddings-v2-base-en:latest",
]

# Thread-safe printing
print_lock = threading.Lock()
def safe_print(msg):
    with print_lock:
        print(msg)


def ocr_pdf(filepath: str) -> str:
    """Run OCR on a scanned PDF and return path to OCR'd version"""
    safe_print("  Detected scanned PDF - running OCR (this may take a few minutes)...")

    # Create temp file for OCR output
    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp:
        ocr_output = tmp.name

    try:
        # Run ocrmypdf - skip pages that already have text, force OCR on images
        result = subprocess.run([
            'ocrmypdf',
            '--skip-text',           # Skip pages that already have text
            '--force-ocr',           # Force OCR on image pages
            '-l', 'eng',             # English language
            '--jobs', '4',           # Parallel processing
            filepath,
            ocr_output
        ], capture_output=True, text=True, timeout=600)  # 10 min timeout

        if result.returncode == 0:
            safe_print("  OCR complete!")
            return ocr_output
        else:
            safe_print(f"  OCR warning: {result.stderr[:200]}")
            # Try simpler OCR without force
            result = subprocess.run([
                'ocrmypdf',
                '--skip-text',
                '-l', 'eng',
                filepath,
                ocr_output
            ], capture_output=True, text=True, timeout=600)
            if result.returncode == 0:
                return ocr_output
            return None
    except subprocess.TimeoutExpired:
        safe_print("  OCR timed out after 10 minutes")
        return None
    except FileNotFoundError:
        safe_print("  OCR not available - install with: sudo apt install ocrmypdf")
        return None


def extract_pdf_pages(filepath: str) -> list:
    """Extract text from PDF, one entry per page. Uses OCR for scanned PDFs."""
    pages = []

    # First try direct text extraction
    with pdfplumber.open(filepath) as pdf:
        for i, page in enumerate(pdf.pages):
            text = page.extract_text() or ""
            if text.strip():
                pages.append({
                    "page": i + 1,
                    "content": text,
                    "char_count": len(text)
                })

    # If we got very little text, it's probably a scanned PDF - try OCR
    total_chars = sum(p.get("char_count", 0) for p in pages)
    if total_chars < 1000:  # Less than 1000 chars from a PDF usually means scanned
        safe_print(f"  Only {total_chars} characters extracted - attempting OCR...")
        ocr_path = ocr_pdf(filepath)

        if ocr_path:
            # Re-extract from OCR'd PDF
            pages = []
            try:
                with pdfplumber.open(ocr_path) as pdf:
                    for i, page in enumerate(pdf.pages):
                        text = page.extract_text() or ""
                        if text.strip():
                            pages.append({
                                "page": i + 1,
                                "content": text,
                                "char_count": len(text)
                            })
            finally:
                # Clean up temp file
                try:
                    os.unlink(ocr_path)
                except:
                    pass

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
    """Store a chunk in pgai - embeddings handled by triggers"""
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
        safe_print(f"  Store error: {e}")
        return False


def process_page(page_data: dict, source_file: str, total_pages: int) -> int:
    """Process a single page - chunk and store"""
    page_num = page_data["page"]
    content = page_data["content"]

    safe_print(f"  [Page {page_num}/{total_pages}] Processing...")

    # Chunk the page content
    chunks = chunk_text(content, chunk_size=800, overlap=100)

    stored = 0
    for i, chunk in enumerate(chunks):
        metadata = {
            "source_file": source_file,
            "page": page_num,
            "chunk": i + 1,
            "total_chunks_in_page": len(chunks),
            "type": "autobiography",
            "namespace": "wolf_story",
            "ingested_at": datetime.now().isoformat()
        }

        if store_chunk(chunk, metadata):
            stored += 1

    safe_print(f"  [Page {page_num}/{total_pages}] Stored {stored}/{len(chunks)} chunks")
    return stored


def ingest_pdf(filepath: str):
    """Main ingestion pipeline"""
    filename = os.path.basename(filepath)

    print("=" * 60)
    print("INGESTION AGENT - Dismantling Document")
    print("=" * 60)
    print(f"File: {filename}")
    print(f"Target: pgai @ wolf_logic")
    print("=" * 60)

    # Extract pages
    print("\nExtracting pages from PDF...")
    pages = extract_pdf_pages(filepath)
    print(f"Extracted {len(pages)} pages with content")

    total_chars = sum(p["char_count"] for p in pages)
    print(f"Total characters: {total_chars:,}")

    # Process pages in parallel
    print(f"\nDeploying {min(8, len(pages))} workers...")

    total_stored = 0
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = {
            executor.submit(process_page, page, filename, len(pages)): page["page"]
            for page in pages
        }

        for future in as_completed(futures):
            page_num = futures[future]
            try:
                stored = future.result()
                total_stored += stored
            except Exception as e:
                safe_print(f"  [Page {page_num}] Error: {e}")

    print("\n" + "=" * 60)
    print(f"INGESTION COMPLETE")
    print(f"Pages processed: {len(pages)}")
    print(f"Chunks stored: {total_stored}")
    print(f"Embeddings: Pending (pgai vectorizer will process)")
    print("=" * 60)

    return total_stored


def ingest_jsonl(filepath: str):
    """Ingest a JSONL file - each line is a JSON object, or fallback to raw text"""
    filename = os.path.basename(filepath)

    print("=" * 60)
    print("INGESTION AGENT - Dismantling JSONL Document")
    print("=" * 60)
    print(f"File: {filename}")
    print(f"Target: pgai @ wolf_logic")
    print("=" * 60)

    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    lines = content.strip().split('\n')
    print(f"Total lines: {len(lines)}")

    # Try parsing as actual JSONL first
    json_objects = []
    valid_json = True
    for line in lines:
        if line.strip():
            try:
                obj = json.loads(line)
                json_objects.append(obj)
            except json.JSONDecodeError:
                valid_json = False
                break

    if valid_json and json_objects:
        print(f"Valid JSONL - {len(json_objects)} records")
        # Store each JSON object as a chunk
        total_stored = 0
        for i, obj in enumerate(json_objects):
            # Extract content - try common fields
            chunk_content = obj.get('content') or obj.get('text') or obj.get('message') or json.dumps(obj)
            metadata = {
                "source_file": filename,
                "record": i + 1,
                "total_records": len(json_objects),
                "type": "jsonl_record",
                "namespace": "session_recovery",
                "ingested_at": datetime.now().isoformat(),
                "original_keys": list(obj.keys()) if isinstance(obj, dict) else []
            }
            if store_chunk(str(chunk_content), metadata):
                total_stored += 1
            if (i + 1) % 100 == 0:
                print(f"  Stored {i + 1}/{len(json_objects)} records...")
    else:
        print("Not valid JSONL - treating as raw text")
        # Fallback to text chunking
        chunks = chunk_text(content, chunk_size=800, overlap=100)
        print(f"Split into {len(chunks)} chunks")

        total_stored = 0
        for i, chunk in enumerate(chunks):
            metadata = {
                "source_file": filename,
                "chunk": i + 1,
                "total_chunks": len(chunks),
                "type": "session_dump",
                "namespace": "session_recovery",
                "ingested_at": datetime.now().isoformat()
            }
            if store_chunk(chunk, metadata):
                total_stored += 1
            if (i + 1) % 50 == 0:
                print(f"  Stored {i + 1}/{len(chunks)} chunks...")

    print("\n" + "=" * 60)
    print(f"INGESTION COMPLETE")
    print(f"Chunks stored: {total_stored}")
    print("=" * 60)

    return total_stored


def ingest_txt(filepath: str):
    """Ingest a plain text file"""
    filename = os.path.basename(filepath)

    print("=" * 60)
    print("INGESTION AGENT - Dismantling Text Document")
    print("=" * 60)
    print(f"File: {filename}")
    print(f"Target: pgai @ wolf_logic")
    print("=" * 60)

    # Read the file
    with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    print(f"Total characters: {len(content):,}")

    # Chunk it
    chunks = chunk_text(content, chunk_size=800, overlap=100)
    print(f"Split into {len(chunks)} chunks")

    # Store chunks
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
        if (i + 1) % 50 == 0:
            print(f"  Stored {i + 1}/{len(chunks)} chunks...")

    print("\n" + "=" * 60)
    print(f"INGESTION COMPLETE")
    print(f"Chunks stored: {total_stored}")
    print("=" * 60)

    return total_stored


def main():
    if len(sys.argv) < 2:
        print("Usage: python ingest_agent.py <filepath>")
        print("  Supports: PDF, TXT, MD, JSONL files")
        sys.exit(1)

    filepath = sys.argv[1]

    if not os.path.exists(filepath):
        print(f"Error: File not found: {filepath}")
        sys.exit(1)

    if filepath.lower().endswith('.pdf'):
        ingest_pdf(filepath)
    elif filepath.lower().endswith(('.jsonl', '.json')):
        ingest_jsonl(filepath)
    elif filepath.lower().endswith(('.txt', '.md', '.text', '.markdown')):
        ingest_txt(filepath)
    else:
        print(f"Error: Unsupported file type. Supports: PDF, TXT, MD, JSONL")
        sys.exit(1)


if __name__ == "__main__":
    main()
