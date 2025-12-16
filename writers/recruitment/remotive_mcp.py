"""
Remotive MCP Server
ROCN Layer - Remote Job Intelligence
"""

import logging
import os
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("remotive-mcp")

BASE_URL = "https://remotive.com/api/remote-jobs"

@mcp.tool(description="Search remote jobs on Remotive")
async def search_remote_jobs(category: str = "", search: str = "", limit: int = 50) -> str:
    """Search for remote work opportunities"""
    try:
        params = {}
        if category:
            params["category"] = category
        if search:
            params["search"] = search
        if limit:
            params["limit"] = limit

        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", [])
        if not jobs:
            return "No remote jobs found"

        result = f"Found {len(jobs)} remote jobs:\n\n"

        for job in jobs:
            result += f"Title: {job.get('title', 'N/A')}\n"
            result += f"Company: {job.get('company_name', 'N/A')}\n"
            result += f"Category: {job.get('category', 'N/A')}\n"
            result += f"Job Type: {job.get('job_type', 'N/A')}\n"
            result += f"Location: {job.get('candidate_required_location', 'Anywhere')}\n"
            result += f"Salary: {job.get('salary', 'Not specified')}\n"
            result += f"Published: {job.get('publication_date', 'N/A')}\n"
            result += f"URL: {job.get('url', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"Remotive API error: {e}")
        return f"Error: {str(e)}"

@mcp.tool(description="Get available job categories on Remotive")
async def get_categories() -> str:
    """Get list of remote job categories"""
    categories = [
        "Software Development",
        "Customer Support",
        "Design",
        "Marketing",
        "Sales",
        "Product",
        "Business",
        "Data",
        "DevOps / Sysadmin",
        "Finance / Legal",
        "HR",
        "QA",
        "Writing",
        "All others"
    ]

    result = "Available remote job categories:\n\n"
    for cat in categories:
        result += f"- {cat}\n"

    return result

@mcp.tool(description="Get latest remote jobs")
async def get_latest_jobs(limit: int = 20) -> str:
    """Get the most recently posted remote jobs"""
    try:
        params = {"limit": limit}
        response = requests.get(BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        jobs = data.get("jobs", [])[:limit]
        result = f"Latest {len(jobs)} remote jobs:\n\n"

        for job in jobs:
            result += f"{job.get('title', 'N/A')} at {job.get('company_name', 'N/A')}\n"
            result += f"Category: {job.get('category', 'N/A')}\n"
            result += f"Posted: {job.get('publication_date', 'N/A')}\n"
            result += f"URL: {job.get('url', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"Remotive latest jobs error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
