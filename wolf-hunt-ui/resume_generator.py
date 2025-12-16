#!/usr/bin/env python3
"""
Resume Generator
Uses Orca/Mistral to generate ATS-optimized resumes tailored to specific job postings
"""

import subprocess
import json
from typing import Dict
import psycopg2
from psycopg2.extras import RealDictCursor

DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'user': 'wolf',
    'password': 'wolflogic2024',
    'database': 'wolf_logic'
}

def get_candidate_profile(candidate_name: str) -> Dict:
    """Get candidate profile from database"""
    conn = psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidates WHERE name = %s", (candidate_name,))
    candidate = cur.fetchone()
    cur.close()
    conn.close()
    return dict(candidate) if candidate else None

def generate_resume_with_llm(candidate: Dict, job_title: str, job_description: str = "") -> str:
    """Generate resume using local LLM"""

    prompt = f"""You are an expert ATS resume writer. Generate a professional summary paragraph for:

Candidate: {candidate['name']}
Target Position: {job_title}
Experience: {candidate['experience_years']} years
Skills: {', '.join(candidate['skills'])}
Location: {candidate['location']}

Job Description Context:
{job_description[:500] if job_description else 'General application'}

Requirements:
1. Write a compelling 3-sentence professional summary
2. Emphasize relevant experience for {job_title}
3. Include key ATS keywords from the job description
4. Highlight quantifiable achievements where possible
5. Match the tone to the target role

Output ONLY the professional summary paragraph, no preamble or explanation."""

    try:
        # Use Mistral Small for better quality
        result = subprocess.run(
            ['ollama', 'run', 'mistral-small'],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=60
        )

        if result.returncode == 0:
            return result.stdout.strip()
        else:
            # Fallback to Orca
            result = subprocess.run(
                ['ollama', 'run', 'orca2'],
                input=prompt,
                capture_output=True,
                text=True,
                timeout=60
            )
            return result.stdout.strip() if result.returncode == 0 else "Error generating resume"

    except Exception as e:
        return f"Error: {str(e)}"

def generate_resume(candidate_name: str, job_title: str, job_description: str = "") -> Dict:
    """
    Generate tailored resume for candidate and job

    Args:
        candidate_name: Name of candidate from database
        job_title: Target job title
        job_description: Optional job description for context

    Returns:
        Dict with generated resume sections
    """

    print(f"\n{'='*60}")
    print(f"🐺 WOLF HUNT - RESUME GENERATOR")
    print(f"{'='*60}\n")
    print(f"Candidate: {candidate_name}")
    print(f"Target Position: {job_title}")
    print(f"\nGenerating ATS-optimized resume...\n")

    # Get candidate profile
    candidate = get_candidate_profile(candidate_name)
    if not candidate:
        return {'error': f'Candidate {candidate_name} not found'}

    # Generate professional summary
    print("  🔄 Generating professional summary with Mistral...")
    summary = generate_resume_with_llm(candidate, job_title, job_description)

    # Build resume dict
    resume = {
        'candidate_name': candidate['name'],
        'contact': {
            'email': candidate['email'],
            'phone': candidate['phone'],
            'location': candidate['location']
        },
        'target_job': job_title,
        'professional_summary': summary,
        'skills': candidate['skills'],
        'experience_years': candidate['experience_years'],
        'target_roles': candidate['target_roles'],
        'resume_path': candidate['resume_path'],
        'generated_at': 'now()'
    }

    print(f"\n{'='*60}")
    print("GENERATED PROFESSIONAL SUMMARY")
    print(f"{'='*60}\n")
    print(summary)
    print(f"\n{'='*60}\n")

    return resume

def test_generator():
    """Test resume generator for both candidates"""

    # Test for Brice Wilson
    print("\nTesting for Brice Wilson...")
    brice_resume = generate_resume(
        'Brice Wilson',
        'National Sales Account Manager - AI',
        'Looking for experienced sales leader with AI/SaaS background. Must have C-suite engagement experience and track record of territory growth.'
    )

    print("\n\nTesting for David Adams...")
    david_resume = generate_resume(
        'David Adams',
        'Senior AI Engineer',
        'Seeking senior AI engineer with experience in LLMs, Docker, and production ML systems. Linux and DevOps experience a plus.'
    )

    return {'brice': brice_resume, 'david': david_resume}

if __name__ == '__main__':
    test_generator()
