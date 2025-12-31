#!/usr/bin/env python3
"""
Resume Generator - Practical Usage Examples
Demonstrates real-world use cases and integration patterns
"""

import os
import sys
from pathlib import Path
from resume_generator import ResumeGenerationEngine
import json

def example_1_basic_generation():
    """Example 1: Generate single resume from job posting"""
    print("\n" + "="*70)
    print("EXAMPLE 1: Basic Resume Generation")
    print("="*70)

    job_posting = """
    POSITION: Senior Python Backend Engineer

    Company: TechCorp Inc

    Requirements:
    - 5+ years Python experience
    - FastAPI or Django
    - PostgreSQL expertise
    - REST API design
    - Docker and Kubernetes
    - AWS cloud services
    - Git version control

    This is a remote-friendly role with flexible hours.
    """

    engine = ResumeGenerationEngine()

    results = engine.generate(
        job_posting_text=job_posting,
        output_dir="/tmp/example1_resumes",
        company_name="TechCorp Inc"
    )

    print(f"\n✓ Generated: {results['resume_id']}")
    print(f"✓ Location: {results['output_files']['docx']}")
    print(f"✓ Matched Skills: {', '.join(results['matched_skills'][:5])}")

    engine.cleanup()


def example_2_batch_generation():
    """Example 2: Generate resumes for multiple job postings"""
    print("\n" + "="*70)
    print("EXAMPLE 2: Batch Generation from Multiple Postings")
    print("="*70)

    jobs = {
        "python_backend": {
            "company": "TechCorp Inc",
            "posting": "Senior Python Engineer, 5+ years, FastAPI, PostgreSQL, AWS"
        },
        "react_frontend": {
            "company": "DigitalVision Inc",
            "posting": "Frontend Engineer, React, TypeScript, 4+ years, Next.js, Tailwind"
        },
        "devops": {
            "company": "CloudSystems Inc",
            "posting": "DevOps Engineer, Kubernetes, Docker, AWS, Terraform, 3+ years"
        }
    }

    engine = ResumeGenerationEngine()
    output_dir = "/tmp/example2_batch"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    results_summary = {}

    for job_id, job_data in jobs.items():
        print(f"\nGenerating for: {job_data['company']}")

        results = engine.generate(
            job_posting_text=job_data['posting'],
            output_dir=output_dir,
            company_name=job_data['company']
        )

        results_summary[job_data['company']] = {
            'resume_id': results['resume_id'],
            'skills': results['matched_skills'][:5],
            'success': results['success']
        }

        if results['success']:
            print(f"  ✓ {results['resume_id']}")

    print("\n" + "-"*70)
    print("BATCH SUMMARY:")
    for company, summary in results_summary.items():
        print(f"  {company}: {summary['resume_id']}")
        print(f"    Skills: {', '.join(summary['skills'])}")

    engine.cleanup()


def example_3_from_file():
    """Example 3: Generate resume from job posting file"""
    print("\n" + "="*70)
    print("EXAMPLE 3: Generate from Job Posting File")
    print("="*70)

    # Create sample job posting file
    job_file = "/tmp/job_posting.txt"

    with open(job_file, 'w') as f:
        f.write("""
Full Stack Engineer - Remote

Company: InnovateTech Solutions
Location: Remote (worldwide)

About us:
InnovateTech is a Series B startup building AI-powered development tools.

Requirements:
- 5+ years full stack development experience
- JavaScript/TypeScript (React, Next.js)
- Python (FastAPI preferred) or Node.js backend
- PostgreSQL and MongoDB experience
- Docker and Docker Compose
- AWS or GCP experience
- Git and GitHub
- Strong communication skills

Nice to have:
- Kubernetes experience
- GraphQL
- Microservices architecture
- DevOps experience
- Open source contributions

Responsibilities:
- Build and maintain full stack features
- Optimize performance
- Mentor junior developers
- Participate in code reviews
        """)

    print(f"Created job posting file: {job_file}")

    engine = ResumeGenerationEngine()

    # Generate from file
    with open(job_file, 'r') as f:
        job_posting = f.read()

    results = engine.generate(
        job_posting_text=job_posting,
        output_dir="/tmp/example3_fromfile",
        company_name="InnovateTech Solutions"
    )

    print(f"\n✓ Resume ID: {results['resume_id']}")
    print(f"✓ Files generated:")
    for fmt, path in results['output_files'].items():
        print(f"  - {fmt.upper()}: {path}")

    engine.cleanup()


