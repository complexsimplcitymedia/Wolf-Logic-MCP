#!/usr/bin/env python3
"""
Quick Atlanta Job Hunt Script
Search for jobs in Atlanta area for both candidates
"""

import asyncio
import sys
sys.path.insert(0, '/mnt/Wolf-code/Wolf-Ai-Enterptises/wolf-hunt-ui')

from job_boards.indeed_board import IndeedBoard
import psycopg2
from psycopg2.extras import RealDictCursor
import json

DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'user': 'wolf',
    'password': 'wolflogic2024',
    'database': 'wolf_logic'
}

async def search_atlanta_jobs():
    """Search for Atlanta jobs for both candidates"""

    print("\n" + "="*60)
    print("🐺 WOLF HUNT - ATLANTA AREA JOB SEARCH")
    print("="*60 + "\n")

    # Initialize Indeed board
    indeed = IndeedBoard()

    # Search queries for each candidate
    searches = [
        {
            'candidate': 'David Adams',
            'queries': [
                'DevOps Engineer',
                'Senior AI Engineer',
                'AI/ML Engineer'
            ]
        },
        {
            'candidate': 'Brice Wilson',
            'queries': [
                'National Sales Manager AI',
                'SaaS Account Manager',
                'Account Executive SaaS'
            ]
        }
    ]

    all_jobs = {}

    for search_group in searches:
        candidate = search_group['candidate']
        all_jobs[candidate] = []

        print(f"\n{'='*60}")
        print(f"Searching for: {candidate}")
        print(f"{'='*60}\n")

        for query in search_group['queries']:
            print(f"  🔍 {query} in Atlanta, GA...")

            try:
                jobs = await indeed.search(
                    query=query,
                    location="Atlanta, GA",
                    limit=25
                )

                print(f"     ✓ Found {len(jobs)} positions")
                all_jobs[candidate].extend(jobs)

                # Show first 3 results
                for i, job in enumerate(jobs[:3], 1):
                    print(f"     {i}. {job['title']} at {job['company']}")

                # Rate limit respect
                await asyncio.sleep(2)

            except Exception as e:
                print(f"     ✗ Error: {e}")

    # Summary
    print(f"\n{'='*60}")
    print("SEARCH SUMMARY")
    print(f"{'='*60}\n")

    for candidate, jobs in all_jobs.items():
        unique_jobs = {j['id']: j for j in jobs}.values()
        print(f"{candidate}: {len(unique_jobs)} unique positions found")

    # Save to database
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Create jobs table if not exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scraped_jobs (
                id VARCHAR(32) PRIMARY KEY,
                title VARCHAR(500),
                company VARCHAR(500),
                location VARCHAR(500),
                description TEXT,
                url TEXT,
                source VARCHAR(100),
                board VARCHAR(100),
                date_posted TIMESTAMP,
                salary VARCHAR(200),
                job_type VARCHAR(100),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                candidate_match VARCHAR(255)
            )
        """)

        saved_count = 0
        for candidate, jobs in all_jobs.items():
            for job in jobs:
                try:
                    cur.execute("""
                        INSERT INTO scraped_jobs
                        (id, title, company, location, description, url, source, board,
                         date_posted, salary, job_type, candidate_match)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (id) DO UPDATE SET
                            scraped_at = CURRENT_TIMESTAMP,
                            candidate_match = EXCLUDED.candidate_match
                    """, (
                        job['id'], job['title'], job['company'], job['location'],
                        job['description'], job['url'], job['source'], job['board'],
                        job['date_posted'], job.get('salary'), job.get('job_type'),
                        candidate
                    ))
                    saved_count += 1
                except Exception as e:
                    print(f"Error saving job: {e}")

        conn.commit()
        cur.close()
        conn.close()

        print(f"\n✓ Saved {saved_count} jobs to database")
        print(f"  Access via: http://localhost:5000/api/jobs/scraped")

    except Exception as e:
        print(f"\n✗ Database error: {e}")

    print(f"\n{'='*60}")
    print("Hunt complete. The prey has been marked.")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    asyncio.run(search_atlanta_jobs())
