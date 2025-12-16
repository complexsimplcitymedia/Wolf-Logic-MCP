#!/usr/bin/env python3
"""
IMDB MCP Server - Lightweight Python Implementation
Queries TMDb API for movie/TV credits (better than OMDB - actually free)
No daemon restart needed - runs as standalone service

TMDb API Docs: https://developers.themoviedb.org/3
"""

import os
import json
import requests
from flask import Flask, request, jsonify
from functools import lru_cache

app = Flask(__name__)

# TMDb API - free tier, actually free (not $1/month like OMDB)
# Get key: https://www.themoviedb.org/settings/api (requires free account)
TMDB_API_KEY = os.getenv('TMDB_API_KEY', '')
TMDB_BASE_URL = 'https://api.themoviedb.org/3'


@lru_cache(maxsize=500)
def search_tmdb_movie(title: str, year: str = None):
    """Search TMDb for movie by title, cached"""
    params = {
        'api_key': TMDB_API_KEY,
        'query': title,
        'include_adult': False
    }
    if year:
        params['year'] = year

    try:
        response = requests.get(f'{TMDB_BASE_URL}/search/movie', params=params, timeout=10)
        data = response.json()

        if data.get('results'):
            # Get first result's details
            movie_id = data['results'][0]['id']
            return get_movie_details(movie_id)

        return {'error': 'No results found'}
    except Exception as e:
        return {'error': str(e)}


@lru_cache(maxsize=500)
def get_movie_details(movie_id: int):
    """Get detailed movie info including credits"""
    params = {
        'api_key': TMDB_API_KEY,
        'append_to_response': 'credits,keywords'
    }

    try:
        response = requests.get(f'{TMDB_BASE_URL}/movie/{movie_id}', params=params, timeout=10)
        return response.json()
    except Exception as e:
        return {'error': str(e)}


@lru_cache(maxsize=500)
def search_person(name: str):
    """Search for person by name"""
    params = {
        'api_key': TMDB_API_KEY,
        'query': name,
        'include_adult': False
    }

    try:
        response = requests.get(f'{TMDB_BASE_URL}/search/person', params=params, timeout=10)
        return response.json()
    except Exception as e:
        return {'error': str(e)}


@lru_cache(maxsize=500)
def get_person_credits(person_id: int):
    """Get person's movie/TV credits"""
    params = {
        'api_key': TMDB_API_KEY
    }

    try:
        response = requests.get(f'{TMDB_BASE_URL}/person/{person_id}/combined_credits', params=params, timeout=10)
        return response.json()
    except Exception as e:
        return {'error': str(e)}


@lru_cache(maxsize=500)
def search_by_crew_role(name: str, department: str = None):
    """
    Search for person and filter their credits by department
    department examples: 'Lighting', 'Camera', 'Electrical', 'Crew'
    """
    # First find the person
    person_results = search_person(name)

    if person_results.get('results'):
        person_id = person_results['results'][0]['id']

        # Get their credits
        credits = get_person_credits(person_id)

        if department:
            # Filter crew credits by department
            filtered_crew = []
            for credit in credits.get('crew', []):
                if department.lower() in credit.get('department', '').lower():
                    filtered_crew.append(credit)

            return {
                'person': person_results['results'][0],
                'credits': filtered_crew,
                'total_credits': len(filtered_crew)
            }
        else:
            return {
                'person': person_results['results'][0],
                'credits': credits
            }

    return {'error': 'Person not found'}


@app.route('/mcp/search', methods=['POST'])
def mcp_search():
    """
    MCP endpoint: search by title
    POST /mcp/search
    {
        "title": "The Matrix",
        "year": "1999"
    }
    """
    data = request.get_json()
    title = data.get('title')
    year = data.get('year')

    if not title:
        return jsonify({'error': 'Title required'}), 400

    result = search_tmdb_movie(title, year)
    return jsonify(result)


@app.route('/mcp/movie/<int:movie_id>', methods=['GET'])
def mcp_movie_details(movie_id):
    """
    MCP endpoint: get movie by TMDb ID
    GET /mcp/movie/603
    """
    result = get_movie_details(movie_id)
    return jsonify(result)


@app.route('/mcp/person', methods=['POST'])
def mcp_person_search():
    """
    MCP endpoint: search person
    POST /mcp/person
    {
        "name": "David Adams"
    }
    """
    data = request.get_json()
    name = data.get('name')

    if not name:
        return jsonify({'error': 'Name required'}), 400

    result = search_person(name)
    return jsonify(result)


@app.route('/mcp/credits', methods=['POST'])
def mcp_credits():
    """
    MCP endpoint: Get person's credits with department filter
    POST /mcp/credits
    {
        "name": "David Adams",
        "department": "Lighting"  # optional: Lighting, Camera, Electrical, Crew
    }
    """
    data = request.get_json()
    name = data.get('name')
    department = data.get('department')

    if not name:
        return jsonify({'error': 'Name required'}), 400

    result = search_by_crew_role(name, department)
    return jsonify(result)


@app.route('/mcp/person/<int:person_id>/credits', methods=['GET'])
def mcp_person_credits(person_id):
    """
    MCP endpoint: Get person's credits by ID
    GET /mcp/person/12345/credits
    """
    result = get_person_credits(person_id)
    return jsonify(result)


@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    has_key = bool(TMDB_API_KEY)
    return jsonify({
        'status': 'running',
        'api': 'TMDb',
        'api_configured': has_key
    })


if __name__ == '__main__':
    if not TMDB_API_KEY:
        print("WARNING: TMDB_API_KEY not set.")
        print("Get free key:")
        print("  1. Create account: https://www.themoviedb.org/signup")
        print("  2. Get API key: https://www.themoviedb.org/settings/api")
        print("  3. Set with: export TMDB_API_KEY=your_key")

    print("\nIMDB MCP Server (powered by TMDb API)")
    print("Running on http://localhost:8765")
    print("\nEndpoints:")
    print("  POST /mcp/search - Search movie by title")
    print("  GET  /mcp/movie/<id> - Get movie by TMDb ID")
    print("  POST /mcp/person - Search for person")
    print("  POST /mcp/credits - Get person's credits (with department filter)")
    print("  GET  /mcp/person/<id>/credits - Get person's credits by ID")
    print("  GET  /health - Health check")
    print()

    app.run(host='0.0.0.0', port=8765, debug=False)