def example_4_track_applications():
    """Example 4: Track resume applications in pgai"""
    print("\n" + "="*70)
    print("EXAMPLE 4: Track Sent Applications")
    print("="*70)

    engine = ResumeGenerationEngine()

    # First, generate a resume
    results = engine.generate(
        job_posting_text="Senior Python Engineer, 5+ years, Django, PostgreSQL",
        output_dir="/tmp/example4_tracking",
        company_name="TechCorp Inc"
    )

    resume_id = results['resume_id']
    print(f"\nGenerated: {resume_id}")

    # Track it
    engine.track_application("TechCorp Inc", "job_123", resume_id)
    print(f"✓ Tracked application")

    # Query to verify
    import psycopg2
    from psycopg2.extras import RealDictCursor

    conn = psycopg2.connect(
        host="localhost", port=5433, database="wolf_logic",
        user="wolf", password="wolflogic2024"
    )
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT company_name, job_title, resume_id, created_at
        FROM resume_applications
        WHERE resume_id = %s
    """, (resume_id,))

    row = cur.fetchone()

    if row:
        print(f"\nTracking Record:")
        print(f"  Company: {row['company_name']}")
        print(f"  Job: {row['job_title']}")
        print(f"  Resume ID: {row['resume_id']}")
        print(f"  Created: {row['created_at']}")

    cur.close()
    conn.close()
    engine.cleanup()


def example_5_analyze_skills():
    """Example 5: Analyze matched skills from generation"""
    print("\n" + "="*70)
    print("EXAMPLE 5: Analyze Matched Skills")
    print("="*70)

    engine = ResumeGenerationEngine()

    job_posting = """
    Lead Backend Engineer

    Requirements:
    - 7+ years backend development
    - Python or Go
    - Microservices architecture
    - Docker and Kubernetes
    - PostgreSQL optimization
    - AWS (EC2, RDS, S3, Lambda)
    - CI/CD pipelines
    - gRPC and Protobuf
    - Message queues (RabbitMQ, Kafka)
    """

    results = engine.generate(
        job_posting_text=job_posting,
        output_dir="/tmp/example5_analysis",
        company_name="AdvancedTech Corp"
    )

    print(f"\nGenerated Resume: {results['resume_id']}")
    print(f"\nMatched Skills Analysis:")
    print(f"Total matched: {len(results['matched_skills'])}")

    # Group skills by category
    categories = {
        'Languages': ['Python', 'Go', 'Java', 'Rust'],
        'Cloud': ['AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes'],
        'Databases': ['PostgreSQL', 'MongoDB', 'Redis', 'Cassandra'],
        'Architecture': ['Microservices', 'Architecture', 'Design', 'Patterns'],
        'Tools': ['Docker', 'Kubernetes', 'CI/CD', 'Jenkins', 'Git'],
    }

    matched_by_category = {cat: [] for cat in categories.keys()}

    for skill in results['matched_skills']:
        for category, keywords in categories.items():
            if any(kw.lower() in skill.lower() for kw in keywords):
                matched_by_category[category].append(skill)
                break

    for category, skills in matched_by_category.items():
        if skills:
            unique = list(set(skills))
            print(f"\n{category} ({len(unique)}):")
            for skill in unique[:5]:
                print(f"  • {skill}")

    engine.cleanup()


def example_6_query_memories():
    """Example 6: Query pgai memories for debugging"""
    print("\n" + "="*70)
    print("EXAMPLE 6: Query Available Memories")
    print("="*70)

    engine = ResumeGenerationEngine()

    queries = [
        "Python FastAPI backend",
        "AWS cloud services",
        "React TypeScript frontend",
        "Kubernetes DevOps",
    ]

    print("\nSearching available experiences in pgai:")
    print("-"*70)

    for query in queries:
        memories = engine.pgai.query_memories(query, limit=2)
        print(f"\nQuery: '{query}'")
        print(f"Found: {len(memories)} memories")

        if memories:
            for i, mem in enumerate(memories[:1], 1):
                content_preview = mem.get('content', '')[:100]
                print(f"  [{i}] {content_preview}...")

    engine.cleanup()


def example_7_integration_pattern():
    """Example 7: Integration pattern for automated job applications"""
    print("\n" + "="*70)
    print("EXAMPLE 7: Integration Pattern - Auto-Apply Pipeline")
    print("="*70)

    # Simulate job feed from API
    job_feed = [
        {
            "id": "job_001",
            "title": "Senior Python Engineer",
            "company": "TechCorp Inc",
            "description": "5+ years Python, FastAPI, PostgreSQL, AWS",
            "apply_url": "https://techcorp.com/apply/job_001"
        },
        {
            "id": "job_002",
            "title": "Backend Developer",
            "company": "DataFlow Systems",
            "description": "Python, Django, database optimization, 4+ years",
            "apply_url": "https://dataflow.com/apply/job_002"
        },
    ]

    engine = ResumeGenerationEngine()
    output_dir = "/tmp/example7_auto_apply"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    print(f"\nProcessing {len(job_feed)} job postings...\n")

    applied_count = 0

    for job in job_feed:
        print(f"Processing: {job['title']} at {job['company']}")

        # Generate resume
        results = engine.generate(
            job_posting_text=job['description'],
            output_dir=output_dir,
            company_name=job['company']
        )

        if results['success']:
            resume_path = results['output_files'].get('docx')

            print(f"  ✓ Resume generated: {results['resume_id']}")
            print(f"  ✓ Would apply to: {job['apply_url']}")

            # In real implementation, would upload to job site
            # apply_to_job(job['apply_url'], resume_path)

            # Track it
            engine.track_application(job['company'], job['id'], results['resume_id'])
            applied_count += 1
        else:
            print(f"  ✗ Generation failed")

    print(f"\n{applied_count}/{len(job_feed)} applications prepared")

    engine.cleanup()


def main():
    """Run all examples"""
    print("\n")
    print("╔" + "="*68 + "╗")
    print("║" + " "*10 + "RESUME GENERATOR - PRACTICAL USAGE EXAMPLES" + " "*14 + "║")
    print("╚" + "="*68 + "╝")

    examples = [
        ("Basic Resume Generation", example_1_basic_generation),
        ("Batch Generation", example_2_batch_generation),
        ("From File", example_3_from_file),
        ("Track Applications", example_4_track_applications),
        ("Analyze Skills", example_5_analyze_skills),
        ("Query Memories", example_6_query_memories),
        ("Integration Pattern", example_7_integration_pattern),
    ]

    for example_name, example_func in examples:
        try:
            example_func()
        except Exception as e:
            print(f"\n✗ Error in {example_name}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*70)
    print("ALL EXAMPLES COMPLETED")
    print("="*70)
    print("\nNext steps:")
    print("  1. Check output files in /tmp/example*_* directories")
    print("  2. Query pgai to see tracked applications")
    print("  3. Customize user profile in resume_generator.py")
    print("  4. Integrate with your job board API")


if __name__ == '__main__':
    main()
