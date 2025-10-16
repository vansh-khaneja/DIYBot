"""
Tavily Web Search Tool

Provides a simple interface to perform web searches using the Tavily API
and returns results along with URLs as metadata.
"""

import os
from typing import Any, Dict, List, Optional


class WebSearchTool:
    """
    Simple web search tool backed by Tavily.

    Reads the API key from the environment variable `TAVILY_API_KEY`.
    If the official client is unavailable, falls back to direct HTTP requests.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key: Optional[str] = api_key or os.getenv("TAVILY_API_KEY")
        self._client = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize or reinitialize the Tavily client with current API key"""
        current_api_key = os.getenv("TAVILY_API_KEY")
        if current_api_key != self.api_key:
            self.api_key = current_api_key
            self._client = None
            
        # Attempt to initialize official Tavily client if available
        try:
            if self.api_key:
                from tavily import TavilyClient  # type: ignore
                self._client = TavilyClient(api_key=self.api_key)
        except Exception:
            # Silently ignore; we'll fall back to requests
            self._client = None

    def search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Perform a web search and return structured results with URL metadata.

        Args:
            query: The search query string
            max_results: Maximum number of results to return (Tavily default caps may apply)

        Returns:
            A dictionary with keys:
              - success: bool
              - results: list of {title, url, content}
              - metadata: {provider, results_count, source_urls}
              - error: optional error message when success is False
        """
        # Reinitialize client if API key has changed
        self._initialize_client()
        
        if not self.api_key:
            return {
                "success": False,
                "results": [],
                "metadata": {},
                "error": "Missing TAVILY_API_KEY in environment",
            }

        try:
            if self._client is not None:
                # Use official client
                response = self._client.search(
                    query=query,
                    max_results=max_results,
                    include_answer=False,
                    include_raw_content=False,
                )
                raw_results = response.get("results", [])
            else:
                # Fallback to HTTP API
                import requests

                url = "https://api.tavily.com/search"
                payload = {
                    "api_key": self.api_key,
                    "query": query,
                    "max_results": max_results,
                    "include_answer": False,
                    "include_raw_content": False,
                }
                r = requests.post(url, json=payload, timeout=30)
                r.raise_for_status()
                data = r.json()
                raw_results = data.get("results", [])

            results: List[Dict[str, str]] = []
            for item in raw_results[:max_results]:
                title = item.get("title") or ""
                url = item.get("url") or ""
                content = item.get("content") or item.get("snippet") or ""
                # Normalize result schema
                results.append({"title": title, "url": url, "content": content})

            return {
                "success": True,
                "results": results,
                "metadata": {
                    "provider": "tavily",
                    "results_count": len(results),
                    "source_urls": [r["url"] for r in results],
                },
            }
        except Exception as e:
            return {
                "success": False,
                "results": [],
                "metadata": {},
                "error": str(e),
            }


def web_search(query: str, max_results: int = 5) -> Dict[str, Any]:
    """Convenience function for quick searches."""
    tool = WebSearchTool()
    return tool.search(query=query, max_results=max_results)


