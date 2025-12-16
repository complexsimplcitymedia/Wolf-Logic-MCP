#!/usr/bin/env python3
"""
Wolf Hunt API Server
Backend API for wolf-hunt job tracking system
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
from resume_generator import generate_resume

app = Flask(__name__)
CORS(app)

# Database configuration
import os
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': int(os.getenv('DB_PORT', 5433)),
    'user': os.getenv('DB_USER', 'wolf'),
    'password': os.getenv('DB_PASSWORD', 'wolflogic2024'),
    'database': os.getenv('DB_NAME', 'wolf_logic')
}

def get_db():
    """Get database connection"""
    return psycopg2.connect(**DB_CONFIG, cursor_factory=RealDictCursor)

@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get all candidates"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT
                c.*,
                COUNT(ja.id) as total_applications,
                COUNT(CASE WHEN ja.response_received THEN 1 END) as responses,
                COUNT(CASE WHEN ja.interview_scheduled THEN 1 END) as interviews
            FROM candidates c
            LEFT JOIN job_applications ja ON c.id = ja.candidate_id
            GROUP BY c.id
            ORDER BY c.name
        """)
        candidates = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'candidates': [dict(c) for c in candidates],
            'count': len(candidates)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/candidates/<int:candidate_id>', methods=['GET'])
def get_candidate(candidate_id):
    """Get specific candidate"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("SELECT * FROM candidates WHERE id = %s", (candidate_id,))
        candidate = cur.fetchone()
        cur.close()
        conn.close()

        if not candidate:
            return jsonify({'success': False, 'error': 'Candidate not found'}), 404

        return jsonify({
            'success': True,
            'candidate': dict(candidate)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/candidates/<int:candidate_id>/applications', methods=['GET'])
def get_candidate_applications(candidate_id):
    """Get all applications for a candidate"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM job_applications
            WHERE candidate_id = %s
            ORDER BY date_applied DESC
        """, (candidate_id,))
        applications = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'applications': [dict(a) for a in applications],
            'count': len(applications)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get all saved jobs"""
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM job_applications
            ORDER BY date_applied DESC
            LIMIT 100
        """)
        jobs = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'jobs': [dict(j) for j in jobs],
            'count': len(jobs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/applications', methods=['POST'])
def create_application():
    """Create new job application"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO job_applications
            (candidate_id, company_name, position_title, job_url, notes)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            data.get('candidate_id'),
            data['company_name'],
            data['position_title'],
            data.get('job_url'),
            data.get('notes')
        ))

        app_id = cur.fetchone()['id']
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'application_id': app_id
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/applications/<int:app_id>', methods=['PUT'])
def update_application(app_id):
    """Update job application"""
    try:
        data = request.json
        conn = get_db()
        cur = conn.cursor()

        # Build update query dynamically based on provided fields
        update_fields = []
        values = []

        for field in ['email_sent', 'email_sent_date', 'call_made', 'call_date',
                     'response_received', 'response_type', 'response_date',
                     'interview_scheduled', 'interview_date', 'notes']:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])

        if not update_fields:
            return jsonify({'success': False, 'error': 'No fields to update'}), 400

        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(app_id)

        query = f"UPDATE job_applications SET {', '.join(update_fields)} WHERE id = %s"
        cur.execute(query, values)
        conn.commit()
        cur.close()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get overall statistics"""
    try:
        conn = get_db()
        cur = conn.cursor()

        cur.execute("""
            SELECT
                COUNT(*) as total_applications,
                COUNT(CASE WHEN response_received THEN 1 END) as responses,
                COUNT(CASE WHEN interview_scheduled THEN 1 END) as interviews,
                COUNT(DISTINCT candidate_id) as active_candidates
            FROM job_applications
        """)
        stats = cur.fetchone()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'stats': dict(stats)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/jobs/scraped', methods=['GET'])
def get_scraped_jobs():
    """Get all scraped jobs"""
    try:
        candidate = request.args.get('candidate')
        conn = get_db()
        cur = conn.cursor()

        if candidate:
            cur.execute("""
                SELECT * FROM scraped_jobs
                WHERE candidate_match = %s
                ORDER BY scraped_at DESC
            """, (candidate,))
        else:
            cur.execute("""
                SELECT * FROM scraped_jobs
                ORDER BY scraped_at DESC
            """)

        jobs = cur.fetchall()
        cur.close()
        conn.close()

        return jsonify({
            'success': True,
            'jobs': [dict(j) for j in jobs],
            'count': len(jobs)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/resume/generate', methods=['POST'])
def generate_resume_endpoint():
    """Generate resume for candidate and job"""
    try:
        data = request.json
        candidate_name = data.get('candidate_name')
        job_title = data.get('job_title')
        job_description = data.get('job_description', '')

        if not candidate_name or not job_title:
            return jsonify({
                'success': False,
                'error': 'candidate_name and job_title required'
            }), 400

        resume = generate_resume(candidate_name, job_title, job_description)

        if 'error' in resume:
            return jsonify({'success': False, 'error': resume['error']}), 404

        return jsonify({
            'success': True,
            'resume': resume
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'service': 'wolf-hunt-api',
        'timestamp': datetime.now().isoformat()
    })

if __name__ == '__main__':
    print("""
╔════════════════════════════════════════════════════════╗
║              WOLF HUNT API SERVER                      ║
║              Job Tracking Backend v1.0                 ║
╠════════════════════════════════════════════════════════╣
║  API running on: http://localhost:5000                 ║
║  Database: wolf_logic@100.110.82.181:5433                   ║
║  Candidates: David Adams, Brice Wilson                 ║
╚════════════════════════════════════════════════════════╝

Available Endpoints:
  GET  /api/candidates - List all candidates
  GET  /api/candidates/<id> - Get candidate details
  GET  /api/candidates/<id>/applications - Get applications
  GET  /api/jobs - Get all job applications
  POST /api/applications - Create application
  PUT  /api/applications/<id> - Update application
  GET  /api/stats - Get statistics
  GET  /health - Health check

Starting server...
    """)

    app.run(host='0.0.0.0', port=5000, debug=True)
