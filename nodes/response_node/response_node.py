"""
Response Node - Final output node for chatbot responses.
This node formats and returns the final response to the user.
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter


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
                name="response_data",
                type="string",
                description="The processed response data from previous nodes",
                required=True
            ),
            NodeInput(
                name="metadata",
                type="dict",
                description="Additional metadata for the response (optional)",
                required=False,
                default_value={}
            )
        ]
    
    def _define_outputs(self) -> List[NodeOutput]:
        """Define the output structure for ResponseNode"""
        return []
    
    def _define_parameters(self) -> List[NodeParameter]:
        """Define the parameters for ResponseNode"""
        return []
    
    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the ResponseNode logic
        
        Args:
            inputs: Dictionary containing 'response_data' and optional 'metadata'
            parameters: Empty dictionary (no parameters)
            
        Returns:
            Empty dictionary (no outputs)
        """
        response_data = inputs["response_data"]
        metadata = inputs.get("metadata", {})
        
        # Simple processing - just return the response data as-is
        # In a real implementation, this might print, save, or send the response
        
        return {}

