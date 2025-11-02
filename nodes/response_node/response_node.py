"""
Response Node - Final output node for chatbot responses.
This node formats and returns the final response to the user.
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node and ui_components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter, NodeStyling
from ui_components import (
    NodeUIConfig, UIGroup, DialogConfig,
    create_label, create_divider,
    UIOption
)


class ResponseNode(BaseNode):
    """
    Response Node - Handles final response formatting and output.
    
    This node serves as the final output point for chatbot responses.
    It receives processed data from previous nodes and formats it into
    a user-friendly response.
    """
    
    def _define_inputs(self) -> List[NodeInput]:
        """Define the input structure for ResponseNode"""
        return [
            NodeInput(
                name="input_data",
                type="string",
                description="Combined input data from multiple connections (user query, knowledge base response, etc.)",
                required=True
            )
        ]
    
    def _define_outputs(self) -> List[NodeOutput]:
        """Define the output structure for ResponseNode"""
        return [
            NodeOutput(
                name="final_response",
                type="string",
                description="The final processed response that will be displayed"
            )
        ]
    
    def _define_parameters(self) -> List[NodeParameter]:
        """Define the parameters for ResponseNode"""
        return []
    
    def _define_styling(self) -> NodeStyling:
        """Define custom styling for ResponseNode"""
        return NodeStyling(
            html_template="""
            <div class="response-node-container">
                <div class="response-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="lucide lucide-monitor-up-icon lucide-monitor-up"><path d="m9 10 3-3 3 3"/><path d="M12 13V7"/><rect width="20" height="14" x="2" y="3" rx="2"/><path d="M12 17v4"/><path d="M8 21h8"/></svg>
                </div>
                <div class="response-content">
                    <div class="response-title">ResponseNode</div>
                    <div class="response-subtitle">OUTPUT</div>
                    <div class="response-preview" title="{{response_content}}">{{response_content}}</div>
                </div>
            </div>
            """,
            custom_css="""
            .response-node-container {
                display: flex;
                align-items: center;
                padding: 16px 20px;
                background: #1f1f1f;
                border: 1.5px solid #10b981;
                border-radius: 9999px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transition: all 0.2s ease;
                transform-origin: center center;
                width: 220px;
                height: 90px;
                position: relative;
            }
            .response-node-container:hover {
                border-color: #34d399;
                box-shadow: 0 4px 12px rgba(16, 185, 129, 0.2);
            }
            .response-icon { margin-right: 12px; flex-shrink: 0; color: #10b981; display: flex; align-items: center; }
            .response-icon svg { width: 20px; height: 20px; }
            .response-content { flex: 1; display: flex; flex-direction: column; justify-content: center; gap: 2px; }
            .response-title { font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 2px; line-height: 1.2; }
            .response-subtitle { font-size: 11px; color: #10b981; opacity: 0.9; line-height: 1.2; }
            .response-preview {
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
            icon="", subtitle="", background_color="#1f1f1f", border_color="#10b981", text_color="#ffffff",
            shape="custom", width=220, height=90, css_classes="", inline_styles='{}', icon_position="",
            hide_outputs=True  # Response node is terminal - hide output handles
        )
    
    def _define_ui_config(self) -> NodeUIConfig:
        """Define the UI configuration for ResponseNode"""
        return NodeUIConfig(
            node_id=self.node_id,
            node_name="ResponseNode",
            groups=[
                UIGroup(
                    name="response_display",
                    label="Response Display",
                    components=[
                        create_label(
                            text="This node displays the final response from your workflow."
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
                title="Configure ResponseNode",
                description="Response Node - Displays the final response from your workflow.",
                background_color="#1f1f1f",
                border_color="#10b981",
                text_color="#ffffff",
                icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" stroke="#10b981" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>""",
                icon_color="#10b981",
                header_background="#1f1f1f",
                footer_background="#1f1f1f",
                button_primary_color="#10b981",
                button_secondary_color="#374151"
            )
        )
    
    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the ResponseNode logic
        
        Args:
            inputs: Dictionary containing 'input_data' (automatically combined from multiple connections)
            parameters: Empty dictionary (no parameters)
            
        Returns:
            Dictionary containing final_response and response_content for display
        """
        raw_input = inputs.get("input_data", "")
        # Be tolerant to non-string inputs (e.g., booleans from routing nodes)
        input_data = (raw_input if isinstance(raw_input, str) else str(raw_input)).strip()
        
        # Process the combined input data
        if input_data:
            # Check if it's already formatted as "Combined inputs:"
            if input_data.startswith("Combined inputs:"):
                # Extract the actual content
                content = input_data.replace("Combined inputs:", "").strip()
                final_response = content
                response_content = content
            else:
                # Single input or already processed
                final_response = input_data
                response_content = input_data
        else:
            # No input received
            final_response = "No response yet"
            response_content = "No response yet"
        
        # Store the response content in the node's data for display in the HTML template
        self.node_data = {
            "response_content": response_content
        }
        
        # Return the response as output for inline display
        return {
            "final_response": final_response,
            "response_content": response_content
        }

