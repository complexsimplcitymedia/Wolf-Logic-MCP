#!/usr/bin/env python3
"""
Indeed Job Board Scraper
"""

import aiohttp
import asyncio
from typing import List, Dict
from bs4 import BeautifulSoup
from .base_board import JobBoard
import urllib.parse

class IndeedBoard(JobBoard):
    """Indeed job board scraper"""

    def __init__(self):
        super().__init__("Indeed")
        self.base_url = "https://www.indeed.com"
        self.search_url = f"{self.base_url}/jobs"

    async def search(self, query: str, location: str = "remote", limit: int = 50, **kwargs) -> List[Dict]:
        """
        Search Indeed for jobs

        Args:
            query: Job search keywords
            location: Location (city, state, or "remote")
            limit: Max results to return
            **kwargs: Additional parameters

        Returns:
            List of normalized job dictionaries
        """
        jobs = []

        # Build search params
        params = {
            'q': query,
            'l': location,
            'limit': min(limit, 50),
            'sort': 'date'
        }

        try:
            async with aiohttp.ClientSession() as session:
                # Make request with user agent
                headers = {
                    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                }

                async with session.get(self.search_url, params=params, headers=headers, timeout=30) as response:
                    if response.status == 200:
                        html = await response.text()
                        jobs = self._parse_search_results(html)
                    else:
                        print(f"[INDEED] Search failed with status {response.status}")

        except Exception as e:
            print(f"[INDEED] Error during search: {e}")

        return jobs[:limit]

    def _parse_search_results(self, html: str) -> List[Dict]:
        """Parse Indeed search results HTML"""
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')

        # Find job cards (Indeed's structure may vary)
        job_cards = soup.find_all('div', class_='job_seen_beacon') or soup.find_all('div', class_='jobsearch-SerpJobCard')

        for card in job_cards:
            try:
                # Extract job data
                title_elem = card.find('h2', class_='jobTitle') or card.find('a', class_='jobtitle')
                company_elem = card.find('span', class_='companyName') or card.find('span', class_='company')
                location_elem = card.find('div', class_='companyLocation') or card.find('span', class_='location')
                summary_elem = card.find('div', class_='job-snippet') or card.find('div', class_='summary')

                # Get job URL
                link_elem = card.find('a', class_='jcs-JobTitle') or title_elem
                job_url = ''
                if link_elem and link_elem.get('href'):
                    job_url = f"{self.base_url}{link_elem['href']}"

                # Get salary if available
                salary_elem = card.find('div', class_='metadata salary-snippet-container')
                salary = salary_elem.get_text(strip=True) if salary_elem else None

                # Create job dict
                if title_elem:
                    raw_job = {
                        'title': title_elem.get_text(strip=True),
                        'company': company_elem.get_text(strip=True) if company_elem else 'Unknown',
                        'location': location_elem.get_text(strip=True) if location_elem else 'Unknown',
                        'description': summary_elem.get_text(strip=True) if summary_elem else '',
                        'url': job_url,
                        'salary': salary
                    }

                    jobs.append(self.normalize_job(raw_job))

            except Exception as e:
                print(f"[INDEED] Error parsing job card: {e}")
                continue

        return jobs

    def get_board_info(self) -> Dict:
        """Return Indeed board metadata"""
        return {
            'name': self.name,
            'supported_locations': 'All US cities + remote',
            'rate_limit': '~100 requests/hour',
            'features': ['salary_data', 'company_reviews', 'date_sorting'],
            'reliability': 'high'
        }
