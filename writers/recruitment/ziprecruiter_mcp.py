"""
ZipRecruiter MCP Server
ROCN Layer - Job Search Intelligence
"""

import logging
import os
from typing import Optional
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("ziprecruiter-mcp")

ZIPRECRUITER_API_KEY = os.getenv("ZIPRECRUITER_API_KEY", "")
BASE_URL = "https://api.ziprecruiter.com/jobs-app/api/jobs"

@mcp.tool(description="Search for jobs on ZipRecruiter by keyword and location")
async def search_jobs(search: str, location: str = "", results_per_page: int = 10, page: int = 1) -> str:
    """Search ZipRecruiter jobs"""
    if not ZIPRECRUITER_API_KEY:
        return "Error: ZIPRECRUITER_API_KEY not set"

    try:
        params = {
            "search": search,
            "location": location,
            "results_per_page": results_per_page,
            "page": page,
            "api_key": ZIPRECRUITER_API_KEY
        }

        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("jobs"):
            return "No jobs found"

        jobs = data["jobs"]
        result = f"Found {len(jobs)} jobs:\n\n"

        for job in jobs:
            result += f"Title: {job.get('name', 'N/A')}\n"
            result += f"Company: {job.get('hiring_company', {}).get('name', 'N/A')}\n"
            result += f"Location: {job.get('location', 'N/A')}\n"
            result += f"URL: {job.get('url', 'N/A')}\n"
            result += f"Posted: {job.get('posted_time_friendly', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"ZipRecruiter API error: {e}")
        return f"Error: {str(e)}"

@mcp.tool(description="Get job details by job ID")
async def get_job_details(job_id: str) -> str:
    """Get detailed information about a specific job"""
    if not ZIPRECRUITER_API_KEY:
        return "Error: ZIPRECRUITER_API_KEY not set"

    try:
        url = f"{BASE_URL}/{job_id}"
        params = {"api_key": ZIPRECRUITER_API_KEY}

        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        job = response.json()

        result = f"Job ID: {job.get('id', 'N/A')}\n"
        result += f"Title: {job.get('name', 'N/A')}\n"
        result += f"Company: {job.get('hiring_company', {}).get('name', 'N/A')}\n"
        result += f"Location: {job.get('location', 'N/A')}\n"
        result += f"Salary: {job.get('salary', 'Not specified')}\n"
        result += f"Description:\n{job.get('snippet', 'N/A')}\n"
        result += f"URL: {job.get('url', 'N/A')}\n"

        return result

    except Exception as e:
        logger.error(f"ZipRecruiter job details error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
