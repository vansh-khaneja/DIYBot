"""
Language Model Node - Uses the language model tool to generate responses.
This node takes a query and generates AI responses using various language models.
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node and ui_components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tools', 'language_model_tool'))

from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter, NodeStyling
from ui_components import (
    NodeUIConfig, UIGroup, DialogConfig,
    create_select, create_textarea, create_number_input, create_slider,
    create_toggle, create_label, create_divider, UIOption
)

try:
    from language_model_tool import LanguageModelTool
except ImportError:
    LanguageModelTool = None


class LanguageModelNode(BaseNode):
    """
    Language Model Node - Generates AI responses using language models.
    
    This node takes a query and optional context, then uses a configured
    language model service to generate a response.
    """
    
    def _define_inputs(self) -> List[NodeInput]:
        """Define the input structure for LanguageModelNode"""
        return [
            NodeInput(
                name="query",
                type="string",
                description="The main text query to send to the language model",
                required=True
            ),
            NodeInput(
                name="context",
                type="string",
                description="Additional context from knowledge base or other sources",
                required=False
            )
        ]
    
    def _define_outputs(self) -> List[NodeOutput]:
        """Define the output structure for LanguageModelNode"""
        return [
            NodeOutput(
                name="response",
                type="string",
                description="The generated response from the language model"
            ),
           
        ]
    
    def _define_parameters(self) -> List[NodeParameter]:
        """Define the parameters for LanguageModelNode"""
        return [
            NodeParameter(
                name="service",
                type="string",
                description="Language model service to use",
                required=True,
                default_value="openai",
                options=["openai", "groq", "ollama"]
            ),
            NodeParameter(
                name="model",
                type="string",
                description="Specific model to use (leave empty for default)",
                required=False,
                default_value=""
            ),
            NodeParameter(
                name="system_prompt",
                type="string",
                description="System/base prompt to set AI behavior",
                required=False,
                default_value="You are a helpful AI assistant."
            ),
            NodeParameter(
                name="temperature",
                type="float",
                description="Creativity/randomness level (0.0 to 1.0)",
                required=False,
                default_value=0.7
            ),
            NodeParameter(
                name="max_tokens",
                type="integer",
                description="Maximum number of tokens in response",
                required=False,
                default_value=500
            ),
        ]
    
    def _define_styling(self) -> NodeStyling:
        """Define custom styling for LanguageModelNode"""
        return NodeStyling(
            # Custom HTML template - everything rendered from HTML/CSS
            html_template="""
            <div class="ai-node-container">
                <div class="ai-icon">
                    <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M12 18V5"/>
                        <path d="M15 13a4.17 4.17 0 0 1-3-4 4.17 4.17 0 0 1-3 4"/>
                        <path d="M17.598 6.5A3 3 0 1 0 12 5a3 3 0 1 0-5.598 1.5"/>
                        <path d="M17.997 5.125a4 4 0 0 1 2.526 5.77"/>
                        <path d="M18 18a4 4 0 0 0 2-7.464"/>
                        <path d="M19.967 17.483A4 4 0 1 1 12 18a4 4 0 1 1-7.967-.517"/>
                        <path d="M6 18a4 4 0 0 1-2-7.464"/>
                        <path d="M6.003 5.125a4 4 0 0 0-2.526 5.77"/>
                    </svg>
                </div>
                <div class="ai-content">
                    <div class="ai-title">Language Model</div>
                    <div class="ai-subtitle">AI Brain</div>
                </div>
            </div>
            """,
            
            # Complete CSS styling - no computation needed
            custom_css="""
            .ai-node-container {
                display: flex;
                align-items: center;
                padding: 16px 20px;
                background: #1f1f1f;
                border: 1.5px solid #a78bfa;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transition: all 0.2s ease;
                width: 220px;
                height: 100px;
                position: relative;
            }
            
            .ai-node-container:hover {
                border-color: #c4b5fd;
                box-shadow: 0 4px 12px rgba(167, 139, 250, 0.2);
            }
            
            .ai-icon {
                margin-right: 12px;
                flex-shrink: 0;
            }
            
            .ai-content {
                flex: 1;
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            
            .ai-title {
                font-size: 13px;
                font-weight: 500;
                color: #ffffff;
                margin-bottom: 2px;
                line-height: 1.2;
            }
            
            .ai-subtitle {
                font-size: 11px;
                color: #a78bfa;
                opacity: 0.9;
                line-height: 1.2;
            }
            """,
            
            # No icon, subtitle, or other properties needed - everything in HTML
            icon="",
            subtitle="",
            background_color="#1f1f1f",
            border_color="#a78bfa",
            text_color="#ffffff",
            shape="custom",
            width=220,
            height=100,
            css_classes="",
            inline_styles='{}',
            icon_position=""
        )
    
    def _define_ui_config(self) -> NodeUIConfig:
        """Define the UI configuration for LanguageModelNode"""
        return NodeUIConfig(
            node_id=self.node_id,
            node_name="LanguageModelNode",
            groups=[
                UIGroup(
                    name="model_config",
                    label="Model Configuration",
                    components=[
                        create_select(
                            name="service",
                            label="AI Service *",
                            required=True,
                            default_value="openai",
                            options=[
                                UIOption(value="openai", label="OpenAI"),
                                UIOption(value="groq", label="Groq"),
                                UIOption(value="ollama", label="Ollama")
                            ],
                            searchable=True
                        ),
                        create_select(
                            name="model",
                            label="Model *",
                            required=True,
                            default_value="",
                            options=[
                                UIOption(value="", label="Select a service first")
                            ],
                            searchable=True
                        )
                    ],
                    styling={
                        "padding": "16px",
                        "background": "#2a2a2a",
                        "border_radius": "8px",
                        "border": "1px solid #404040"
                    }
                ),
                UIGroup(
                    name="generation_config",
                    label="Generation Settings",
                    components=[
                        create_slider(
                            name="temperature",
                            label="Temperature",
                            required=False,
                            default_value=0.7,
                            min_value=0.0,
                            max_value=2.0,
                            step=0.1,
                            show_value=True
                        ),
                        create_number_input(
                            name="max_tokens",
                            label="Max Tokens",
                            required=False,
                            default_value=500,
                            min_value=1,
                            max_value=4000,
                            step=1
                        )
                    ],
                    styling={
                        "padding": "16px",
                        "background": "#2a2a2a",
                        "border_radius": "8px",
                        "border": "1px solid #404040"
                    }
                ),
                UIGroup(
                    name="advanced_config",
                    label="Advanced Settings",
                    components=[
                        create_textarea(
                            name="system_prompt",
                            label="System Prompt",
                            required=False,
                            default_value="",
                            placeholder="Enter a custom system prompt...",
                            rows=3
                        )
                    ],
                    collapsible=True,
                    collapsed=True,
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
                title="Configure LanguageModelNode",
                description="Language Model Node - Generates AI responses using language models. This node takes a query and optional context, then uses a configured language model service to generate a response.",
                background_color="#1f1f1f",
                border_color="#a78bfa",
                text_color="#ffffff",
                icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 18V5M15 13a4.17 4.17 0 01-3-4 4.17 4.17 0 01-3 4M17.598 6.5A3 3 0 100 5a3 3 0 105.598 1.5M17.997 5.125a4 4 0 012.526 5.77M18 18a4 4 0 002-7.464M19.967 17.483A4 4 0 1112 18a4 4 0 11-7.967-.517M6 18a4 4 0 01-2-7.464M6.003 5.125a4 4 0 00-2.526 5.77" stroke="#a78bfa" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>""",
                icon_color="#a78bfa",
                header_background="#1f1f1f",
                footer_background="#1f1f1f",
                button_primary_color="#a78bfa",
                button_secondary_color="#374151"
            )
        )
    
    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the LanguageModelNode logic
        
        Args:
            inputs: Dictionary containing 'query'
            parameters: Dictionary containing service settings and system_prompt
            
        Returns:
            Dictionary containing 'response', 'metadata', and 'success'
        """
        # Check if language model tool is available
        if LanguageModelTool is None:
            return {
                "response": "",
                "metadata": {"error": "Language model tool not available"},
                "success": False
            }
        
        try:
            # Extract inputs
            query = inputs.get("query", "").strip()
            context = inputs.get("context", "").strip()
            
            # Combine query and context intelligently
            if context and query:
                # If both are provided, create a comprehensive prompt
                combined_query = f"""Based on the following context, please answer the user's question:

