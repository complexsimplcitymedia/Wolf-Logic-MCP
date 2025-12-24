#!/usr/bin/env python3
"""Resume Generator - Orca2 Workers"""
import json
import psycopg2
import ollama
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

PG_CONFIG = {
    "host": "localhost",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

def get_candidate_background():
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        background = {"core_identity": [], "production_experience": [], "technical_skills": [], "leadership": []}
        with conn.cursor() as cur:
            cur.execute("SELECT content FROM memories WHERE namespace = 'core_identity' LIMIT 10")
            background["core_identity"] = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT content FROM memories WHERE content ILIKE '%production%' OR content ILIKE '%film%' LIMIT 20")
            background["production_experience"] = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT content FROM memories WHERE content ILIKE '%python%' OR content ILIKE '%AI%' OR content ILIKE '%docker%' LIMIT 20")
            background["technical_skills"] = [row[0] for row in cur.fetchall()]
            cur.execute("SELECT content FROM memories WHERE content ILIKE '%department%' OR content ILIKE '%management%' LIMIT 10")
            background["leadership"] = [row[0] for row in cur.fetchall()]
        conn.close()
        return background
    except Exception as e:
        print(f"[Error] {e}")
        return None

def generate_resume_worker(job, background, worker_id):
    try:
        context = f"""CANDIDATE BACKGROUND:
Production: {chr(10).join(background.get('production_experience', [])[:5])}
Technical: {chr(10).join(background.get('technical_skills', [])[:5])}
Leadership: {chr(10).join(background.get('leadership', [])[:3])}"""

        job_desc = f"""JOB: {job.get('title', 'N/A')}
COMPANY: {job.get('company', 'N/A')}
LOCATION: {job.get('location', 'N/A')}
DESCRIPTION: {job.get('description', '')[:1000]}"""

        prompt = f"""Write a professional ATS-optimized resume (250-350 words) for this job.
{context}
{job_desc}
Create a compelling resume highlighting relevant experience and skills. Use industry language. Be truthful but optimally framed.
RESUME:"""

        response = ollama.generate(model="orca2:latest", prompt=prompt)
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
        print(f"[Worker {worker_id}] ✗ {e}")
        return None

def generate_parallel(jobs, background, output_dir="/tmp/wolf_hunt_resumes_orca2"):
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    print(f"ORCA2 RESUME GENERATION - {len(jobs)} jobs, 9 workers")
    resumes = []
    with ThreadPoolExecutor(max_workers=9) as executor:
        futures = [executor.submit(generate_resume_worker, job, background, (i % 9) + 1) for i, job in enumerate(jobs)]
        for future in as_completed(futures):
            resume = future.result()
            if resume:
                resumes.append(resume)
                safe_company = resume['company'].replace(' ', '_').replace('/', '_')[:50]
                safe_title = resume['job_title'].replace(' ', '_').replace('/', '_')[:50]
                filename = f"{output_dir}/{safe_company}_{safe_title}.txt"
                try:
                    with open(filename, 'w') as f:
                        f.write(f"RESUME FOR: {resume['job_title']}\nCOMPANY: {resume['company']}\nLOCATION: {resume['location']}\nJOB URL: {resume['job_url']}\n{'='*60}\n\n{resume['resume_text']}")
                except Exception as e:
                    print(f"[Save Error] {e}")
    try:
        with open(f"{output_dir}/all_resumes.json", 'w') as f:
            json.dump(resumes, f, indent=2)
    except: pass
    print(f"COMPLETE - {len(resumes)} resumes")
    return resumes

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--job-file', required=True)
    parser.add_argument('--output-dir', default='/tmp/wolf_hunt_resumes_orca2')
    args = parser.parse_args()
    with open(args.job_file, 'r') as f:
        jobs = json.load(f)
    background = get_candidate_background()
    if background:
        generate_parallel(jobs, background, args.output_dir)
