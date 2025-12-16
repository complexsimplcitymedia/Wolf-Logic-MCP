#!/usr/bin/env python3
"""
Job Board - Extract all jobs from Wolf Hunt namespace and display
"""
import psycopg2
import json
import re

DB_CONFIG = {
    'host': '100.110.82.181',
    'port': 5433,
    'database': 'wolf_logic',
    'user': 'wolf',
    'password': 'wolflogic2024'
}

def parse_job_content(content):
    """Parse job content string into structured data"""
    job = {}

    # Extract job title and company
    title_match = re.search(r'Job:\s*(.+?)\s+at\s+(.+?)(?:\n|$)', content)
    if title_match:
        job['title'] = title_match.group(1).strip()
        job['company'] = title_match.group(2).strip()

    # Extract location
    location_match = re.search(r'Location:\s*(.+?)(?:\n|$)', content)
    if location_match:
        job['location'] = location_match.group(1).strip()

    # Extract site
    site_match = re.search(r'Site:\s*(.+?)(?:\n|$)', content)
    if site_match:
        job['site'] = site_match.group(1).strip()

    # Extract posted date
    posted_match = re.search(r'Posted:\s*(.+?)(?:\n|$)', content)
    if posted_match:
        job['posted'] = posted_match.group(1).strip()

    # Extract salary
    salary_match = re.search(r'Salary:\s*(.+?)(?:\n|$)', content)
    if salary_match:
        job['salary'] = salary_match.group(1).strip()

    # Extract remote status
    remote_match = re.search(r'Remote:\s*(.+?)(?:\n|$)', content)
    if remote_match:
        job['remote'] = remote_match.group(1).strip().lower() in ['true', 'yes']

    # Extract URL
    url_match = re.search(r'URL:\s*(.+?)(?:\n|$)', content)
    if url_match:
        job['url'] = url_match.group(1).strip()

    # Extract description (everything after "Description:")
    desc_match = re.search(r'Description:\s*(.+)', content, re.DOTALL)
    if desc_match:
        job['description'] = desc_match.group(1).strip()

    return job

