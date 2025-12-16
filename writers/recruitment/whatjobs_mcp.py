"""
WhatJobs MCP Server
ROCN Layer - Aggregated Job Intelligence
"""

import logging
import os
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("whatjobs-mcp")

WHATJOBS_API_KEY = os.getenv("WHATJOBS_API_KEY", "")
BASE_URL = "https://api.whatjobs.com/v1"

@mcp.tool(description="Search jobs across multiple sources via WhatJobs")
async def search_jobs(query: str, location: str = "", page: int = 1, per_page: int = 20) -> str:
    """Search aggregated job listings"""
    if not WHATJOBS_API_KEY:
        return "Error: WHATJOBS_API_KEY not set"

    try:
        headers = {"Authorization": f"Bearer {WHATJOBS_API_KEY}"}
        params = {
            "what": query,
            "where": location,
            "page": page,
            "per_page": per_page
        }

        response = requests.get(f"{BASE_URL}/jobs", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        jobs = data.get("results", [])
        if not jobs:
            return "No jobs found"

        total = data.get("total", 0)
        result = f"Found {total} total jobs, showing page {page} ({len(jobs)} jobs):\n\n"

        for job in jobs:
            result += f"Title: {job.get('title', 'N/A')}\n"
            result += f"Company: {job.get('company', 'N/A')}\n"
            result += f"Location: {job.get('location', 'N/A')}\n"
            result += f"Salary: {job.get('salary', 'Not specified')}\n"
            result += f"Source: {job.get('source', 'N/A')}\n"
            result += f"Posted: {job.get('date_posted', 'N/A')}\n"
            result += f"URL: {job.get('url', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"WhatJobs API error: {e}")
        return f"Error: {str(e)}"

@mcp.tool(description="Get job alerts for specific criteria")
async def create_job_alert(query: str, location: str = "", email: str = "") -> str:
    """Create a job alert for matching criteria"""
    if not WHATJOBS_API_KEY:
        return "Error: WHATJOBS_API_KEY not set"

    if not email:
        return "Error: Email required for job alerts"

    try:
        headers = {"Authorization": f"Bearer {WHATJOBS_API_KEY}"}
        payload = {
            "query": query,
            "location": location,
            "email": email,
            "frequency": "daily"
        }

        response = requests.post(f"{BASE_URL}/alerts", headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()

        return f"Job alert created successfully!\nID: {data.get('alert_id', 'N/A')}\nQuery: {query}\nLocation: {location}\nEmail: {email}"

    except Exception as e:
        logger.error(f"WhatJobs alert error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
