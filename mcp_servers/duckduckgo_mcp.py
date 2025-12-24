#!/usr/bin/env python3
"""
DuckDuckGo MCP Server - Web search tool for Messiah
Lightweight MCP server for Termux/Android compatibility
"""

import json
from duckduckgo_search import DDGS

class DuckDuckGoMCP:
    """MCP-style interface for DuckDuckGo search"""

    def __init__(self):
        self.ddgs = DDGS()

    def search(self, query: str, max_results: int = 10) -> list:
        """Search DuckDuckGo and return results"""
        try:
            results = list(self.ddgs.text(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("href", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def search_news(self, query: str, max_results: int = 10) -> list:
        """Search DuckDuckGo News"""
        try:
            results = list(self.ddgs.news(query, max_results=max_results))
            return [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "source": r.get("source", ""),
                    "date": r.get("date", ""),
                    "snippet": r.get("body", "")
                }
                for r in results
            ]
        except Exception as e:
            return [{"error": str(e)}]

    def search_pdfs(self, query: str, max_results: int = 10) -> list:
        """Search specifically for PDF files"""
        pdf_query = f"{query} filetype:pdf"
        return self.search(pdf_query, max_results)

    def search_archive(self, query: str, max_results: int = 10) -> list:
        """Search Internet Archive specifically"""
        archive_query = f"site:archive.org {query}"
        return self.search(archive_query, max_results)


def get_tools():
    """Return MCP tool definitions"""
    return [
        {
            "name": "web_search",
            "description": "Search the web using DuckDuckGo. Returns titles, URLs, and snippets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "news_search",
            "description": "Search DuckDuckGo News for recent articles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "News search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "pdf_search",
            "description": "Search for PDF files on the web.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "PDF search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"}
                },
                "required": ["query"]
            }
        },
        {
            "name": "archive_search",
            "description": "Search Internet Archive (archive.org) for books, documents, media.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Archive search query"},
                    "max_results": {"type": "integer", "description": "Max results (default 10)"}
                },
                "required": ["query"]
            }
        }
    ]


def main():
    """Interactive CLI for testing"""
    print("=" * 50)
    print("DUCKDUCKGO MCP SERVER")
    print("=" * 50)
    print("Commands: search, news, pdf, archive, quit")
    print()

    ddg = DuckDuckGoMCP()

    while True:
        try:
            cmd = input("\nCommand: ").strip().lower()
            if cmd in ['quit', 'exit', 'q']:
                break

            query = input("Query: ").strip()
            if not query:
                continue

            if cmd == 'search':
                results = ddg.search(query)
            elif cmd == 'news':
                results = ddg.search_news(query)
            elif cmd == 'pdf':
                results = ddg.search_pdfs(query)
            elif cmd == 'archive':
                results = ddg.search_archive(query)
            else:
                results = ddg.search(query)

            print(json.dumps(results, indent=2))

        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()
