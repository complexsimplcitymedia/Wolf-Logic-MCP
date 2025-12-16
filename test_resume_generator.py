#!/usr/bin/env python3
"""
Test suite for Resume Generation Engine
Tests all major components and generates sample resumes
"""

import os
import sys
import json
from pathlib import Path

# Add parent to path
sys.path.insert(0, '/mnt/Wolf-code/Wolf-Ai-Enterptises')

from resume_generator import (
    JobPostingParser,
    SkillMatcher,
    ResumeBuilder,
    ResumeGenerationEngine,
    PgaiDB,
    safe_print
)

# Sample job postings for testing
SAMPLE_JOB_POSTINGS = {
    'python_backend': """
POSITION: Senior Python Backend Engineer

COMPANY: TechVision Solutions Inc.

Job Title: Senior Backend Engineer - Python

ABOUT US:
TechVision Solutions is a leading cloud-native software company with 200+ employees.
We build scalable, high-performance systems for enterprise clients worldwide.

REQUIREMENTS:
We are seeking a Senior Python Backend Engineer with 5+ years of professional experience.

Required Skills:
- Python (advanced proficiency)
- PostgreSQL and NoSQL database design
- Django or FastAPI experience
- REST API design and implementation
- Docker containerization
- AWS cloud platform (EC2, RDS, S3)
- Git version control
- Linux/Unix systems
- Microservices architecture understanding

Technical Stack:
- Python 3.9+
- FastAPI/Django
- PostgreSQL, MongoDB, Redis
- Docker, Docker Compose
- Kubernetes (nice to have)
- AWS services

Responsibilities:
- Design and implement scalable backend services
- Optimize database queries and system performance
- Mentor junior developers
- Participate in code reviews
- Collaborate with frontend teams

Nice to have:
- Kubernetes experience
- CI/CD pipeline development
- GraphQL implementation
- Cloud architecture certification
- Open source contributions
    """,

    'frontend_react': """
POSITION: Frontend Engineer - React

Company: Digital Innovations Ltd

Job Title: Senior Frontend Engineer

REQUIREMENTS:
5+ years frontend development experience

Must Have Skills:
- React (advanced)
- JavaScript/TypeScript
- CSS, HTML5
- State management (Redux, Context API)
- RESTful APIs
- Git
- Testing frameworks (Jest, React Testing Library)
- Responsive design
- Web performance optimization

Technology Stack:
- React 18+
- TypeScript
- Next.js
- Tailwind CSS
- Jest & React Testing Library
- Webpack/Vite

Responsibilities:
- Build responsive user interfaces
- Implement complex features
- Optimize performance
- Maintain code quality
- Collaborate with designers and backend engineers

Nice to Have:
- Next.js experience
- GraphQL
- Web accessibility (WCAG)
- SEO optimization
- Figma design tool knowledge
    """,

    'devops': """
POSITION: DevOps Engineer

Company: Cloud Systems Corp

Job Requirements:

Years Required: 3+ years

Core Skills:
- Docker & Kubernetes orchestration
- AWS or Azure cloud platforms
- CI/CD pipelines (Jenkins, GitHub Actions, GitLab CI)
- Infrastructure as Code (Terraform, CloudFormation)
- Linux system administration
- Python or Bash scripting
- PostgreSQL/MySQL administration
- Monitoring and logging (Prometheus, ELK Stack)
- Git version control

Technology Requirements:
- Kubernetes management
- Docker containerization
- AWS EC2, RDS, S3, CloudFormation
- Jenkins or GitLab CI
- Terraform
- ELK Stack or Prometheus

Responsibilities:
- Manage and maintain Kubernetes clusters
- Build CI/CD pipelines
- Monitor system performance
- Implement infrastructure automation
- Troubleshoot infrastructure issues
- Support development teams

Preferred:
- Terraform expertise
- Kubernetes cluster administration
- AWS certification
- Ansible experience
- Helm charts experience
    """
}


def test_job_posting_parser():
    """Test job posting parsing"""
    safe_print("\n" + "="*70)
    safe_print("TEST: Job Posting Parser")
    safe_print("="*70)

    for job_name, posting in SAMPLE_JOB_POSTINGS.items():
        safe_print(f"\nParsing: {job_name}")
        safe_print("-" * 70)

        parser = JobPostingParser(posting)
        analysis = parser.parse()

        safe_print(f"  Job Title: {analysis.get('job_title', 'N/A')}")
        safe_print(f"  Company: {analysis.get('company', 'N/A')}")
        safe_print(f"  Years Required: {analysis.get('years_experience', 'N/A')}")
        safe_print(f"  Required Skills ({len(analysis.get('required_skills', []))}): {', '.join(analysis.get('required_skills', [])[:5])}")
        safe_print(f"  Key Technologies: {', '.join(analysis.get('key_technologies', []))}")
        safe_print(f"  Responsibilities: {len(analysis.get('responsibilities', []))} found")
        safe_print(f"  Nice to Have: {len(analysis.get('nice_to_have', []))} found")


