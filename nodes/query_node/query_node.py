"""
Query Node - Entry point for user queries in the chatbot workflow.
This node receives user input and passes it through the workflow.
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node and ui_components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter, NodeStyling
from ui_components import (
    NodeUIConfig, UIGroup, DialogConfig,
    create_text_input, create_label, create_button,
    UIOption
)


class QueryNode(BaseNode):
    """
    Query Node - Handles user input queries.
    
    This node serves as the entry point for user queries in the chatbot workflow.
    It receives user input and passes it through to the next nodes in the workflow.
    """
    
    def _define_inputs(self) -> List[NodeInput]:
        """Define the input structure for QueryNode"""
        return []
    
    def _define_outputs(self) -> List[NodeOutput]:
        """Define the output structure for QueryNode"""
        return [
            NodeOutput(
                name="query",
                type="string",
                description="The processed query ready for the next node"
            )
        ]
    
    def _define_parameters(self) -> List[NodeParameter]:
        """Define the parameters for QueryNode"""
        return [
            NodeParameter(
                name="query",
                type="string",
                description="The user's input query or message",
                required=True,
                default_value="Hi there!"
            )
        ]
    
    def _define_styling(self) -> NodeStyling:
        """Define custom styling for QueryNode"""
        return NodeStyling(
            html_template="""
            <div class=\"query-node-container\">
                <div class=\"query-icon\">
                    <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-monitor-down-icon lucide-monitor-down\"><path d=\"M12 13V7\"/><path d=\"m15 10-3 3-3-3\"/><rect width=\"20\" height=\"14\" x=\"2\" y=\"3\" rx=\"2\"/><path d=\"M12 17v4\"/><path d=\"M8 21h8\"/></svg>
                </div>
                <div class=\"query-content\">
                    <div class=\"query-title\">QueryNode</div>
                    <div class=\"query-subtitle\">INPUT</div>
                    <div class=\"query-preview\" title=\"{{query}}\">{{query}}</div>
                </div>
            </div>
            """,
            custom_css="""
            .query-node-container {
                display: flex;
                align-items: center;
                padding: 16px 20px;
                background: #1f1f1f;
                border: 1.5px solid #06b6d4;
                border-radius: 9999px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transition: all 0.2s ease;
                transform-origin: center center;
                width: 220px;
                height: 90px;
                position: relative;
            }
            .query-node-container:hover {
                border-color: #22d3ee;
                box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);
            }
            .query-icon { margin-right: 12px; flex-shrink: 0; color: #06b6d4; display: flex; align-items: center; }
            .query-icon svg { width: 20px; height: 20px; }
            .query-content { flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 2px; }
            .query-title { font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 2px; line-height: 1.2; }
            .query-subtitle { font-size: 11px; color: #06b6d4; opacity: 0.9; line-height: 1.2; }
            .query-preview {
                margin-top: 2px;
                font-size: 11px;
                color: #cbd5e1;
                opacity: 0.9;
                max-width: 160px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }
            """,
            icon="", subtitle="", background_color="#1f1f1f", border_color="#06b6d4", text_color="#ffffff",
            shape="custom", width=220, height=90, css_classes="", inline_styles='{}', icon_position=""
        )
    
    def _define_ui_config(self) -> NodeUIConfig:
        """Define the UI configuration for QueryNode"""
        return NodeUIConfig(
            node_id=self.node_id,
            node_name="QueryNode",
            groups=[
                UIGroup(
                    name="query_config",
                    label="Query Configuration",
                    components=[
                        create_text_input(
                            name="query",
                            label="User Query *",
                            required=True,
                            default_value="Hi there!",
                            placeholder="Enter your query here...",
                            styling={
                                "width": "100%"
                            }
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
                title="Configure QueryNode",
                description="Query Node - Handles user input queries. This node serves as the entry point for user queries in the chatbot workflow. It receives user input and passes it through to the next nodes in the workflow.",
                background_color="#1f1f1f",
                border_color="#60a5fa",
                text_color="#ffffff",
                icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 9h8M8 13h6M6 4h12a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2z" stroke="#60a5fa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>""",
                icon_color="#60a5fa",
                header_background="#1f1f1f",
                footer_background="#1f1f1f",
                button_primary_color="#60a5fa",
                button_secondary_color="#374151"
            )
        )
    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the QueryNode logic
        
        Args:
            inputs: Empty dictionary (no inputs)
            parameters: Dictionary containing 'query'
            
        Returns:
            Dictionary containing the processed 'query'
        """
        query = parameters["query"]
        
        # Simple processing - just clean the query
        processed_query = query.strip()
        
        return {
            "query": processed_query
        }


