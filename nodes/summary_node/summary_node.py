"""
Summary Node - Summarizes large content by chunking and combining results.

This node handles content of any size by:
1. Splitting content into manageable chunks
2. Summarizing each chunk using a language model
3. Combining summaries in a tree-like structure
4. Providing final consolidated summary

Inputs:
  - content (string): The content to be summarized

Outputs:
  - summary (string): The final summarized content
  - metadata (dict): Information about the summarization process
"""

from typing import Dict, Any, List, Optional
import sys
import os
import re
import math

# Add the parent directory to the path to import base_node
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter, NodeStyling
from ui_components import (
    NodeUIConfig, UIGroup, DialogConfig,
    create_label, create_divider, create_select, create_slider,
    UIOption
)

# Add backend root to path to import language model services
BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

try:
    from language_model_services.openai_service.openai_service import OpenAIService
    from language_model_services.groq_service.groq_service import GroqService
    from language_model_services.ollama_service.ollama_service import OllamaService
except Exception:
    OpenAIService = None
    GroqService = None
    OllamaService = None


class SummaryNode(BaseNode):
    """
    Summary Node - Summarizes large content using chunking and tree-like combination.
    """

    def _define_inputs(self) -> List[NodeInput]:
        return [
            NodeInput(
                name="content",
                type="string",
                description="The content to be summarized",
                required=True,
            )
        ]

    def _define_outputs(self) -> List[NodeOutput]:
        return [
            NodeOutput(
                name="summary",
                type="string",
                description="The final summarized content",
            ),
            NodeOutput(
                name="metadata",
                type="dict",
                description="Metadata about the summarization process including chunk count, levels, etc.",
            ),
        ]

    def _define_parameters(self) -> List[NodeParameter]:
        return [
            NodeParameter(
                name="service",
                type="string",
                description="AI service to use for summarization",
                required=True,
                default_value="openai",
            ),
            NodeParameter(
                name="model",
                type="string",
                description="Language model to use",
                required=True,
                default_value="gpt-3.5-turbo",
            ),
            NodeParameter(
                name="chunk_size",
                type="int",
                description="Maximum size of each chunk in characters",
                required=False,
                default_value=2000,
            ),
            NodeParameter(
                name="summarization_level",
                type="string",
                description="Level of summarization (small, medium, large)",
                required=False,
                default_value="medium",
            ),
            NodeParameter(
                name="max_chunks_per_level",
                type="int",
                description="Maximum number of chunks to combine at each level",
                required=False,
                default_value=5,
            ),
        ]

    def _define_styling(self) -> NodeStyling:
        """Define custom styling for SummaryNode"""
        return NodeStyling(
            html_template="""
            <div class="summary-node-container">
                <div class="summary-icon">
                    <svg width='24' height='24' viewBox='0 0 24 24' fill='none' xmlns='http://www.w3.org/2000/svg'>
                        <path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z' stroke='#06b6d4' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/>
                        <polyline points='14,2 14,8 20,8' stroke='#06b6d4' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/>
                        <line x1='16' y1='13' x2='8' y2='13' stroke='#06b6d4' stroke-width='2' stroke-linecap='round'/>
                        <line x1='16' y1='17' x2='8' y2='17' stroke='#06b6d4' stroke-width='2' stroke-linecap='round'/>
                        <polyline points='10,9 9,9 8,9' stroke='#06b6d4' stroke-width='2' stroke-linecap='round' stroke-linejoin='round' fill='none'/>
                    </svg>
                </div>
                <div class="summary-content">
                    <div class="summary-title">Summary Node</div>
                    <div class="summary-subtitle">Content Summarizer</div>
                </div>
            </div>
            """,
            custom_css="""
            .summary-node-container {
                display: flex;
                align-items: center;
                padding: 16px 20px;
                background: #1f1f1f;
                border: 1.5px solid #06b6d4;
                border-radius: 8px;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transition: all 0.2s ease;
                width: 220px;
                height: 100px;
                position: relative;
            }
            .summary-node-container:hover {
                border-color: #22d3ee;
                box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);
            }
            .summary-icon { margin-right: 12px; flex-shrink: 0; }
            .summary-content { flex: 1; display: flex; flex-direction: column; justify-content: center; }
            .summary-title { font-size: 13px; font-weight: 500; color: #ffffff; margin-bottom: 2px; line-height: 1.2; }
            .summary-subtitle { font-size: 11px; color: #06b6d4; opacity: 0.9; line-height: 1.2; }
            """,
            icon="", subtitle="", background_color="#1f1f1f", border_color="#06b6d4", text_color="#ffffff",
            shape="custom", width=220, height=100, css_classes="", inline_styles='{}', icon_position=""
        )

    def _define_ui_config(self) -> NodeUIConfig:
        """Define the UI configuration for SummaryNode"""
        return NodeUIConfig(
            node_id=self.node_id,
            node_name="SummaryNode",
            groups=[
                UIGroup(
                    name="model_settings",
                    label="Model Settings",
                    components=[
                        create_label(
                            text="<strong>AI Service:</strong>"
                        ),
                        create_select(
                            name="service",
                            label="Service",
                            options=[
                                UIOption(value="openai", label="OpenAI"),
                                UIOption(value="groq", label="Groq"),
                                UIOption(value="ollama", label="Ollama"),
                            ],
                            required=True,
                            default_value="openai"
                        ),
                        create_select(
                            name="model",
                            label="Model",
                            options=[
                                UIOption(value="gpt-3.5-turbo", label="GPT-3.5 Turbo"),
                                UIOption(value="gpt-4o", label="GPT-4o"),
                                UIOption(value="gpt-4o-mini", label="GPT-4o Mini"),
                            ],
                            required=True,
                            default_value="gpt-3.5-turbo"
                        ),
                    ],
                    styling={
                        "padding": "16px",
                        "background": "#2a2a2a",
                        "border_radius": "8px",
                        "border": "1px solid #404040"
                    }
                ),
                UIGroup(
                    name="summarization_settings",
                    label="Summarization Settings",
                    components=[
                        create_label(
                            text="<strong>Chunk Size:</strong>"
                        ),
                        create_slider(
                            name="chunk_size",
                            label="Characters per chunk",
                            min_value=1000,
                            max_value=4000,
                            step=500,
                            default_value=2000,
                            show_value=True
                        ),
                        create_label(
                            text="<strong>Summarization Level:</strong>"
                        ),
                        create_select(
                            name="summarization_level",
                            label="Level",
                            options=[
                                UIOption(value="small", label="Small (Brief)"),
                                UIOption(value="medium", label="Medium (Balanced)"),
                                UIOption(value="large", label="Large (Detailed)"),
                            ],
                            required=True,
                            default_value="medium"
                        ),
                        create_label(
                            text="<strong>Max Chunks per Level:</strong>"
                        ),
                        create_slider(
                            name="max_chunks_per_level",
                            label="Chunks to combine",
                            min_value=3,
                            max_value=10,
                            step=1,
                            default_value=5,
                            show_value=True
                        ),
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
                title="Configure SummaryNode",
                description="Summary Node - Summarizes large content using chunking and tree-like combination.",
                background_color="#1f1f1f",
                border_color="#06b6d4",
                text_color="#ffffff",
                icon="""<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    <polyline points="14,2 14,8 20,8" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                    <line x1="16" y1="13" x2="8" y2="13" stroke="#06b6d4" stroke-width="2" stroke-linecap="round"/>
                    <line x1="16" y1="17" x2="8" y2="17" stroke="#06b6d4" stroke-width="2" stroke-linecap="round"/>
                    <polyline points="10,9 9,9 8,9" stroke="#06b6d4" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="none"/>
                </svg>""",
                icon_color="#06b6d4",
                header_background="#1f1f1f",
                footer_background="#1f1f1f",
                button_primary_color="#06b6d4",
                button_secondary_color="#374151"
            )
        )

    def _get_language_model_service(self, service: str):
        """Get the appropriate language model service"""
        if service == "openai" and OpenAIService:
            return OpenAIService()
        elif service == "groq" and GroqService:
            return GroqService()
        elif service == "ollama" and OllamaService:
            return OllamaService()
        else:
            raise ValueError(f"Unsupported service: {service}")

    def _get_summarization_prompt(self, level: str) -> str:
        """Get the appropriate prompt based on summarization level"""
        prompts = {
            "small": "Provide a brief summary of the following content. Focus on the main points only. Keep it concise and to the point.",
            "medium": "Provide a balanced summary of the following content. Include key points and important details while maintaining clarity.",
            "large": "Provide a detailed summary of the following content. Include comprehensive information while maintaining organization and readability."
        }
        return prompts.get(level, prompts["medium"])

    def _split_content_into_chunks(self, content: str, chunk_size: int) -> List[str]:
        """Split content into chunks of specified size"""
        if len(content) <= chunk_size:
            return [content]
        
        chunks = []
        # Try to split at sentence boundaries first
        sentences = re.split(r'(?<=[.!?])\s+', content)
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= chunk_size:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    def _summarize_chunk(self, chunk: str, service: str, model: str, level: str) -> str:
        """Summarize a single chunk using the language model"""
        try:
            lm_service = self._get_language_model_service(service)
            prompt = self._get_summarization_prompt(level)
            
            full_prompt = f"{prompt}\n\nContent:\n{chunk}"
            
            response = lm_service.generate(
                model_name=model,
                query=full_prompt,
                temperature=0.3,  # Lower temperature for more consistent summaries
                max_tokens=1000
            )
            
            return response.strip()
        except Exception as e:
            return f"Error summarizing chunk: {str(e)}"

    def _combine_summaries(self, summaries: List[str], service: str, model: str, level: str) -> str:
        """Combine multiple summaries into a single summary"""
        if len(summaries) == 1:
            return summaries[0]
        
        combined_content = "\n\n".join([f"Summary {i+1}:\n{summary}" for i, summary in enumerate(summaries)])
        
        prompt = f"""Combine the following summaries into a single, coherent summary. 
        Maintain the key information from all summaries while creating a unified narrative.
        
        Summaries to combine:
        {combined_content}
        
        Provide a single, well-structured summary that captures the essence of all the individual summaries."""
        
        try:
            lm_service = self._get_language_model_service(service)
            response = lm_service.generate(
                model_name=model,
                query=prompt,
                temperature=0.3,
                max_tokens=1500
            )
            return response.strip()
        except Exception as e:
            return f"Error combining summaries: {str(e)}"

    def _summarize_tree_structure(self, chunks: List[str], service: str, model: str, level: str, max_chunks_per_level: int) -> Dict[str, Any]:
        """Create a tree-like summarization structure"""
        if not chunks:
            return {"summary": "", "metadata": {"error": "No content to summarize"}}
        
        if len(chunks) == 1:
            summary = self._summarize_chunk(chunks[0], service, model, level)
            return {
                "summary": summary,
                "metadata": {
                    "chunk_count": 1,
                    "levels": 1,
                    "total_chunks_processed": 1
                }
            }
        
        current_level = chunks
        level_summaries = []
        total_chunks_processed = len(chunks)
        levels = 0
        
        while len(current_level) > 1:
            levels += 1
            level_summaries = []
            
            # Process chunks in groups
            for i in range(0, len(current_level), max_chunks_per_level):
                group = current_level[i:i + max_chunks_per_level]
                
                if len(group) == 1:
                    summary = self._summarize_chunk(group[0], service, model, level)
                else:
                    # First summarize each chunk in the group
                    chunk_summaries = [self._summarize_chunk(chunk, service, model, level) for chunk in group]
                    # Then combine the summaries
                    summary = self._combine_summaries(chunk_summaries, service, model, level)
                
                level_summaries.append(summary)
            
            current_level = level_summaries
        
        final_summary = current_level[0] if current_level else ""
        
        return {
            "summary": final_summary,
            "metadata": {
                "chunk_count": len(chunks),
                "levels": levels,
                "total_chunks_processed": total_chunks_processed,
                "final_summary_length": len(final_summary)
            }
        }

    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the SummaryNode logic
        """
        content = inputs.get("content", "").strip()
        
        if not content:
            return {
                "summary": "",
                "metadata": {
                    "error": "No content provided for summarization",
                    "chunk_count": 0,
                    "levels": 0
                }
            }
        
        # Get parameters
        service = parameters.get("service", "openai")
        model = parameters.get("model", "gpt-3.5-turbo")
        chunk_size = parameters.get("chunk_size", 2000)
        level = parameters.get("summarization_level", "medium")
        max_chunks_per_level = parameters.get("max_chunks_per_level", 5)
        
        try:
            # Split content into chunks
            chunks = self._split_content_into_chunks(content, chunk_size)
            
            # Perform tree-like summarization
            result = self._summarize_tree_structure(chunks, service, model, level, max_chunks_per_level)
            
            return result
            
        except Exception as e:
            return {
                "summary": f"Error during summarization: {str(e)}",
                "metadata": {
                    "error": str(e),
                    "chunk_count": 0,
                    "levels": 0
                }
            }
