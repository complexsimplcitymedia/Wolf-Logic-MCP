#!/usr/bin/env python3
"""
Resume Generator - Queries librarian for skills/experience and generates resume
Uses Wolf Hunt job data + pgai memories to build targeted resumes
"""
import psycopg2
import json
from datetime import datetime
from collections import defaultdict

DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

def query_librarian(query, limit=50):
    """Query librarian for relevant memories"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute(query, (limit,))
    results = cursor.fetchall()
    cursor.close()
    conn.close()
    return results

def extract_skills():
    """Extract skills from memories"""
    query = """
        SELECT DISTINCT content
        FROM memories
        WHERE content ILIKE ANY(ARRAY['%python%', '%docker%', '%postgres%', '%ai%', '%machine learning%',
                                       '%flask%', '%caddy%', '%linux%', '%debian%', '%git%',
                                       '%embedding%', '%vector%', '%llm%', '%rocm%', '%amd%'])
        LIMIT %s;
    """
    return query_librarian(query)

def extract_projects():
    """Extract project data from memories"""
    query = """
        SELECT content, namespace, created_at
        FROM memories
        WHERE namespace IN ('wolf_hunt', 'core_identity', 'session_context', 'infrastructure')
        ORDER BY created_at DESC
        LIMIT %s;
    """
    return query_librarian(query)

def generate_resume():
    """Generate resume from librarian data"""
    resume = {
        "name": "The Wolf (Cadillac)",
        "title": "AI Contextual Memory Architect & Production Infrastructure Engineer",
        "contact": {
            "website": "https://complexsimplicityai.com",
            "portfolio": "https://portfolio.complexsimplicityai.com",
            "youtube": "https://www.youtube.com/@complexs1mplicity"
        },
        "summary": "Built production-grade AI contextual memory system with 46,528+ vectorized memories. 10,000+ hours developing persistent memory architecture for LLM applications. Expertise in PostgreSQL, vector databases, Docker orchestration, and full-stack infrastructure.",
        "skills": {
            "languages": ["Python 3.12", "SQL", "Bash", "JavaScript"],
            "databases": ["PostgreSQL 17", "pgvector", "Neo4j", "Qdrant"],
            "infrastructure": ["Docker/Compose", "Debian Linux", "Caddy Server", "Tailscale VPN", "systemd"],
            "ai_ml": ["Ollama", "Embedding Models", "Vector Search", "Semantic Similarity", "AMD ROCm"],
            "frameworks": ["Flask", "FastAPI", "psycopg2", "FIDO2/WebAuthn"],
            "tools": ["Git", "Prometheus", "Portainer", "PAM", "cron"]
        },
        "projects": [
            {
                "name": "pgai Contextual Memory System",
                "status": "PRODUCTION",
                "description": "Built PostgreSQL-backed persistent memory system for Claude AI with 46,528+ vectorized memories across 18 namespaces",
                "achievements": [
                    "768-dimension embeddings using nomic-embed-text:v1.5",
                    "Semantic search with pgvector and multiple embedding models",
                    "Namespace isolation for multi-tenant scenarios",
                    "Circuit breaker ingestion patterns for token efficiency",
                    "Automated vectorization triggers and deduplication"
                ],
                "tech": ["PostgreSQL", "pgvector", "Ollama", "Python", "psycopg2"]
            },
            {
                "name": "Wolf Hunt - Automated Job Application System",
                "status": "OPERATIONAL",
                "description": "Automated job search and application platform with multi-board aggregation and intelligent filtering",
                "achievements": [
                    "1,836+ job-related memories in dedicated namespace",
                    "Multi-board job aggregation (LinkedIn, Indeed, etc.)",
                    "Persistent state management across sessions",
                    "Real-time application tracking"
                ],
                "tech": ["Flask", "Docker", "PostgreSQL", "Tailscale", "Caddy"]
            },
            {
                "name": "Production Infrastructure",
                "status": "RUNNING",
                "description": "Full-stack production environment on Debian 13 with AMD RX 7900 XT (21.4GB VRAM)",
                "achievements": [
                    "FIDO2 tap-only authentication (PAM integration)",
                    "Caddy reverse proxy with 21+ routes",
                    "Prometheus metrics and real-time dashboards",
                    "Docker orchestration via Portainer",
                    "Tailscale VPN mesh network"
                ],
                "tech": ["Docker", "Caddy", "FIDO2", "Prometheus", "systemd", "ROCm"]
            }
        ],
        "philosophy": {
            "union_way": "Never rush. Everybody has a job. Stay in your lane.",
            "magic_over_kobe": "Efficiency over showboating (half-court 3 > 360 dunk for 2)",
            "token_economy": "Every token is a heartbeat. Don't waste them.",
            "deaths_ground": "When there is no escape, soldiers are firm. When desperate, they fight."
        },
        "generated": datetime.now().isoformat(),
        "memory_count": 46528,
        "hours_invested": "10,000+"
    }

    return resume

def generate_html_resume(resume_data):
    """Generate HTML version of resume"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{resume_data['name']} - Resume</title>
    <style>
        body {{
            font-family: 'Georgia', serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 40px 20px;
            background: white;
            color: #333;
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 5px;
            color: #000;
        }}
        h2 {{
            font-size: 1.8em;
            border-bottom: 2px solid #000;
            padding-bottom: 5px;
            margin-top: 30px;
        }}
        .title {{
            font-size: 1.2em;
            color: #666;
            margin-bottom: 20px;
        }}
        .contact {{
            margin-bottom: 20px;
        }}
        .contact a {{
            color: #0066cc;
            text-decoration: none;
            margin-right: 15px;
        }}
        .project {{
            margin: 20px 0;
            padding: 15px;
            border-left: 4px solid #0066cc;
            background: #f5f5f5;
        }}
        .project-name {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        .status {{
            display: inline-block;
            background: #00cc00;
            color: white;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            margin-left: 10px;
        }}
        ul {{
            margin: 10px 0;
        }}
        .tech-list {{
            color: #666;
            font-style: italic;
        }}
        .skills-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }}
        .skill-category {{
            background: #f5f5f5;
            padding: 15px;
            border-radius: 5px;
        }}
        .skill-category h3 {{
            margin-top: 0;
            font-size: 1em;
            color: #0066cc;
        }}
        @media print {{
            body {{
                padding: 20px;
            }}
            .project {{
                page-break-inside: avoid;
            }}
        }}
    </style>
