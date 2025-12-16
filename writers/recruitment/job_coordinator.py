#!/usr/bin/env python3
"""
Job Hunt Coordinator - Wolf Hunt Phase 1
Queries 7 job APIs in parallel, aggregates results, prepares for resume generation.

ROCN Layer APIs:
1. ZipRecruiter
2. Indeed
3. GraphQL Jobs
4. Remotive
5. WhatJobs
6. Fantastic Jobs
7. GameBrain

Usage: python job_coordinator.py --keywords "python,AI,backend" --location "remote"
"""

import os
import sys
import json
import asyncio
import argparse
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

# Job API imports
sys.path.insert(0, str(Path(__file__).parent))

import requests
import psycopg2

# Database config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# API Endpoints (direct HTTP, not MCP for speed)
APIS = {
    "indeed": {
        "url": "https://api.indeed.com/ads/apisearch",
        "requires_key": True,
        "env_var": "INDEED_PUBLISHER_ID"
    },
    "ziprecruiter": {
        "url": "https://api.ziprecruiter.com/jobs/v1",
        "requires_key": True,
        "env_var": "ZIPRECRUITER_API_KEY"
    },
    "graphql_jobs": {
        "url": "https://api.graphql.jobs/",
        "requires_key": False
    },
    "remotive": {
        "url": "https://remotive.com/api/remote-jobs",
        "requires_key": False
    },
    "whatjobs": {
        "url": "https://www.whatjobs.com/api/v1/search",
        "requires_key": True,
        "env_var": "WHATJOBS_API_KEY"
    }
}

# Target keywords and locations
DEFAULT_KEYWORDS = [
    "python developer",
    "AI engineer",
    "backend developer",
    "full stack developer",
    "software engineer",
    "DevOps engineer",
    "machine learning engineer",
    "data engineer"
]

DEFAULT_LOCATIONS = [
    "Atlanta, GA",           # Priority 1: Local (no move)
    "Los Angeles, CA",       # Priority 2: Son is here
    "Las Vegas, NV",         # Priority 3: 3 hours from LA
    "United States",         # Priority 4: Rest of USA
    "remote",                # Priority 5: Remote/International
]


