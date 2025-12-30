#!/usr/bin/env python3
"""
Wolf Hunt API - Unified Job Search Endpoint
Wraps JobSpy library and serves results to wolf-hunt-ui at port 3333
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from jobspy import scrape_jobs
import logging
import psycopg2
import json

app = Flask(__name__)
CORS(app)  # Allow requests from UI on port 3333

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database config
PG_CONFIG = {
    "host": "100.110.82.181",
    "port": 5433,
    "database": "wolf_logic",
    "user": "wolf",
    "password": "wolflogic2024"
}

# Map board names to JobSpy site_names
BOARD_MAPPING = {
    'indeed': 'indeed',
    'linkedin': 'linkedin',
    'ziprecruiter': 'zip_recruiter',
    'glassdoor': 'glassdoor',
    'google': 'google',
    'remotive': 'indeed',  # Remotive doesn't need separate - Indeed covers it
}


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'operational', 'service': 'wolf_hunt_api'}), 200


@app.route('/search', methods=['POST'])
def search_jobs():
    """
    Unified job search endpoint for all boards

    Request JSON:
    {
        "query": "software engineer",
        "location": "remote",
        "boards": ["indeed", "linkedin", "ziprecruiter"],
        "results_wanted": 25
    }
    """
    try:
        data = request.json
        query = data.get('query', '')
        location = data.get('location', '')
        boards = data.get('boards', ['indeed', 'linkedin'])
        results_wanted = data.get('results_wanted', 25)

        if not query:
            return jsonify({'error': 'Query is required'}), 400

        # Map board names to JobSpy site names
        site_names = []
        for board in boards:
            if board in BOARD_MAPPING:
                site_name = BOARD_MAPPING[board]
                if site_name not in site_names:
                    site_names.append(site_name)

        if not site_names:
            site_names = ['indeed', 'linkedin']  # Default

        logger.info(f"Searching: query='{query}', location='{location}', sites={site_names}")

        # JobSpy search
        is_remote = location.lower() in ['remote', '']

        jobs_df = scrape_jobs(
            site_name=site_names,
            search_term=query,
            location=location if location else '',
            is_remote=is_remote,
            results_wanted=results_wanted,
            hours_old=168,  # 7 days
            country_indeed='USA'
        )

        # Convert DataFrame to list of dicts
        jobs = []
        for _, row in jobs_df.iterrows():
            # Helper to safely get values and handle NaN
            def safe_get(key, default=''):
                val = row.get(key, default)
                if isinstance(val, float) and str(val) == 'nan':
                    return default
                return val if val is not None else default

            description = safe_get('description', '')
            if description:
                description = str(description)[:500]  # Truncate

            jobs.append({
                'id': safe_get('id', ''),
                'title': safe_get('title', 'N/A'),
                'company': safe_get('company', 'N/A'),
                'location': safe_get('location', 'N/A'),
                'description': description,
                'url': safe_get('job_url', ''),
                'source': safe_get('site', 'unknown'),
                'date': str(safe_get('date_posted', '')),
                'salary': safe_get('salary_string', ''),
                'remote': bool(safe_get('is_remote', False))
            })

        logger.info(f"Found {len(jobs)} jobs")

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs),
            'query': query,
            'location': location
        }), 200

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all jobs from database (wolf_hunt namespace)"""
    try:
        conn = psycopg2.connect(**PG_CONFIG)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT metadata
                FROM memories
                WHERE namespace='wolf_hunt'
                ORDER BY (metadata->>'location_priority')::int, created_at DESC
            """)

            jobs = []
            for row in cur.fetchall():
                meta = row[0]
                jobs.append({
                    'id': meta.get('url', ''),
                    'title': meta.get('title', 'N/A'),
                    'company': meta.get('company', 'N/A'),
                    'location': meta.get('location', 'N/A'),
                    'description': '',
                    'url': meta.get('url', ''),
                    'source': meta.get('job_site', 'unknown'),
                    'date': meta.get('date_posted', ''),
                    'salary': f"${meta.get('salary_min', 0)}-${meta.get('salary_max', 0)}" if meta.get('salary_min', 0) > 0 else '',
                    'remote': meta.get('is_remote', False),
                    'priority': meta.get('location_priority', 5),
                    'search_term': meta.get('search_term', ''),
                    'search_location': meta.get('search_location', '')
                })

        conn.close()
        logger.info(f"Returning {len(jobs)} jobs from database")

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        logger.error(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/jobs/scraped', methods=['GET'])
def get_scraped_jobs():
    """Get all scraped jobs from database (wolf_hunt namespace) - UI endpoint"""
    try:
        candidate = request.args.get('candidate', '')

        conn = psycopg2.connect(**PG_CONFIG)
        with conn.cursor() as cur:
            cur.execute("""
                SELECT metadata
                FROM memories
                WHERE namespace='wolf_hunt'
                ORDER BY (metadata->>'location_priority')::int, created_at DESC
            """)

            jobs = []
            for row in cur.fetchall():
                meta = row[0]
                jobs.append({
                    'id': meta.get('url', ''),
                    'title': meta.get('title', 'N/A'),
                    'company': meta.get('company', 'N/A'),
                    'location': meta.get('location', 'N/A'),
                    'description': '',
                    'url': meta.get('url', ''),
                    'source': meta.get('job_site', 'unknown'),
                    'board': meta.get('job_site', 'unknown'),
                    'scraped_at': meta.get('scraped_at', ''),
                    'candidate_match': candidate if candidate else None
                })

        conn.close()
        logger.info(f"UI request: Returning {len(jobs)} scraped jobs")

        return jsonify({
            'success': True,
            'jobs': jobs,
            'count': len(jobs)
        }), 200

    except Exception as e:
        logger.error(f"Database error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/boards', methods=['GET'])
def get_boards():
    """Return available job boards"""
    return jsonify({
        'boards': list(BOARD_MAPPING.keys()),
        'default': ['indeed', 'linkedin', 'ziprecruiter']
    }), 200


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
