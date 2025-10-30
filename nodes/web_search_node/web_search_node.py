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
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter, NodeStyling
from ui_components import (
    NodeUIConfig, UIGroup, DialogConfig,
    create_label, create_divider,
    UIOption
)

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

    def _define_styling(self) -> NodeStyling:
        """Define custom styling for WebSearchNode"""
        return NodeStyling(
            html_template="""
            <div class="web-search-node-container">
                <div class="web-search-icon">
                    <svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'>
                        <circle cx='12' cy='12' r='10' stroke='#f59e0b' stroke-width='2' fill='none'/>
                        <path d='M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z' stroke='#f59e0b' stroke-width='2' fill='none'/>
                    </svg>
                </div>
                <div class="web-search-content">
                    <div class="web-search-title">Web Search</div>
                    <div class="web-search-subtitle">Search Engine</div>
                </div>
            </div>
            """,
            custom_css="""
            .web-search-node-container {
                display: flex;
                align-items: center;
                padding: 16px 20px;
                background: #1f1f1f;
                border: 1.5px solid #f59e0b;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transition: all 0.2s ease;
                width: 220px;
                height: 100px;
                position: relative;
            }
            .web-search-node-container:hover {
                border-color: #fbbf24;
                box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);
            }
            .web-search-icon { margin-right: 12px; flex-shrink: 0; }
            .web-search-content { flex: 1; display: flex; flex-direction: column; justify-content: center; }
            .web-search-title { font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 2px; line-height: 1.2; }
            .web-search-subtitle { font-size: 11px; color: #f59e0b; opacity: 0.9; line-height: 1.2; }
            """,
            icon="", subtitle="", background_color="#1f1f1f", border_color="#f59e0b", text_color="#ffffff",
            shape="custom", width=220, height=100, css_classes="", inline_styles='{}', icon_position=""
        )

    def _define_ui_config(self) -> NodeUIConfig:
        """Define the UI configuration for WebSearchNode"""
        return NodeUIConfig(
            node_id=self.node_id,
            node_name="WebSearchNode",
            groups=[
                UIGroup(
                    name="search_settings",
                    label="Search Settings",
                    components=[
                        create_label(
                            text="This node performs web searches and returns results with metadata."
                        )
                    ],
                    styling={
                        "padding": "16px",
                        "background": "#2a2a2a",
                        "border_radius": "8px",
                        "border": "1px solid #404040"
                    }
                )
            ],
            layout="vertical",
            global_styling={
                "font_family": "Inter, sans-serif",
                "color_scheme": "light"
            },
            dialog_config=DialogConfig(
                title="Configure WebSearchNode",
                description="Web Search Node - Performs web searches and returns results with metadata.",
                background_color="#1f1f1f",
                border_color="#f59e0b",
                text_color="#ffffff",
                icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <circle cx="12" cy="12" r="10" stroke="#f59e0b" stroke-width="2" fill="none"/>
                    <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" stroke="#f59e0b" stroke-width="2" fill="none"/>
                </svg>""",
                icon_color="#f59e0b",
                header_background="#1f1f1f",
                footer_background="#1f1f1f",
                button_primary_color="#f59e0b",
                button_secondary_color="#374151"
            )
        )

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


