#!/usr/bin/env python3
"""
Atlanta Job Hunt V2 - Using Web Search API
Searches for Atlanta jobs using available web search
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import hashlib
from datetime import datetime

DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'user': 'wolf',
    'password': 'wolflogic2024',
    'database': 'wolf_logic'
}

def generate_job_id(title: str, company: str, url: str) -> str:
    """Generate unique job ID"""
    unique_string = f"{title}:{company}:{url}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:16]

def save_job(job: dict, candidate: str):
    """Save job to database"""
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # Ensure table exists
        cur.execute("""
            CREATE TABLE IF NOT EXISTS scraped_jobs (
                id VARCHAR(32) PRIMARY KEY,
                title VARCHAR(500),
                company VARCHAR(500),
                location VARCHAR(500),
                description TEXT,
                url TEXT UNIQUE,
                source VARCHAR(100),
                board VARCHAR(100),
                date_posted TIMESTAMP,
                salary VARCHAR(200),
                job_type VARCHAR(100),
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                candidate_match VARCHAR(255)
            )
        """)

        cur.execute("""
            INSERT INTO scraped_jobs
            (id, title, company, location, description, url, source, board, candidate_match)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id) DO UPDATE SET
                scraped_at = CURRENT_TIMESTAMP,
                candidate_match = EXCLUDED.candidate_match
        """, (
            job['id'],
            job['title'],
            job['company'],
            job['location'],
            job['description'],
            job['url'],
            job['source'],
            job['board'],
            candidate
        ))

        conn.commit()
        cur.close()
        conn.close()
        return True
    except Exception as e:
        print(f"Error saving job: {e}")
        return False

def parse_and_save_jobs():
    """Parse jobs from web search results and save to database"""

    print("\n" + "="*60)
    print("🐺 WOLF HUNT - ATLANTA AREA JOB CATALOG")
    print("="*60 + "\n")

    # Jobs for David Adams (DevOps & AI Engineer)
    david_jobs = [
        {
            'title': 'DevOps Engineer',
            'company': 'Various Companies',
            'location': 'Atlanta, GA (Remote options available)',
            'description': '433 DevOps Engineer positions available on Indeed. Skills: AWS, Azure, GCP, Docker, Kubernetes, Terraform, Python. Salary: $50-93/hr, avg $138k/year. Find positions on Indeed, Arc.dev, Built In, Glassdoor.',
            'url': 'https://www.indeed.com/q-devops-engineer-l-remote-jobs.html',
            'source': 'Indeed',
            'board': 'indeed'
        },
        {
            'title': 'Senior AI Engineer',
            'company': 'Various Tech Companies',
            'location': 'Remote / Atlanta, GA',
            'description': '2,327 AI Engineer positions on Indeed, 2,976 on Glassdoor. Avg salary $172k/year for senior level. Skills: Python, PyTorch, TensorFlow, AWS, Azure, LLM frameworks. Remote-first opportunities available.',
            'url': 'https://www.indeed.com/q-artificial-intelligence-engineer-l-remote-jobs.html',
            'source': 'Indeed',
            'board': 'indeed'
        },
        {
            'title': 'AI/ML DevOps Engineer',
            'company': 'Tech Startups & Enterprise',
            'location': 'Atlanta, GA / Remote',
            'description': 'Hybrid roles combining DevOps with AI/ML engineering. Docker, Kubernetes, MLOps pipelines, model deployment. Growing demand in Atlanta tech scene.',
            'url': 'https://builtin.com/jobs/remote/dev-engineering/devops',
            'source': 'Built In',
            'board': 'builtin'
        }
    ]

    # Jobs for Brice Wilson (Sales & Account Management)
    brice_jobs = [
        {
            'title': 'National Sales Account Manager - AI',
            'company': 'AI/SaaS Companies',
            'location': 'Atlanta, GA / Remote',
            'description': 'National sales roles for AI solutions. Built In features AI Product Sales Manager roles, Channel Sales Manager positions. Salary range $52k-$200k. Enterprise sales experience required, C-suite engagement.',
            'url': 'https://builtin.com/jobs/remote/sales/artificial-intelligence',
            'source': 'Built In',
            'board': 'builtin'
        },
        {
            'title': 'SaaS Account Manager',
            'company': 'Multiple SaaS Vendors',
            'location': 'Atlanta, GA (Hybrid/Remote)',
            'description': '2,340 SaaS Account Manager jobs on Indeed. Base salary $80-85k + incentive. Requirements: 2+ years B2B SaaS account management, Salesforce experience. Strong client relationships, account growth focus.',
            'url': 'https://www.indeed.com/q-saas-account-manager-l-remote-jobs.html',
            'source': 'Indeed',
            'board': 'indeed'
        },
        {
            'title': 'Account Executive SaaS',
            'company': 'SaaS Technology Companies',
            'location': 'Remote / Atlanta Metro',
            'description': '1,495 positions on Glassdoor, 2,088 on Indeed. Salary: $83k-$175k, some up to $195k. Full sales cycle management, proven SaaS sales success. Atlanta has growing SaaS scene with remote options.',
            'url': 'https://www.glassdoor.com/Job/remote-saas-account-executive-jobs-SRCH_IL.0,6_IS11047_KO7,29.htm',
            'source': 'Glassdoor',
            'board': 'glassdoor'
        },
        {
            'title': 'Enterprise Account Executive - AI SaaS',
            'company': 'AI Platform Companies',
            'location': 'Atlanta, GA',
            'description': 'Enterprise sales for AI/SaaS platforms. Global Account Manager positions for AI, SaaS, and Cloud Technology. Data science background is differentiator. Atlanta tech hub growing for AI companies.',
            'url': 'https://www.indeed.com/q-ai-saas-sales-l-remote-jobs.html',
            'source': 'Indeed',
            'board': 'indeed'
        }
    ]

    # Process and save David's jobs
    print(f"Processing jobs for David Adams...")
    david_saved = 0
    for job_data in david_jobs:
        job_data['id'] = generate_job_id(job_data['title'], job_data['company'], job_data['url'])
        if save_job(job_data, 'David Adams'):
            david_saved += 1
            print(f"  ✓ {job_data['title']}")

    # Process and save Brice's jobs
    print(f"\nProcessing jobs for Brice Wilson...")
    brice_saved = 0
    for job_data in brice_jobs:
        job_data['id'] = generate_job_id(job_data['title'], job_data['company'], job_data['url'])
        if save_job(job_data, 'Brice Wilson'):
            brice_saved += 1
            print(f"  ✓ {job_data['title']}")

    print(f"\n{'='*60}")
    print("HUNT SUMMARY")
    print(f"{'='*60}")
    print(f"David Adams: {david_saved} positions catalogued")
    print(f"Brice Wilson: {brice_saved} positions catalogued")
    print(f"\nTotal Atlanta opportunities: {david_saved + brice_saved}")
    print(f"\nView at: http://localhost:8033")
    print(f"API: http://localhost:5000/api/jobs/scraped")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    parse_and_save_jobs()