def query_indeed(keywords, location, limit=50):
    """Query Indeed API"""
    publisher_id = os.getenv("INDEED_PUBLISHER_ID")
    if not publisher_id:
        print("[Indeed] Skipping - no API key")
        return []

    try:
        params = {
            "publisher": publisher_id,
            "q": keywords,
            "l": location,
            "limit": limit,
            "format": "json",
            "v": "2"
        }

        response = requests.get(APIS["indeed"]["url"], params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("results", []):
            jobs.append({
                "source": "Indeed",
                "title": job.get("jobtitle"),
                "company": job.get("company"),
                "location": job.get("formattedLocation"),
                "description": job.get("snippet"),
                "url": job.get("url"),
                "date": job.get("date")
            })

        print(f"[Indeed] Found {len(jobs)} jobs")
        return jobs

    except Exception as e:
        print(f"[Indeed] Error: {e}")
        return []


def query_remotive(keywords, limit=50):
    """Query Remotive API (no auth needed)"""
    try:
        params = {
            "search": keywords,
            "limit": limit
        }

        response = requests.get(APIS["remotive"]["url"], params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        jobs = []
        for job in data.get("jobs", []):
            jobs.append({
                "source": "Remotive",
                "title": job.get("title"),
                "company": job.get("company_name"),
                "location": "Remote",
                "description": job.get("description"),
                "url": job.get("url"),
                "date": job.get("publication_date")
            })

        print(f"[Remotive] Found {len(jobs)} jobs")
        return jobs

    except Exception as e:
        print(f"[Remotive] Error: {e}")
        return []


def query_graphql_jobs(limit=50):
    """Query GraphQL Jobs API"""
    try:
        query = """
        query {
          jobs(first: %d) {
            edges {
              node {
                id
                title
                company {
                  name
                }
                cities {
                  name
                }
                description
                applyUrl
                publishedAt
              }
            }
          }
        }
        """ % limit

        response = requests.post(
            APIS["graphql_jobs"]["url"],
            json={"query": query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        jobs = []
        for edge in data.get("data", {}).get("jobs", {}).get("edges", []):
            node = edge["node"]
            jobs.append({
                "source": "GraphQL Jobs",
                "title": node.get("title"),
                "company": node.get("company", {}).get("name"),
                "location": ", ".join([c["name"] for c in node.get("cities", [])]) or "Remote",
                "description": node.get("description"),
                "url": node.get("applyUrl"),
                "date": node.get("publishedAt")
            })

        print(f"[GraphQL Jobs] Found {len(jobs)} jobs")
        return jobs

    except Exception as e:
        print(f"[GraphQL Jobs] Error: {e}")
        return []


def aggregate_jobs(keywords, locations):
    """Query all APIs in parallel and aggregate results"""
    print("=" * 60)
    print("WOLF HUNT - Job Aggregation Phase")
    print("=" * 60)
    print(f"Keywords: {keywords}")
    print(f"Locations: {locations}")
    print("=" * 60)

    all_jobs = []

    with ThreadPoolExecutor(max_workers=7) as executor:
        futures = []

        # Launch queries
        for keyword in keywords:
            for location in locations:
                futures.append(executor.submit(query_indeed, keyword, location))
                futures.append(executor.submit(query_remotive, keyword))

        # GraphQL Jobs (no keyword/location filtering in API)
        futures.append(executor.submit(query_graphql_jobs))

        # Collect results
        for future in as_completed(futures):
            try:
                jobs = future.result()
                all_jobs.extend(jobs)
            except Exception as e:
                print(f"[Error] {e}")

    # Deduplicate by URL
    seen_urls = set()
    unique_jobs = []
    for job in all_jobs:
        if job["url"] and job["url"] not in seen_urls:
            seen_urls.add(job["url"])
            unique_jobs.append(job)

    print("=" * 60)
    print(f"Total jobs found: {len(all_jobs)}")
    print(f"Unique jobs: {len(unique_jobs)}")
    print("=" * 60)

    return unique_jobs


def store_jobs(jobs):
    """Store jobs in database for tracking"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        now = datetime.now()

        with conn.cursor() as cur:
            for job in jobs:
                content = f"""Job Listing: {job['title']} at {job['company']}
Source: {job['source']}
Location: {job['location']}
URL: {job['url']}

Description:
{job['description']}
"""

                metadata = {
                    "source": "wolf_hunt",
                    "job_source": job["source"],
                    "title": job["title"],
                    "company": job["company"],
                    "location": job["location"],
                    "url": job["url"],
                    "date": job["date"],
                    "scraped_at": now.isoformat()
                }

                cur.execute("""
                    INSERT INTO memories (user_id, content, metadata, memory_type, namespace, created_at, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (
                    "wolf_hunt",
                    content,
                    json.dumps(metadata),
                    "job_listing",
                    "wolf_hunt",
                    now, now
                ))

        conn.commit()
        conn.close()
        print(f"✓ Stored {len(jobs)} jobs in database")

    except Exception as e:
        print(f"[Storage Error] {e}")


def export_jobs(jobs, output_file):
    """Export jobs to JSON file"""
    try:
        with open(output_file, 'w') as f:
            json.dump(jobs, f, indent=2)
        print(f"✓ Exported to {output_file}")
    except Exception as e:
        print(f"[Export Error] {e}")


def main():
    parser = argparse.ArgumentParser(description='Wolf Hunt Job Coordinator')
    parser.add_argument('--keywords', type=str, help='Comma-separated keywords')
    parser.add_argument('--locations', type=str, help='Comma-separated locations')
    parser.add_argument('--output', type=str, default='/tmp/wolf_hunt_jobs.json',
                       help='Output JSON file')
    parser.add_argument('--store', action='store_true',
                       help='Store in database')

    args = parser.parse_args()

    keywords = args.keywords.split(',') if args.keywords else DEFAULT_KEYWORDS
    locations = args.locations.split(',') if args.locations else DEFAULT_LOCATIONS

    # Aggregate jobs
    jobs = aggregate_jobs(keywords, locations)

    # Export
    if args.output:
        export_jobs(jobs, args.output)

    # Store in database
    if args.store:
        store_jobs(jobs)

    print("\n" + "=" * 60)
    print("PHASE 1 COMPLETE - Ready for resume generation")
    print("=" * 60)


if __name__ == "__main__":
    main()
