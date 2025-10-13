"""
Query Node - Entry point for user queries in the chatbot workflow.
This node receives user input and passes it through the workflow.
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter


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
                required=True
            )
        ]
    
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


