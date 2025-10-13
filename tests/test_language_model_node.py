"""
Test script for the Language Model Node
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

# Import the node class
from langauage_model_node.language_model_node import LanguageModelNode

def test_language_model_node():
    """Test the Language Model Node functionality"""
    
    print("Testing Language Model Node...")
    print("=" * 50)
    
    # Test 1: Register the node
    print("\n1. Registering Language Model Node...")
    register_node(LanguageModelNode)
    print("[OK] Language Model Node registered successfully")
    
    # Test 2: List all nodes
    print("\n2. Listing all registered nodes...")
    nodes = list_nodes()
    print(f"[LIST] Registered nodes: {nodes}")
    
    # Test 3: Get node schema
    print("\n3. Getting Language Model Node schema...")
    schema = get_node_schema("languagemodelnode")
    if schema:
        print("[OK] Schema retrieved successfully")
        print(f"   - Node ID: {schema['node_id']}")
        print(f"   - Inputs: {len(schema['inputs'])}")
        for inp in schema['inputs']:
            print(f"     * {inp['name']} ({inp['type']}): {inp['description']}")
        print(f"   - Outputs: {len(schema['outputs'])}")
        for out in schema['outputs']:
            print(f"     * {out['name']} ({out['type']}): {out['description']}")
        print(f"   - Parameters: {len(schema['parameters'])}")
        for param in schema['parameters']:
            print(f"     * {param['name']} ({param['type']}): {param['description']}")
    else:
        print("[FAIL] Failed to get schema")
    
    # Test 4: Create and test node instance
    print("\n4. Testing Language Model Node execution...")
    lm_node = create_node("languagemodelnode")
    
    if lm_node:
        print("[OK] Language Model Node created successfully")
        
        # Test basic execution
        try:
            result = lm_node.run(
                inputs={
                    "query": "What is artificial intelligence?"
                },
                parameters={
                    "service": "openai",
                    "system_prompt": "You are a helpful AI assistant. Be concise.",
                    "temperature": 0.7,
                    "max_tokens": 200
                }
            )
            
            print("[OK] Language Model Node execution successful")
            print(f"   - Success: {result['success']}")
            print(f"   - Response: {result['response'][:100]}...")
            print(f"   - Metadata: {result['metadata']}")
            
        except Exception as e:
            print(f"[FAIL] Language Model Node execution failed: {e}")
    else:
        print("[FAIL] Failed to create Language Model Node")
    
    # Test 5: Test with different parameters
    print("\n5. Testing with different parameters...")
    if lm_node:
        try:
            result = lm_node.run(
                inputs={
                    "query": "Tell me a short joke"
                },
                parameters={
                    "service": "openai",
                    "system_prompt": "You are a comedian. Be funny and brief.",
                    "temperature": 0.9,  # More creative
                    "max_tokens": 100
                }
            )
            
            print("[OK] Different parameters test successful")
            print(f"   - Response: {result['response']}")
            
        except Exception as e:
            print(f"[FAIL] Different parameters test failed: {e}")
    
    # Test 6: Test error handling
    print("\n6. Testing error handling...")
    if lm_node:
        try:
            # Test with invalid service
            result = lm_node.run(
                inputs={"query": "test"},
                parameters={"service": "invalid_service"}
            )
            print(f"Invalid service test: Success={result['success']}, Error={result['metadata'].get('error', 'No error')}")
            
        except Exception as e:
            print(f"Error handling test exception: {e}")
    
    print("\n" + "=" * 50)
    print("[DONE] Language Model Node testing completed!")


if __name__ == "__main__":
    test_language_model_node()
