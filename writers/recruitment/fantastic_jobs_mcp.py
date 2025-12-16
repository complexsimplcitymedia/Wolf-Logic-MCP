"""
Fantastic Jobs MCP Server
ROCN Layer - Job Search Intelligence
"""

import logging
import os
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("fantastic-jobs-mcp")

FANTASTIC_API_KEY = os.getenv("FANTASTIC_JOBS_API_KEY", "")
BASE_URL = "https://api.fantasticjobs.com/v1"

@mcp.tool(description="Search jobs on Fantastic Jobs platform")
async def search_jobs(keywords: str, location: str = "", page: int = 1, per_page: int = 20) -> str:
    """Search for jobs across multiple categories"""
    if not FANTASTIC_API_KEY:
        return "Error: FANTASTIC_JOBS_API_KEY not set"

    try:
        headers = {"X-API-Key": FANTASTIC_API_KEY}
        params = {
            "keywords": keywords,
            "location": location,
            "page": page,
            "per_page": per_page
        }

        response = requests.get(f"{BASE_URL}/jobs/search", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", [])
        if not jobs:
            return "No jobs found"

        result = f"Found {len(jobs)} jobs (Page {page}):\n\n"

        for job in jobs:
            result += f"Title: {job.get('title', 'N/A')}\n"
            result += f"Company: {job.get('company', 'N/A')}\n"
            result += f"Location: {job.get('location', 'N/A')}\n"
            result += f"Salary: {job.get('salary_range', 'Not specified')}\n"
            result += f"Remote: {job.get('remote_friendly', False)}\n"
            result += f"URL: {job.get('apply_url', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"Fantastic Jobs API error: {e}")
        return f"Error: {str(e)}"

@mcp.tool(description="Get job categories available")
async def get_categories() -> str:
    """Get available job categories"""
    if not FANTASTIC_API_KEY:
        return "Error: FANTASTIC_JOBS_API_KEY not set"

    try:
        headers = {"X-API-Key": FANTASTIC_API_KEY}
        response = requests.get(f"{BASE_URL}/categories", headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        categories = data.get("categories", [])
        result = "Available job categories:\n\n"

        for cat in categories:
            result += f"- {cat.get('name', 'N/A')} ({cat.get('count', 0)} jobs)\n"

        return result

    except Exception as e:
        logger.error(f"Fantastic Jobs categories error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
