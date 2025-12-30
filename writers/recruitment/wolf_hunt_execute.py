#!/usr/bin/env python3
"""
Wolf Hunt - Full Execution
Aggregates jobs across all search terms and locations
Stores in PostgreSQL for Phase 2 (resume generation)
"""

from jobspy import scrape_jobs
import psycopg2
import json
from datetime import datetime
from pathlib import Path
import pandas as pd

# Database config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Search terms (your specified titles)
SEARCH_TERMS = [
    "AI engineer senior",
    "Lead DevOps engineer",
    "AI engineer",
    "DevOps engineer",
    "Full stack developer",
    "Senior full stack developer",
    "Full stack developer Java",
    "Full stack developer ReactJS",
    "Senior developer React",
    # Unreal Engine positions
    "Unreal Engine developer",
    "Unreal Engine technical artist",
    "Technical artist Unreal",
    "Unreal Engine lighting artist",
    "Cinematics developer Unreal",
    "Real-time rendering engineer"
]

# Priority locations
LOCATIONS = [
    {"name": "Atlanta, GA", "priority": 1, "reason": "Local - no move"},
    {"name": "Los Angeles, CA", "priority": 2, "reason": "Son is here"},
    {"name": "Las Vegas, NV", "priority": 3, "reason": "3 hours from son"},
    {"name": "remote", "priority": 1, "reason": "No relocation needed"}  # Remote gets priority 1
]

# Job boards
SITES = ['indeed', 'linkedin', 'zip_recruiter']


def aggregate_jobs():
    """Run all searches and aggregate results"""
    print("=" * 70)
    print("WOLF HUNT - FULL JOB AGGREGATION")
    print("=" * 70)
    print(f"Search Terms: {len(SEARCH_TERMS)}")
    print(f"Locations: {len(LOCATIONS)}")
    print(f"Sites: {', '.join(SITES)}")
    print("=" * 70)
    print()

    all_jobs = []
    search_count = 0
    total_searches = len(SEARCH_TERMS) * len(LOCATIONS)

    for search_term in SEARCH_TERMS:
        for location_info in LOCATIONS:
            location = location_info['name']
            search_count += 1

            print(f"[{search_count}/{total_searches}] {search_term} in {location}...")

            try:
                is_remote = location.lower() == 'remote'

                jobs_df = scrape_jobs(
                    site_name=SITES,
                    search_term=search_term,
                    location='' if is_remote else location,
                    is_remote=is_remote,
                    results_wanted=25,
                    hours_old=168,  # 7 days
                    country_indeed='USA'
                )

                # Add priority and search metadata
                jobs_df['search_term'] = search_term
                jobs_df['search_location'] = location
                jobs_df['location_priority'] = location_info['priority']
                jobs_df['location_reason'] = location_info['reason']

                all_jobs.append(jobs_df)

                print(f"  ✓ Found {len(jobs_df)} jobs")

            except Exception as e:
                print(f"  ✗ Error: {e}")

    print()
    print("=" * 70)

    if not all_jobs:
        print("No jobs found!")
        return None

    # Combine all results
    combined = pd.concat(all_jobs, ignore_index=True)

    # Deduplicate by job URL
    combined = combined.drop_duplicates(subset=['job_url'], keep='first')

    print(f"Total jobs found: {len(combined)}")
    print(f"After deduplication: {len(combined)}")
    print("=" * 70)

    return combined


def store_jobs(jobs_df):
    """Store jobs in PostgreSQL wolf_hunt namespace"""
    if jobs_df is None or len(jobs_df) == 0:
        print("No jobs to store")
        return

    print()
    print("Storing jobs in database...")

    try:
        conn = psycopg2.connect(**PG_CONFIG)
        now = datetime.now()
        stored_count = 0

        with conn.cursor() as cur:
            for _, job in jobs_df.iterrows():
                # Build content
                content = f"""Job: {job.get('title', 'N/A')} at {job.get('company', 'N/A')}
Location: {job.get('location', 'N/A')}
Site: {job.get('site', 'N/A')}
Posted: {job.get('date_posted', 'N/A')}
Salary: {job.get('min_annual_salary_usd', 'N/A')} - {job.get('max_annual_salary_usd', 'N/A')} USD
Remote: {job.get('is_remote', False)}
URL: {job.get('job_url', 'N/A')}

Description:
{str(job.get('description', ''))[:1000]}
"""

                # Build metadata
                metadata = {
                    "source": "wolf_hunt",
                    "job_site": str(job.get('site', 'unknown')),
                    "title": str(job.get('title', '')),
                    "company": str(job.get('company', '')),
                    "location": str(job.get('location', '')),
                    "url": str(job.get('job_url', '')),
                    "date_posted": str(job.get('date_posted', '')),
                    "search_term": str(job.get('search_term', '')),
                    "search_location": str(job.get('search_location', '')),
                    "location_priority": int(job.get('location_priority', 5)),
                    "location_reason": str(job.get('location_reason', '')),
                    "is_remote": bool(job.get('is_remote', False)),
                    "salary_min": float(job.get('min_annual_salary_usd', 0)) if pd.notna(job.get('min_annual_salary_usd')) else 0,
                    "salary_max": float(job.get('max_annual_salary_usd', 0)) if pd.notna(job.get('max_annual_salary_usd')) else 0,
                    "scraped_at": now.isoformat()
                }

                try:
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
                    stored_count += 1
                except Exception as e:
                    print(f"  Error storing job: {e}")
                    continue

        conn.commit()
        conn.close()

        print(f"✓ Stored {stored_count} jobs in database (wolf_hunt namespace)")

    except Exception as e:
        print(f"Database error: {e}")


def export_jobs(jobs_df, output_file='/tmp/wolf_hunt_jobs.json'):
    """Export jobs to JSON"""
    if jobs_df is None or len(jobs_df) == 0:
        print("No jobs to export")
        return

    try:
        # Convert to dict and handle NaN values
        jobs_list = jobs_df.to_dict('records')

        # Clean NaN values
        for job in jobs_list:
            for key, value in job.items():
                if pd.isna(value):
                    job[key] = None

        with open(output_file, 'w') as f:
            json.dump(jobs_list, f, indent=2, default=str)

        print(f"✓ Exported to {output_file}")

    except Exception as e:
        print(f"Export error: {e}")


def main():
    print()
    print("🐺 WOLF HUNT EXECUTION")
    print("Fighting for family")
    print()

    # Aggregate
    jobs = aggregate_jobs()

    if jobs is not None:
        # Store in database
        store_jobs(jobs)

        # Export to JSON
        export_jobs(jobs)

        print()
        print("=" * 70)
        print("WOLF HUNT PHASE 1 COMPLETE")
        print(f"Total unique jobs: {len(jobs)}")
        print("Ready for Phase 2: Resume Generation")
        print("=" * 70)
        print()

        # Show top 10 by priority
        print("Top 10 jobs by location priority:")
        top_jobs = jobs.nsmallest(10, 'location_priority')
        for i, (_, job) in enumerate(top_jobs.iterrows(), 1):
            print(f"{i:2}. [{job['location_priority']}] {job['title'][:50]:50} at {job['company'][:30]:30} ({job['search_location']})")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
