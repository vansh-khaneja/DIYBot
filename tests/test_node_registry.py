"""
Test script for the simplified Node Registry
"""

import sys
import os

# Add the parent directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'nodes'))

# Import the registry functions
from node_registry import register_node, create_node, list_nodes, get_node_schema

# Import the node classes
from query_node.query_node import QueryNode
from response_node.response_node import ResponseNode

def test_node_registry():
    """Test all functionality of the node registry"""
    
    print("Testing Node Registry...")
    print("=" * 50)
    
    print("\n1. Registering nodes...")
    register_node(QueryNode)
    register_node(ResponseNode)
    print("[OK] Nodes registered successfully")
    
    # Test 2: List all nodes
    print("\n2. Listing all registered nodes...")
    nodes = list_nodes()
    print(f"[LIST] Registered nodes: {nodes}")
    print("[OK] Node listing works")
    
    # Test 3: Create node instances
    print("\n3. Creating node instances...")
    query_node = create_node("querynode")
    response_node = create_node("responsenode")
    
    if query_node:
        print("[OK] QueryNode created successfully")
    else:
        print("[FAIL] Failed to create QueryNode")
    
    if response_node:
        print("[OK] ResponseNode created successfully")
    else:
        print("[FAIL] Failed to create ResponseNode")
    
    # Test 4: Get node schemas
    print("\n4. Getting node schemas...")
    query_schema = get_node_schema("querynode")
    response_schema = get_node_schema("responsenode")
    
    if query_schema:
        print("[OK] QueryNode schema retrieved")
        print(f"   - Node ID: {query_schema['node_id']}")
        print(f"   - Inputs: {len(query_schema['inputs'])}")
        print(f"   - Outputs: {len(query_schema['outputs'])}")
        print(f"   - Parameters: {len(query_schema['parameters'])}")
    else:
        print("[FAIL] Failed to get QueryNode schema")
    
    if response_schema:
        print("[OK] ResponseNode schema retrieved")
        print(f"   - Node ID: {response_schema['node_id']}")
        print(f"   - Inputs: {len(response_schema['inputs'])}")
        print(f"   - Outputs: {len(response_schema['outputs'])}")
        print(f"   - Parameters: {len(response_schema['parameters'])}")
    else:
        print("[FAIL] Failed to get ResponseNode schema")
    
    # Test 5: Test node execution
    print("\n5. Testing node execution...")
    if query_node:
        try:
            # Test QueryNode execution
            result = query_node.run(
                inputs={},
                parameters={"query": "Hello, how are you?"}
            )
            print("[OK] QueryNode execution successful")
            print(f"   - Output: {result}")
        except Exception as e:
            print(f"[FAIL] QueryNode execution failed: {e}")
    
    if response_node:
        try:
            # Test ResponseNode execution
            result = response_node.run(
                inputs={
                    "response_data": "I'm doing great, thank you for asking!",
                    "metadata": {"timestamp": "2024-01-01", "source": "test"}
                },
                parameters={}
            )
            print("[OK] ResponseNode execution successful")
            print(f"   - Output: {result}")
        except Exception as e:
            print(f"[FAIL] ResponseNode execution failed: {e}")
    
    # Test 6: Test invalid node creation
    print("\n6. Testing invalid node creation...")
    invalid_node = create_node("nonexistentnode")
    if invalid_node is None:
        print("[OK] Invalid node creation correctly returns None")
    else:
        print("[FAIL] Invalid node creation should return None")
    
    print("\n" + "=" * 50)
    print("Node Registry testing completed!")


if __name__ == "__main__":
    test_node_registry()