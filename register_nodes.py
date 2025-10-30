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
from nodes.web_search_node.web_search_node import WebSearchNode
from nodes.knowledge_base_retrieval_node.knowledge_base_retrieval_node import KnowledgeBaseRetrievalNode
from nodes.summary_node.summary_node import SummaryNode
from nodes.conditional_node.conditional_node import ConditionalNode
from nodes.intent_classification_node.intent_classification_node import IntentClassificationNode

# Import the registry
from nodes.node_registry import register_node

def register_all_nodes():
    """Register all available nodes in the system"""
    
    # Register only the nodes that have actual implementations
    register_node(LanguageModelNode)
    register_node(QueryNode)
    register_node(ResponseNode)
    register_node(WebSearchNode)
    register_node(KnowledgeBaseRetrievalNode)
    register_node(SummaryNode)
    register_node(ConditionalNode)
    register_node(IntentClassificationNode)
    
    print("[OK] All nodes registered successfully!")
    from nodes.node_registry import node_registry
    print(f"[DATA] Total registered nodes: {len(node_registry.list_nodes())}")

if __name__ == "__main__":
    register_all_nodes()