def extract_all_jobs():
    """Extract all jobs from wolf_hunt namespace"""
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT content, created_at
        FROM memories
        WHERE namespace = 'wolf_hunt'
        AND content LIKE '%Job:%at%'
        ORDER BY created_at DESC;
    """)

    jobs = []
    for content, created_at in cursor.fetchall():
        job = parse_job_content(content)
        if job.get('title'):
            job['imported_at'] = created_at.isoformat()
            jobs.append(job)

    cursor.close()
    conn.close()

    return jobs

def generate_jobs_html(jobs):
    """Generate HTML job board"""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Wolf Hunt - {len(jobs)} Jobs Available</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: 'Courier New', monospace;
            background: #0a0a0a;
            color: #00ff00;
            padding: 20px;
        }}

        .header {{
            max-width: 1400px;
            margin: 0 auto 40px;
            border-bottom: 2px solid #00ff00;
            padding-bottom: 20px;
        }}

        h1 {{
            font-size: 3em;
            text-shadow: 0 0 10px #00ff00;
        }}

        .stats {{
            display: flex;
            gap: 30px;
            margin-top: 20px;
            font-size: 1.2em;
        }}

        .stat {{
            background: #1a1a1a;
            padding: 10px 20px;
            border: 1px solid #00ff00;
            border-radius: 4px;
        }}

        .filters {{
            max-width: 1400px;
            margin: 0 auto 30px;
            background: #1a1a1a;
            padding: 20px;
            border: 1px solid #00ff00;
        }}

        .filter-group {{
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            margin-bottom: 15px;
        }}

        input, select {{
            background: #0a0a0a;
            border: 1px solid #00ff00;
            color: #00ff00;
            padding: 8px 12px;
            font-family: 'Courier New', monospace;
        }}

        .jobs-grid {{
            max-width: 1400px;
            margin: 0 auto;
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
            gap: 20px;
        }}

        .job-card {{
            background: #1a1a1a;
            border: 1px solid #00ff00;
            padding: 20px;
            border-radius: 8px;
            transition: all 0.3s;
        }}

        .job-card:hover {{
            border-color: #00ff00;
            box-shadow: 0 0 20px #00ff00;
            transform: translateY(-2px);
        }}

        .job-title {{
            font-size: 1.3em;
            font-weight: bold;
            margin-bottom: 10px;
            color: #00ff00;
        }}

        .job-company {{
            font-size: 1.1em;
            color: #00cc00;
            margin-bottom: 10px;
        }}

        .job-meta {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            margin: 10px 0;
            font-size: 0.9em;
        }}

        .meta-tag {{
            background: #0a0a0a;
            padding: 4px 8px;
            border: 1px solid #00ff00;
            border-radius: 3px;
        }}

        .remote-tag {{
            background: #00ff00;
            color: #0a0a0a;
            padding: 4px 8px;
            border-radius: 3px;
            font-weight: bold;
        }}

        .job-description {{
            margin: 15px 0;
            color: #00cc00;
            font-size: 0.9em;
            max-height: 150px;
            overflow: hidden;
            text-overflow: ellipsis;
        }}

        .apply-btn {{
            display: inline-block;
            background: #0a0a0a;
            border: 2px solid #00ff00;
            color: #00ff00;
            padding: 10px 20px;
            text-decoration: none;
            border-radius: 4px;
            margin-top: 10px;
            transition: all 0.3s;
        }}

        .apply-btn:hover {{
            background: #00ff00;
            color: #0a0a0a;
        }}

        .no-results {{
            text-align: center;
            padding: 60px;
            font-size: 1.5em;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🐺 WOLF HUNT</h1>
        <div class="stats">
            <div class="stat">Total Jobs: <strong id="total-jobs">{len(jobs)}</strong></div>
            <div class="stat">Remote: <strong id="remote-jobs">{sum(1 for j in jobs if j.get('remote'))}</strong></div>
            <div class="stat">Recent (7d): <strong id="recent-jobs">{sum(1 for j in jobs if '2025-12' in j.get('posted', ''))}</strong></div>
        </div>
    </div>

    <div class="filters">
        <div class="filter-group">
            <input type="text" id="search-title" placeholder="Search titles..." onkeyup="filterJobs()">
            <input type="text" id="search-company" placeholder="Search companies..." onkeyup="filterJobs()">
            <input type="text" id="search-location" placeholder="Search locations..." onkeyup="filterJobs()">
            <select id="filter-remote" onchange="filterJobs()">
                <option value="">All Jobs</option>
                <option value="true">Remote Only</option>
                <option value="false">On-site Only</option>
            </select>
            <select id="filter-site" onchange="filterJobs()">
                <option value="">All Sites</option>
"""

    # Get unique sites
    sites = set(j.get('site', 'unknown') for j in jobs)
    for site in sorted(sites):
        html += f'                <option value="{site}">{site.title()}</option>\n'

    html += """            </select>
        </div>
    </div>

    <div class="jobs-grid" id="jobs-grid">
"""

    for job in jobs:
        remote_badge = '<span class="remote-tag">REMOTE</span>' if job.get('remote') else ''
        description_preview = job.get('description', '')[:300] + '...' if len(job.get('description', '')) > 300 else job.get('description', '')

        html += f"""        <div class="job-card"
             data-title="{job.get('title', '').lower()}"
             data-company="{job.get('company', '').lower()}"
             data-location="{job.get('location', '').lower()}"
             data-remote="{str(job.get('remote', False)).lower()}"
             data-site="{job.get('site', 'unknown')}">
            <div class="job-title">{job.get('title', 'Unknown Position')}</div>
            <div class="job-company">{job.get('company', 'Unknown Company')}</div>
            <div class="job-meta">
                <span class="meta-tag">📍 {job.get('location', 'Location TBD')}</span>
                <span class="meta-tag">📅 {job.get('posted', 'Date unknown')}</span>
                <span class="meta-tag">💰 {job.get('salary', 'Not specified')}</span>
                {remote_badge}
            </div>
            <div class="job-description">{description_preview}</div>
            <a href="{job.get('url', '#')}" class="apply-btn" target="_blank">APPLY NOW →</a>
        </div>
"""

    html += """    </div>

    <div class="no-results" id="no-results" style="display: none;">
        No jobs found matching your filters.
    </div>

    <script>
        function filterJobs() {
            const titleSearch = document.getElementById('search-title').value.toLowerCase();
            const companySearch = document.getElementById('search-company').value.toLowerCase();
            const locationSearch = document.getElementById('search-location').value.toLowerCase();
            const remoteFilter = document.getElementById('filter-remote').value;
            const siteFilter = document.getElementById('filter-site').value;

            const cards = document.querySelectorAll('.job-card');
            let visibleCount = 0;

            cards.forEach(card => {
                const title = card.dataset.title;
                const company = card.dataset.company;
                const location = card.dataset.location;
                const remote = card.dataset.remote;
                const site = card.dataset.site;

                const matchesTitle = !titleSearch || title.includes(titleSearch);
                const matchesCompany = !companySearch || company.includes(companySearch);
                const matchesLocation = !locationSearch || location.includes(locationSearch);
                const matchesRemote = !remoteFilter || remote === remoteFilter;
                const matchesSite = !siteFilter || site === siteFilter;

                if (matchesTitle && matchesCompany && matchesLocation && matchesRemote && matchesSite) {
                    card.style.display = 'block';
                    visibleCount++;
                } else {
                    card.style.display = 'none';
                }
            });

            document.getElementById('no-results').style.display = visibleCount === 0 ? 'block' : 'none';
        }
    </script>
</body>
</html>
"""
    return html

if __name__ == '__main__':
    print("🐺 Extracting all jobs from librarian...")
    jobs = extract_all_jobs()

    print(f"✅ Found {len(jobs)} jobs")

    # Save JSON
    with open('jobs.json', 'w') as f:
        json.dump(jobs, f, indent=2)
    print(f"✅ Saved jobs.json")

    # Generate HTML
    html = generate_jobs_html(jobs)
    with open('jobs.html', 'w') as f:
        f.write(html)
    print(f"✅ Saved jobs.html")

    # Stats
    remote_count = sum(1 for j in jobs if j.get('remote'))
    sites = {}
    for j in jobs:
        site = j.get('site', 'unknown')
        sites[site] = sites.get(site, 0) + 1

    print(f"\n📊 Job Stats:")
    print(f"   Total: {len(jobs)}")
    print(f"   Remote: {remote_count}")
    print(f"   Sites: {dict(sites)}")
    print(f"\n🔗 View at: http://localhost:8890/jobs.html")