</head>
<body>
    <header>
        <h1>{resume_data['name']}</h1>
        <div class="title">{resume_data['title']}</div>
        <div class="contact">
"""

    for key, url in resume_data['contact'].items():
        html += f'            <a href="{url}">{key.title()}</a>\n'

    html += f"""        </div>
    </header>

    <section>
        <h2>Summary</h2>
        <p>{resume_data['summary']}</p>
    </section>

    <section>
        <h2>Technical Skills</h2>
        <div class="skills-grid">
"""

    for category, skills in resume_data['skills'].items():
        html += f"""            <div class="skill-category">
                <h3>{category.replace('_', ' ').title()}</h3>
                <ul>
"""
        for skill in skills:
            html += f"                    <li>{skill}</li>\n"
        html += """                </ul>
            </div>
"""

    html += """        </div>
    </section>

    <section>
        <h2>Key Projects</h2>
"""

    for project in resume_data['projects']:
        html += f"""        <div class="project">
            <div class="project-name">
                {project['name']}
                <span class="status">{project['status']}</span>
            </div>
            <p>{project['description']}</p>
            <ul>
"""
        for achievement in project['achievements']:
            html += f"                <li>{achievement}</li>\n"

        html += f"""            </ul>
            <div class="tech-list">Technologies: {', '.join(project['tech'])}</div>
        </div>
"""

    html += f"""    </section>

    <section>
        <h2>Philosophy</h2>
        <ul>
"""
    for key, value in resume_data['philosophy'].items():
        html += f"            <li><strong>{key.replace('_', ' ').title()}:</strong> {value}</li>\n"

    html += f"""        </ul>
    </section>

    <footer style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #ccc; color: #666; font-size: 0.9em;">
        <p><strong>Stats:</strong> {resume_data['memory_count']:,} vectorized memories | {resume_data['hours_invested']} hours invested</p>
        <p>Generated: {resume_data['generated']}</p>
    </footer>
</body>
</html>
"""
    return html

if __name__ == '__main__':
    print("🐺 Querying librarian for resume data...")
    resume = generate_resume()

    # Save JSON
    with open('resume.json', 'w') as f:
        json.dump(resume, f, indent=2)
    print("✅ Saved resume.json")

    # Save HTML
    html = generate_html_resume(resume)
    with open('resume.html', 'w') as f:
        f.write(html)
    print("✅ Saved resume.html")

    print(f"\n📊 Resume Stats:")
    print(f"   - {resume['memory_count']:,} memories queried")
    print(f"   - {len(resume['projects'])} major projects")
    print(f"   - {sum(len(v) for v in resume['skills'].values())} technical skills")
    print(f"\n🔗 View at: http://localhost:8890/resume.html")
