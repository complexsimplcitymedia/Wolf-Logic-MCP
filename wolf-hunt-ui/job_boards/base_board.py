#!/usr/bin/env python3
"""
Base Job Board Interface
Abstract class for all job board scrapers
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

class JobBoard(ABC):
    """Abstract base class for job board scrapers"""

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    async def search(self, query: str, location: str = "remote", **kwargs) -> List[Dict]:
        """
        Search for jobs on this board

        Args:
            query: Job title or keywords
            location: Location or "remote"
            **kwargs: Additional board-specific parameters

        Returns:
            List of job dictionaries with standardized fields
        """
        pass

    def normalize_job(self, raw_job: Dict) -> Dict:
        """
        Normalize job data to standard format

        Standard fields:
        - id: Unique identifier
        - title: Job title
        - company: Company name
        - location: Job location
        - description: Job description
        - url: Application URL
        - source: Board name
        - date_posted: When posted
        - salary: Salary info (optional)
        - job_type: Full-time, contract, etc (optional)
        """
        job_id = self.generate_job_id(
            raw_job.get('title', ''),
            raw_job.get('company', ''),
            raw_job.get('url', '')
        )

        return {
            'id': job_id,
            'title': raw_job.get('title', '').strip(),
            'company': raw_job.get('company', '').strip(),
            'location': raw_job.get('location', '').strip(),
            'description': raw_job.get('description', '').strip(),
            'url': raw_job.get('url', '').strip(),
            'source': self.name,
            'board': self.name.lower().replace(' ', '-'),
            'date_posted': raw_job.get('date_posted', datetime.now().isoformat()),
            'salary': raw_job.get('salary'),
            'job_type': raw_job.get('job_type'),
            'scraped_at': datetime.now().isoformat()
        }

    def generate_job_id(self, title: str, company: str, url: str) -> str:
        """Generate unique job ID from title, company, URL"""
        unique_string = f"{self.name}:{title}:{company}:{url}"
        return hashlib.md5(unique_string.encode()).hexdigest()[:16]

    @abstractmethod
    def get_board_info(self) -> Dict:
        """Return board metadata (name, capabilities, limits, etc)"""
        pass
