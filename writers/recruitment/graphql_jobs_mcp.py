"""
GraphQL Jobs MCP Server
ROCN Layer - Developer Job Intelligence
"""

import logging
import os
import requests
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("graphql-jobs-mcp")

BASE_URL = "https://api.graphql.jobs/v1"

@mcp.tool(description="Search GraphQL and developer jobs")
async def search_jobs(query: str = "", location: str = "", remote: bool = False) -> str:
    """Search for GraphQL and tech jobs"""
    try:
        graphql_query = """
        query Jobs($input: JobsInput!) {
            jobs(input: $input) {
                id
                title
                commitment {
                    title
                }
                cities {
                    name
                    country {
                        name
                    }
                }
                remoteOk
                company {
                    name
                    websiteUrl
                }
                description
                applyUrl
                postedAt
                tags {
                    name
                }
            }
        }
        """

        variables = {
            "input": {
                "slug": query if query else None,
                "type": "FULL_TIME"
            }
        }

        response = requests.post(
            BASE_URL,
            json={"query": graphql_query, "variables": variables},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        jobs = data.get("data", {}).get("jobs", [])
        if not jobs:
            return "No jobs found"

        result = f"Found {len(jobs)} GraphQL/Developer jobs:\n\n"

        for job in jobs:
            result += f"Title: {job.get('title', 'N/A')}\n"
            result += f"Company: {job.get('company', {}).get('name', 'N/A')}\n"

            cities = job.get('cities', [])
            if cities:
                city_str = ", ".join([f"{c.get('name', '')} ({c.get('country', {}).get('name', '')})" for c in cities])
                result += f"Location: {city_str}\n"

            result += f"Remote OK: {'Yes' if job.get('remoteOk') else 'No'}\n"
            result += f"Commitment: {job.get('commitment', {}).get('title', 'N/A')}\n"

            tags = job.get('tags', [])
            if tags:
                result += f"Tags: {', '.join([t.get('name', '') for t in tags])}\n"

            result += f"Posted: {job.get('postedAt', 'N/A')}\n"
            result += f"Apply: {job.get('applyUrl', 'N/A')}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"GraphQL Jobs API error: {e}")
        return f"Error: {str(e)}"

@mcp.tool(description="Get companies hiring on GraphQL Jobs")
async def get_companies() -> str:
    """Get list of companies posting GraphQL jobs"""
    try:
        graphql_query = """
        query {
            companies {
                id
                name
                websiteUrl
                logoUrl
                jobs {
                    id
                    title
                }
            }
        }
        """

        response = requests.post(
            BASE_URL,
            json={"query": graphql_query},
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        companies = data.get("data", {}).get("companies", [])
        result = f"Found {len(companies)} companies:\n\n"

        for company in companies:
            result += f"Company: {company.get('name', 'N/A')}\n"
            result += f"Website: {company.get('websiteUrl', 'N/A')}\n"
            jobs_count = len(company.get('jobs', []))
            result += f"Active Jobs: {jobs_count}\n"
            result += "-" * 50 + "\n"

        return result

    except Exception as e:
        logger.error(f"GraphQL Jobs companies error: {e}")
        return f"Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()
