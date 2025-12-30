#!/usr/bin/env python3
"""
WordPress → PostgreSQL Memory Sync
Syncs WordPress posts and pages into wolf_logic database as memories.
"""

import os
import sys
import requests
import psycopg2
import psycopg2.extras
from datetime import datetime
from typing import List, Dict

# WordPress API settings
WP_URL = os.getenv("WORDPRESS_URL", "http://localhost:8082")
WP_USER = os.getenv("WORDPRESS_USER", "")
WP_PASSWORD = os.getenv("WORDPRESS_PASSWORD", "")

# PostgreSQL settings
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

def fetch_wordpress_content(content_type: str = "posts", per_page: int = 100) -> List[Dict]:
    """Fetch posts or pages from WordPress REST API"""
    url = f"{WP_URL}/wp-json/wp/v2/{content_type}"
    params = {"per_page": per_page, "status": "publish"}

    try:
        if WP_USER and WP_PASSWORD:
            response = requests.get(url, params=params, auth=(WP_USER, WP_PASSWORD))
        else:
            response = requests.get(url, params=params)

        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {content_type}: {e}")
        return []

def clean_html(html: str) -> str:
    """Remove HTML tags and clean content"""
    import re
    # Remove HTML tags
    text = re.sub(r'<[^>]+>', '', html)
    # Decode HTML entities
    import html as html_module
    text = html_module.unescape(text)
    # Clean up whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def sync_to_postgres(items: List[Dict], content_type: str):
    """Sync WordPress content to PostgreSQL"""
    conn = psycopg2.connect(**PG_CONFIG)
    cur = conn.cursor()

    synced = 0
    skipped = 0

    for item in items:
        wp_id = item.get('id')
        title = item.get('title', {}).get('rendered', 'Untitled')
        content_html = item.get('content', {}).get('rendered', '')
        excerpt = item.get('excerpt', {}).get('rendered', '')
        link = item.get('link', '')
        published = item.get('date_gmt', '')
        modified = item.get('modified_gmt', '')

        # Clean HTML content
        content = clean_html(content_html)
        excerpt_clean = clean_html(excerpt)

        # Build full content
        full_content = f"{title}\n\n{content}"
        if excerpt_clean:
            full_content = f"{title}\n{excerpt_clean}\n\n{content}"

        # Create metadata
        metadata = {
            "wordpress_id": wp_id,
            "title": title,
            "url": link,
            "type": content_type.rstrip('s'),  # "posts" -> "post", "pages" -> "page"
            "published_date": published,
            "modified_date": modified,
            "source": "wordpress"
        }

        # Check if already exists
        cur.execute("""
            SELECT id FROM memories
            WHERE metadata->>'wordpress_id' = %s
            AND namespace = 'wordpress'
        """, (str(wp_id),))

        existing = cur.fetchone()

        if existing:
            # Update existing memory
            cur.execute("""
                UPDATE memories
                SET content = %s,
                    metadata = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (full_content, psycopg2.extras.Json(metadata), existing[0]))
            skipped += 1
        else:
            # Insert new memory
            cur.execute("""
                INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (
                "wordpress_sync",
                full_content,
                psycopg2.extras.Json(metadata),
                f"wordpress_{content_type.rstrip('s')}",
                "wordpress",
                published if published else datetime.utcnow(),
                modified if modified else datetime.utcnow()
            ))
            synced += 1

    conn.commit()
    cur.close()
    conn.close()

    return synced, skipped

def main():
    print("=" * 60)
    print("WordPress → PostgreSQL Memory Sync")
    print("=" * 60)
    print(f"WordPress URL: {WP_URL}")
    print(f"PostgreSQL: {PG_CONFIG['host']}:{PG_CONFIG['port']}/{PG_CONFIG['database']}")
    print()

    # Sync posts
    print("Fetching WordPress posts...")
    posts = fetch_wordpress_content("posts")
    print(f"Found {len(posts)} published posts")

    if posts:
        print("Syncing posts to PostgreSQL...")
        synced, skipped = sync_to_postgres(posts, "posts")
        print(f"  New: {synced}")
        print(f"  Updated: {skipped}")

    print()

    # Sync pages
    print("Fetching WordPress pages...")
    pages = fetch_wordpress_content("pages")
    print(f"Found {len(pages)} published pages")

    if pages:
        print("Syncing pages to PostgreSQL...")
        synced, skipped = sync_to_postgres(pages, "pages")
        print(f"  New: {synced}")
        print(f"  Updated: {skipped}")

    print()
    print("=" * 60)
    print("Sync complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
