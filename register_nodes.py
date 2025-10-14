"""
Startup script to register all available nodes
"""

import sys
import os

# Add the project root to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# Import all node classes (only the ones that actually exist)
from nodes.langauage_model_node.language_model_node import LanguageModelNode
from nodes.query_node.query_node import QueryNode
from nodes.response_node.response_node import ResponseNode

# Import the registry
from nodes.node_registry import register_node

def register_all_nodes():
    """Register all available nodes in the system"""
    
    # Register only the nodes that have actual implementations
    register_node(LanguageModelNode)
    register_node(QueryNode)
    register_node(ResponseNode)
    
    print("[OK] All nodes registered successfully!")
    from nodes.node_registry import node_registry
    print(f"[DATA] Total registered nodes: {len(node_registry.list_nodes())}")

if __name__ == "__main__":
    register_all_nodes()
