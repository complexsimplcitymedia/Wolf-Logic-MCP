#!/usr/bin/env python3
"""
Wolf Hunt Resume Generator - Phase 2
Generates custom resumes per job using memory system + LLM.

Workflow:
1. Query librarian for David's full background
2. Load job listing requirements
3. Use qwen2.5 to rewrite resume matching requirements
4. Output custom resume per position

Usage: python resume_generator.py --job-file /tmp/wolf_hunt_jobs.json
"""

import os
import sys
import json
import psycopg2
import ollama
from pathlib import Path
from datetime import datetime

# Config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

EXTRACTION_MODEL = "qwen2.5:0.5b"  # Fast model for resume generation


def get_candidate_background():
    """Query memory system for David's full background"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)

        # Get core identity, experience, and skills from memories
        queries = [
            # Core identity/constitution
            "SELECT content FROM memories WHERE namespace = 'core_identity' LIMIT 10",
            # Film production background
            "SELECT content FROM memories WHERE content ILIKE '%production%' OR content ILIKE '%film%' LIMIT 20",
            # Technical background
            "SELECT content FROM memories WHERE content ILIKE '%python%' OR content ILIKE '%AI%' OR content ILIKE '%docker%' LIMIT 20",
            # Leadership/management
            "SELECT content FROM memories WHERE content ILIKE '%department%' OR content ILIKE '%management%' LIMIT 10"
        ]

        background = {
            "core_identity": [],
            "production_experience": [],
            "technical_skills": [],
            "leadership": []
        }

        with conn.cursor() as cur:
            # Core identity
            cur.execute(queries[0])
            background["core_identity"] = [row[0] for row in cur.fetchall()]

            # Production
            cur.execute(queries[1])
            background["production_experience"] = [row[0] for row in cur.fetchall()]

            # Technical
            cur.execute(queries[2])
            background["technical_skills"] = [row[0] for row in cur.fetchall()]

            # Leadership
            cur.execute(queries[3])
            background["leadership"] = [row[0] for row in cur.fetchall()]

        conn.close()

        print("[Librarian] Retrieved candidate background from memory system")
        return background

    except Exception as e:
        print(f"[Librarian Error] {e}")
        return None


def generate_resume(job, background):
    """Generate custom resume for specific job using LLM"""
    try:
        # Build context from background
        context = f"""
CANDIDATE BACKGROUND:

Production Experience:
{chr(10).join(background.get('production_experience', [])[:5])}

Technical Skills:
{chr(10).join(background.get('technical_skills', [])[:5])}

Leadership Experience:
{chr(10).join(background.get('leadership', [])[:3])}

Core Strengths:
{chr(10).join(background.get('core_identity', [])[:2])}
"""

        # Job requirements
        job_description = f"""
JOB TITLE: {job['title']}
COMPANY: {job['company']}
LOCATION: {job['location']}

DESCRIPTION:
{job['description']}
"""

        # LLM prompt
        prompt = f"""You are a professional resume writer. Given the candidate's background and a job description, create a tailored resume that highlights relevant experience and skills matching the job requirements.

{context}

{job_description}

Write a concise, impactful resume (200-300 words) that:
1. Matches the job requirements with candidate's actual experience
2. Emphasizes relevant technical skills
3. Highlights leadership and production experience
4. Uses industry-standard language
5. Is truthful but optimally framed

RESUME:"""

        # Generate with qwen2.5
        response = ollama.generate(
            model=EXTRACTION_MODEL,
            prompt=prompt
        )

        resume_text = response['response']

        print(f"[Resume] Generated for {job['title']} at {job['company']}")

        return {
            "job_title": job['title'],
            "company": job['company'],
            "location": job['location'],
            "job_url": job['url'],
            "resume_text": resume_text,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        print(f"[Resume Error] {e}")
        return None


def generate_batch(jobs, background, output_dir="/tmp/wolf_hunt_resumes"):
    """Generate resumes for batch of jobs"""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("WOLF HUNT - Resume Generation Phase")
    print("=" * 60)
    print(f"Jobs to process: {len(jobs)}")
    print(f"Output directory: {output_dir}")
    print("=" * 60)

    resumes = []

    for i, job in enumerate(jobs):
        print(f"\n[{i+1}/{len(jobs)}] Processing: {job['title']} at {job['company']}")

        resume = generate_resume(job, background)

        if resume:
            resumes.append(resume)

            # Save individual resume
            filename = f"{output_dir}/{job['company'].replace(' ', '_')}_{job['title'].replace(' ', '_')}.txt"
            try:
                with open(filename, 'w') as f:
                    f.write(f"RESUME FOR: {resume['job_title']}\n")
                    f.write(f"COMPANY: {resume['company']}\n")
                    f.write(f"LOCATION: {resume['location']}\n")
                    f.write(f"JOB URL: {resume['job_url']}\n")
                    f.write("=" * 60 + "\n\n")
                    f.write(resume['resume_text'])

                print(f"  ✓ Saved: {filename}")

            except Exception as e:
                print(f"  ✗ Save error: {e}")

    # Save all resumes metadata
    try:
        with open(f"{output_dir}/all_resumes.json", 'w') as f:
            json.dump(resumes, f, indent=2)
        print(f"\n✓ Saved all resumes metadata: {output_dir}/all_resumes.json")
    except Exception as e:
        print(f"[Export Error] {e}")

    print("\n" + "=" * 60)
    print(f"PHASE 2 COMPLETE - {len(resumes)} resumes generated")
    print("=" * 60)

    return resumes


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Wolf Hunt Resume Generator')
    parser.add_argument('--job-file', type=str, required=True,
                       help='JSON file with job listings from coordinator')
    parser.add_argument('--output-dir', type=str, default='/tmp/wolf_hunt_resumes',
                       help='Output directory for resumes')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of resumes to generate (for testing)')

    args = parser.parse_args()

    # Load jobs
    try:
        with open(args.job_file, 'r') as f:
            jobs = json.load(f)
        print(f"✓ Loaded {len(jobs)} jobs from {args.job_file}")
    except Exception as e:
        print(f"[Error] Could not load jobs: {e}")
        return 1

    # Apply limit if specified
    if args.limit:
        jobs = jobs[:args.limit]
        print(f"[Limit] Processing first {args.limit} jobs only")

    # Get candidate background
    background = get_candidate_background()
    if not background:
        print("[Error] Could not retrieve candidate background")
        return 1

    # Generate resumes
    resumes = generate_batch(jobs, background, args.output_dir)

    print(f"\nResumes available in: {args.output_dir}/")

    return 0


if __name__ == "__main__":
    sys.exit(main())