def test_database_connection():
    """Test PostgreSQL connection"""
    safe_print("\n" + "="*70)
    safe_print("TEST: Database Connection")
    safe_print("="*70)

    db = PgaiDB({
        "host": "100.110.82.181",
        "port": 5433,
        "database": "wolf_logic",
        "user": "wolf",
        "password": "wolflogic2024"
    })

    try:
        db.connect()
        safe_print("  Connected to pgai database")

        # Test table creation
        db.create_resume_table()
        safe_print("  Resume tracking table ready")

        # Test memory queries
        safe_print("\n  Testing memory queries...")
        memories = db.query_memories("Python programming", limit=3)
        safe_print(f"  Found {len(memories)} memories matching 'Python programming'")

        db.close()
        return True

    except Exception as e:
        safe_print(f"  ERROR: {e}")
        return False


def test_resume_generation():
    """Test complete resume generation"""
    safe_print("\n" + "="*70)
    safe_print("TEST: Resume Generation Pipeline")
    safe_print("="*70)

    output_dir = "/tmp/resume_tests"
    Path(output_dir).mkdir(exist_ok=True)

    engine = ResumeGenerationEngine()

    results = engine.generate(
        job_posting_text=SAMPLE_JOB_POSTINGS['python_backend'],
        output_dir=output_dir,
        company_name="TechVision Solutions"
    )

    safe_print("\n" + "-"*70)
    safe_print("RESULTS:")
    safe_print(f"  Success: {results['success']}")
    safe_print(f"  Resume ID: {results.get('resume_id', 'N/A')}")
    safe_print(f"  Skills Matched: {len(results.get('matched_skills', []))}")
    safe_print(f"  Output Files:")
    for fmt, path in results.get('output_files', {}).items():
        if os.path.exists(path):
            size = os.path.getsize(path) / 1024
            safe_print(f"    - {fmt.upper()}: {path} ({size:.1f} KB)")

    engine.cleanup()

    return results['success']


def test_all_sample_jobs():
    """Generate resumes for all sample job postings"""
    safe_print("\n" + "="*70)
    safe_print("TEST: Generate Resumes for All Sample Jobs")
    safe_print("="*70)

    output_dir = "/tmp/resume_tests/all_jobs"
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    engine = ResumeGenerationEngine()
    results_summary = {}

    for job_name, posting in SAMPLE_JOB_POSTINGS.items():
        safe_print(f"\n[{job_name.upper()}]")

        results = engine.generate(
            job_posting_text=posting,
            output_dir=output_dir,
            company_name=job_name.replace('_', ' ').title()
        )

        results_summary[job_name] = {
            'success': results['success'],
            'files': results.get('output_files', {}),
            'skills': len(results.get('matched_skills', []))
        }

    engine.cleanup()

    # Print summary
    safe_print("\n" + "="*70)
    safe_print("GENERATION SUMMARY")
    safe_print("="*70)

    for job_name, summary in results_summary.items():
        safe_print(f"\n{job_name.upper()}:")
        safe_print(f"  Success: {summary['success']}")
        safe_print(f"  Skills: {summary['skills']}")
        safe_print(f"  Files: {len(summary['files'])}")


def test_memory_queries():
    """Test pgai memory queries"""
    safe_print("\n" + "="*70)
    safe_print("TEST: Memory Queries")
    safe_print("="*70)

    engine = ResumeGenerationEngine()

    queries = [
        "Python programming experience",
        "AWS cloud platform",
        "React frontend development",
        "Docker containerization",
        "database design",
    ]

    for query in queries:
        safe_print(f"\nQuery: '{query}'")
        results = engine.list_memories_for_query(query, limit=3)
        safe_print(f"  Results: {len(results)}")

    engine.cleanup()


def run_all_tests():
    """Run all tests"""
    safe_print("\n\n")
    safe_print("╔" + "="*68 + "╗")
    safe_print("║" + " "*15 + "RESUME GENERATOR TEST SUITE" + " "*25 + "║")
    safe_print("╚" + "="*68 + "╝")

    tests = [
        ("Job Posting Parser", test_job_posting_parser),
        ("Database Connection", test_database_connection),
        ("Resume Generation", test_resume_generation),
        ("Memory Queries", test_memory_queries),
        ("Batch Generation", test_all_sample_jobs),
    ]

    results = {}

    for test_name, test_func in tests:
        try:
            safe_print(f"\n\nRunning: {test_name}")
            test_func()
            results[test_name] = "PASS"
        except Exception as e:
            safe_print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()
            results[test_name] = "FAIL"

    # Summary
    safe_print("\n\n" + "="*70)
    safe_print("TEST SUMMARY")
    safe_print("="*70)

    for test_name, status in results.items():
        status_symbol = "✓" if status == "PASS" else "✗"
        safe_print(f"  {status_symbol} {test_name}: {status}")

    passed = sum(1 for s in results.values() if s == "PASS")
    total = len(results)

    safe_print(f"\nTotal: {passed}/{total} tests passed")

    return all(s == "PASS" for s in results.values())


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
