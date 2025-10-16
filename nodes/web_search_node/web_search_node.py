"""
Web Search Node - Uses Tavily-backed WebSearchTool to fetch results.

Inputs:
  - query (string): search query

Outputs:
  - response (string): textual aggregation of search results
  - metadata (dict): includes 'urls' (list[str]) and provider info
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter

# Add backend root to path to import tools
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

try:
    from tools.web_search_tool.web_search_tool import WebSearchTool
except Exception:
    WebSearchTool = None  # type: ignore


class WebSearchNode(BaseNode):
    """
    Web Search Node - Performs a web search and outputs results with URL metadata.
    """

    def _define_inputs(self) -> List[NodeInput]:
        return [
            NodeInput(
                name="query",
                type="string",
                description="The search query to execute",
                required=True,
            )
        ]

    def _define_outputs(self) -> List[NodeOutput]:
        return [
            NodeOutput(
                name="response",
                type="string",
                description="Textual aggregation of the top search results",
            ),
            NodeOutput(
                name="metadata",
                type="dict",
                description="Metadata including list of URLs under key 'urls'",
            ),
        ]

    def _define_parameters(self) -> List[NodeParameter]:
        return [
            NodeParameter(
                name="max_results",
                type="int",
                description="Maximum number of results to retrieve",
                required=False,
                default_value=5,
            )
        ]

    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        query: str = inputs["query"]
        max_results: int = parameters.get("max_results", 5)

        if not WebSearchTool:
            return {
                "response": "",
                "metadata": {
                    "error": "WebSearchTool unavailable",
                    "urls": [],
                },
            }

        tool = WebSearchTool()
        result = tool.search(query=query, max_results=max_results)

        if not result.get("success"):
            return {
                "response": "",
                "metadata": {
                    "error": result.get("error", "unknown error"),
                    "urls": [],
                },
            }

        items: List[Dict[str, Any]] = result.get("results", [])
        urls: List[str] = [item.get("url", "") for item in items if item.get("url")]

        # Build a simple textual aggregation of results
        lines: List[str] = []
        for item in items:
            title = item.get("title") or "Untitled"
            url = item.get("url") or ""
            content = item.get("content") or ""
            lines.append(f"- {title}\n  {url}\n  {content}")

        response_text = "\n\n".join(lines)

        metadata: Dict[str, Any] = {
            "provider": result.get("metadata", {}).get("provider", "tavily"),
            "results_count": result.get("metadata", {}).get("results_count", len(items)),
            "urls": urls,
        }

        return {
            "response": response_text,
            "metadata": metadata,
        }


