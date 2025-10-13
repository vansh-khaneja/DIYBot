"""
Test script for all refactored nodes
"""

import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'nodes'))

# Import the registry functions
from node_registry import register_node, create_node, list_nodes, get_node_schema

# Import all node classes
from query_node.query_node import QueryNode
from response_node.response_node import ResponseNode
from langauage_model_node.language_model_node import LanguageModelNode

def test_all_refactored_nodes():
    """Test all refactored nodes functionality"""
    
    print("Testing All Refactored Nodes...")
    print("=" * 60)
    
    # Register all nodes
    print("\n1. Registering all nodes...")
    register_node(QueryNode)
    register_node(ResponseNode)
    register_node(LanguageModelNode)
    print("[OK] All nodes registered successfully")
    
    # List all nodes
    print("\n2. Listing all registered nodes...")
    nodes = list_nodes()
    print(f"[LIST] Registered nodes: {nodes}")
    
    # Show schemas for all nodes
    print("\n3. Node Schemas:")
    for node_name in nodes:
        schema = get_node_schema(node_name)
        if schema:
            print(f"\n[ITEM] {schema['name']} ({schema['node_id']}):")
            print(f"   Inputs: {len(schema['inputs'])}")
            for inp in schema['inputs']:
                print(f"      {inp['name']} ({inp['type']}): {inp['description']}")
            print(f"   Outputs: {len(schema['outputs'])}")
            for out in schema['outputs']:
                print(f"      {out['name']} ({out['type']}): {out['description']}")
            print(f"   Parameters: {len(schema['parameters'])}")
            for param in schema['parameters']:
                print(f"      {param['name']} ({param['type']}): {param['description']}")
    
    # Test QueryNode
    print("\n4. Testing QueryNode...")
    query_node = create_node("querynode")
    if query_node:
        try:
            result = query_node.run(
                inputs={},
                parameters={
                    "query": "  HELLO WORLD  "
                }
            )
            print(f"[OK] QueryNode: {result['query']}")
        except Exception as e:
            print(f"[FAIL] QueryNode error: {e}")
    
    # Test LanguageModelNode
    print("\n5. Testing LanguageModelNode...")
    lm_node = create_node("languagemodelnode")
    if lm_node:
        try:
            result = lm_node.run(
                inputs={
                    "query": "What is Python programming?"
                },
                parameters={
                    "service": "openai",
                    "system_prompt": "You are a programming tutor. Explain simply.",
                    "temperature": 0.5,
                    "max_tokens": 150
                }
            )
            print(f"[OK] LanguageModelNode: {result['response'][:100]}...")
        except Exception as e:
            print(f"[FAIL] LanguageModelNode error: {e}")
    
    # Test ResponseNode
    print("\n6. Testing ResponseNode...")
    response_node = create_node("responsenode")
    if response_node:
        try:
            result = response_node.run(
                inputs={
                    "response_data": "Python is a programming language that is easy to learn and powerful.",
                    "metadata": {"source": "AI", "confidence": 0.95}
                },
                parameters={}
            )
            print(f"[OK] ResponseNode: Processed response successfully")
        except Exception as e:
            print(f"[FAIL] ResponseNode error: {e}")
    
    # Test workflow simulation
    print("\n7. Testing Workflow Simulation...")
    try:
        # Step 1: Process query
        query_result = query_node.run(
            inputs={},
            parameters={"query": "Explain machine learning"}
        )
        
        # Step 2: Generate AI response
        lm_result = lm_node.run(
            inputs={
                "query": query_result["query"]
            },
            parameters={
                "service": "openai",
                "system_prompt": "You are an AI educator. Be clear and helpful.",
                "temperature": 0.7,
                "max_tokens": 200
            }
        )
        
        # Step 3: Process response
        response_result = response_node.run(
            inputs={
                "response_data": lm_result["response"],
                "metadata": lm_result["metadata"]
            },
            parameters={}
        )
        
        print("[OK] Workflow simulation successful!")
        print(f"Final response processed successfully")
        
    except Exception as e:
        print(f"[FAIL] Workflow simulation error: {e}")
    
    print("\n" + "=" * 60)
    print("[DONE] All refactored nodes testing completed!")


if __name__ == "__main__":
    test_all_refactored_nodes()
