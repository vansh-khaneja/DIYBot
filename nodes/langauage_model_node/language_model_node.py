"""
Language Model Node - Uses the language model tool to generate responses.
This node takes a query and generates AI responses using various language models.
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tools', 'language_model_tool'))

from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter

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
                description="The text query to send to the language model",
                required=True
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
            NodeOutput(
                name="metadata",
                type="dict",
                description="Metadata about the generation (service, model, lengths, etc.)"
            ),
            NodeOutput(
                name="success",
                type="boolean",
                description="Whether the generation was successful"
            )
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
            query = inputs["query"]
            
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
                query=query,
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
                    "metadata": result.get("metadata", {}),
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