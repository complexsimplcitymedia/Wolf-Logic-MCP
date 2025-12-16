#!/usr/bin/env python3
"""
Wolf Hunt Resume Generator - PARALLEL VERSION
Union way: 9 workers, each gets jobs, coordinator collects results
"""

import json
import psycopg2
import ollama
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# Config
PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Worker fleet - qwen2.5 only (fast resume generation)
WORKERS = ["qwen2.5:0.5b"] * 9  # 9 workers all using same model


def get_candidate_background():
    """Query memory system for David's background"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)

        queries = [
            "SELECT content FROM memories WHERE namespace = 'core_identity' LIMIT 10",
            "SELECT content FROM memories WHERE content ILIKE '%production%' OR content ILIKE '%film%' LIMIT 20",
            "SELECT content FROM memories WHERE content ILIKE '%python%' OR content ILIKE '%AI%' OR content ILIKE '%docker%' LIMIT 20",
            "SELECT content FROM memories WHERE content ILIKE '%department%' OR content ILIKE '%management%' LIMIT 10"
        ]

        background = {
            "core_identity": [],
            "production_experience": [],
            "technical_skills": [],
            "leadership": []
        }

        with conn.cursor() as cur:
            cur.execute(queries[0])
            background["core_identity"] = [row[0] for row in cur.fetchall()]

            cur.execute(queries[1])
            background["production_experience"] = [row[0] for row in cur.fetchall()]

            cur.execute(queries[2])
            background["technical_skills"] = [row[0] for row in cur.fetchall()]

            cur.execute(queries[3])
            background["leadership"] = [row[0] for row in cur.fetchall()]

        conn.close()
        return background

    except Exception as e:
        print(f"[Librarian Error] {e}")
        return None


def generate_resume_worker(job, background, worker_id):
    """Worker function - generates one resume"""
    try:
        # Build context
        context = f"""
CANDIDATE BACKGROUND:

Production Experience:
{chr(10).join(background.get('production_experience', [])[:5])}

Technical Skills:
{chr(10).join(background.get('technical_skills', [])[:5])}

Leadership:
{chr(10).join(background.get('leadership', [])[:3])}
"""

        job_description = f"""
JOB: {job.get('title', 'N/A')}
COMPANY: {job.get('company', 'N/A')}
LOCATION: {job.get('location', 'N/A')}

DESCRIPTION:
{job.get('description', '')[:1000]}
"""

        prompt = f"""You are a professional resume writer. Create a tailored resume (200-300 words) that matches this job.

{context}

{job_description}

Write a concise resume highlighting relevant experience, technical skills, and leadership. Use industry language. Be truthful but optimally framed.

RESUME:"""

        # Generate
        response = ollama.generate(
            model="qwen2.5:0.5b",
            prompt=prompt
        )

        resume_text = response['response']

        print(f"[Worker {worker_id}] ✓ {job.get('title', 'N/A')[:50]} at {job.get('company', 'N/A')}")

        return {
            "job_title": job.get('title', 'N/A'),
            "company": job.get('company', 'N/A'),
            "location": job.get('location', 'N/A'),
            "job_url": job.get('job_url', ''),
            "resume_text": resume_text,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"[Worker {worker_id}] ✗ Error: {e}")
        return None


def generate_parallel(jobs, background, output_dir="/tmp/wolf_hunt_resumes"):
    """Parallel generation with thread pool"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("WOLF HUNT - PARALLEL RESUME GENERATION")
    print("=" * 70)
    print(f"Jobs: {len(jobs)}")
    print(f"Workers: {len(WORKERS)}")
    print(f"Output: {output_dir}")
    print("=" * 70)
    print()

    resumes = []

    # Fan out to thread pool
    with ThreadPoolExecutor(max_workers=len(WORKERS)) as executor:
        futures = []
        for i, job in enumerate(jobs):
            worker_id = (i % len(WORKERS)) + 1
            future = executor.submit(generate_resume_worker, job, background, worker_id)
            futures.append(future)

        # Collect results as they complete
        for future in as_completed(futures):
            resume = future.result()
            if resume:
                resumes.append(resume)

                # Save individual file
                safe_company = resume['company'].replace(' ', '_').replace('/', '_')[:50]
                safe_title = resume['job_title'].replace(' ', '_').replace('/', '_')[:50]
                filename = f"{output_dir}/{safe_company}_{safe_title}.txt"

                try:
                    with open(filename, 'w') as f:
                        f.write(f"RESUME FOR: {resume['job_title']}\n")
                        f.write(f"COMPANY: {resume['company']}\n")
                        f.write(f"LOCATION: {resume['location']}\n")
                        f.write(f"JOB URL: {resume['job_url']}\n")
                        f.write("=" * 60 + "\n\n")
                        f.write(resume['resume_text'])
                except Exception as e:
                    print(f"[Save Error] {e}")

    # Save metadata
    try:
        with open(f"{output_dir}/all_resumes.json", 'w') as f:
            json.dump(resumes, f, indent=2)
    except Exception as e:
        print(f"[Export Error] {e}")

    print()
    print("=" * 70)
    print(f"PHASE 2 COMPLETE - {len(resumes)} resumes generated")
    print("=" * 70)

    return resumes


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Parallel Resume Generator')
    parser.add_argument('--job-file', type=str, required=True)
    parser.add_argument('--output-dir', type=str, default='/tmp/wolf_hunt_resumes')
    parser.add_argument('--limit', type=int, default=None)

    args = parser.parse_args()

    # Load jobs
    with open(args.job_file, 'r') as f:
        jobs = json.load(f)
    print(f"✓ Loaded {len(jobs)} jobs")

    if args.limit:
        jobs = jobs[:args.limit]
        print(f"[Limit] Processing first {args.limit} jobs")

    # Get background
    background = get_candidate_background()
    if not background:
        print("[Error] Could not retrieve background")
        return 1

    print("[Librarian] Retrieved candidate background")
    print()

    # Generate in parallel
    resumes = generate_parallel(jobs, background, args.output_dir)

    print(f"\nResumes available in: {args.output_dir}/")

    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
