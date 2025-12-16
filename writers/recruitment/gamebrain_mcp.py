"""
GameBrain MCP Server
ROCN Layer - Gaming Job Intelligence
"""

import logging
import os
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("gamebrain-mcp")

GAMEBRAIN_API_KEY = os.getenv("GAMEBRAIN_API_KEY", "")
BASE_URL = "https://gamebrain.co/api"

@mcp.tool(description="Search for gaming industry jobs")
async def search_gaming_jobs(query: str, location: str = "", limit: int = 20) -> str:
    """Search for jobs in the gaming industry"""
    if not GAMEBRAIN_API_KEY:
        return "Error: GAMEBRAIN_API_KEY not set"

    try:
        headers = {"Authorization": f"Bearer {GAMEBRAIN_API_KEY}"}
        params = {
            "q": query,
            "location": location,
            "limit": limit
        }

        response = requests.get(f"{BASE_URL}/jobs", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if not data.get("jobs"):
            return "No gaming jobs found"

        jobs = data["jobs"]
        result = f"Found {len(jobs)} gaming industry jobs:\n\n"

        for job in jobs:
            result += f"Title: {job.get('title', 'N/A')}\n"
            result += f"Company: {job.get('company', 'N/A')}\n"
            result += f"Location: {job.get('location', 'N/A')}\n"
            result += f"Type: {job.get('job_type', 'N/A')}\n"
            result += f"URL: {job.get('url', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"GameBrain API error: {e}")
        return f"Error: {str(e)}"

@mcp.tool(description="Get gaming companies listing")
async def get_gaming_companies(limit: int = 50) -> str:
    """Get list of gaming companies"""
    if not GAMEBRAIN_API_KEY:
        return "Error: GAMEBRAIN_API_KEY not set"

    try:
        headers = {"Authorization": f"Bearer {GAMEBRAIN_API_KEY}"}
        params = {"limit": limit}

        response = requests.get(f"{BASE_URL}/companies", headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        companies = data.get("companies", [])
        result = f"Found {len(companies)} gaming companies:\n\n"

        for company in companies:
            result += f"Name: {company.get('name', 'N/A')}\n"
            result += f"Location: {company.get('location', 'N/A')}\n"
            result += f"Size: {company.get('size', 'N/A')}\n"
            result += f"Website: {company.get('website', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"GameBrain companies error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
