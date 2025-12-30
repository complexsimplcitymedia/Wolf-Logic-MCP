#!/usr/bin/env python3
"""Bulk import existing categorized memories into pgai"""
import json
import psycopg2
from datetime import datetime

EXPORT_FILE = '/mnt/Wolf-code/memory_layer/mem0/memory_export/mem0_complete_export.json'

print("Loading memories...")
with open(EXPORT_FILE, 'r') as f:
    memories = json.load(f)

print(f"Loaded {len(memories)} memories")

conn = psycopg2.connect(
    host="localhost", port=5433, database="wolf_logic",
    user="wolf", password="wolflogic2024"
)

inserted = 0
errors = 0

with conn.cursor() as cur:
    for i, mem in enumerate(memories):
        try:
            metadata = {
                "provider": mem.get("metadata", {}).get("provider", ""),
                "categories": mem.get("categories", []),
                "ai_categorization": mem.get("ai_categorization", {}),
                "structured_attributes": mem.get("structured_attributes", {}),
                "original_id": mem.get("id", "")
            }

            cur.execute("""
                INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                mem.get("user_id", "thewolfwalksalone"),
                mem.get("memory", ""),
                json.dumps(metadata),
                mem.get("ai_categorization", {}).get("category", "general"),
                "mem0_import",
                mem.get("created_at", datetime.now().isoformat()),
                mem.get("updated_at", datetime.now().isoformat())
            ))
            inserted += 1

            if inserted % 500 == 0:
                conn.commit()
                print(f"  {inserted} inserted...")

        except Exception as e:
            errors += 1
            conn.rollback()

    conn.commit()

conn.close()
print(f"\nDone! Inserted {inserted}, Errors {errors}")
