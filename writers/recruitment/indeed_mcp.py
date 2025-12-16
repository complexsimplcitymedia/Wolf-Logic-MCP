"""
Indeed MCP Server
ROCN Layer - Job Search Intelligence
"""

import logging
import os
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("indeed-mcp")

INDEED_API_KEY = os.getenv("INDEED_API_KEY", "")
INDEED_PUBLISHER_ID = os.getenv("INDEED_PUBLISHER_ID", "")
BASE_URL = "https://api.indeed.com/ads/apisearch"

@mcp.tool(description="Search for jobs on Indeed")
async def search_jobs(query: str, location: str = "", job_type: str = "", limit: int = 25, start: int = 0) -> str:
    """Search Indeed for jobs"""
    if not INDEED_PUBLISHER_ID:
        return "Error: INDEED_PUBLISHER_ID not set"

    try:
        params = {
            "publisher": INDEED_PUBLISHER_ID,
            "q": query,
            "l": location,
            "jt": job_type,
            "limit": limit,
            "start": start,
            "format": "json",
            "v": "2"
        }

        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get("results", [])
        if not results:
            return "No jobs found"

        result = f"Found {data.get('totalResults', 0)} total jobs, showing {len(results)}:\n\n"

        for job in results:
            result += f"Title: {job.get('jobtitle', 'N/A')}\n"
            result += f"Company: {job.get('company', 'N/A')}\n"
            result += f"Location: {job.get('formattedLocation', 'N/A')}\n"
            result += f"Snippet: {job.get('snippet', 'N/A')}\n"
            result += f"Date: {job.get('date', 'N/A')}\n"
            result += f"URL: {job.get('url', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"Indeed API error: {e}")
        return f"Error: {str(e)}"

@mcp.tool(description="Get job type statistics")
async def get_job_types(query: str, location: str = "") -> str:
    """Get breakdown of job types for a search"""
    if not INDEED_PUBLISHER_ID:
        return "Error: INDEED_PUBLISHER_ID not set"

    try:
        job_types = ["fulltime", "parttime", "contract", "internship", "temporary"]
        result = f"Job type breakdown for '{query}' in '{location}':\n\n"

        for jt in job_types:
            params = {
                "publisher": INDEED_PUBLISHER_ID,
                "q": query,
                "l": location,
                "jt": jt,
                "limit": 1,
                "format": "json",
                "v": "2"
            }

            response = requests.get(BASE_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            count = data.get("totalResults", 0)
            result += f"{jt.capitalize()}: {count} jobs\n"

        return result

    except Exception as e:
        logger.error(f"Indeed job types error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