Context:
{context}

User Question: {query}

Please provide a helpful and accurate response based on the context provided."""
            elif context:
                # If only context is provided, use it as the query
                combined_query = context
            else:
                # If only query is provided, use it as is
                combined_query = query
            
            # Extract parameters
            service = parameters.get("service", "openai")
            model = parameters.get("model", "")
            system_prompt = parameters.get("system_prompt", "You are a helpful AI assistant.")
            temperature = parameters.get("temperature", 0.7)
            max_tokens = parameters.get("max_tokens", 500)
            
            # Initialize the language model tool
            lm_tool = LanguageModelTool()
            
            # Generate response
            result = lm_tool.generate_response(
                query=combined_query,
                service=service,
                model=model if model else None,
                system_prompt=system_prompt if system_prompt else None,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Return results
            if result["success"]:
                return {
                    "response": result["response"],
                    "metadata": {
                        "success": True,
                        "service": result["metadata"]["service"],
                        "model": result["metadata"]["model"],
                        "query_length": len(query),
                        "context_length": len(context),
                        "combined_length": len(combined_query),
                        "input_combination": "query_and_context" if context and query else ("context_only" if context else "query_only"),
                        "response_length": result["metadata"]["response_length"]
                    },
                    "success": True
                }
            else:
                return {
                    "response": "",
                    "metadata": {"error": result.get("error", "Unknown error")},
                    "success": False
                }
                
        except Exception as e:
            return {
                "response": "",
                "metadata": {"error": str(e)},
                "success": False
            }