"""
Nodes API endpoints - Handle all node-related operations
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Set
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from nodes.node_registry import node_registry

router = APIRouter(prefix="/nodes", tags=["nodes"])


@router.get("/", response_model=Dict[str, Any])
async def get_all_nodes():
    """
    Get all registered nodes with their complete schemas
    
    Returns:
        Dict containing:
        - nodes: List of all registered node names
        - schemas: Dictionary mapping node names to their schemas
    """
    try:
        # Get all registered node names
        node_names = node_registry.list_nodes()
        
        # Get schemas for all nodes
        schemas = {}
        for node_name in node_names:
            schema = node_registry.get_node_schema(node_name)
            if schema:
                schemas[node_name] = schema
        
        return {
            "success": True,
            "data": {
                "nodes": node_names,
                "schemas": schemas,
                "total_count": len(node_names)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve nodes: {str(e)}")


@router.get("/list", response_model=Dict[str, Any])
async def list_nodes():
    """
    Get a simple list of all registered node names
    
    Returns:
        Dict containing list of node names
    """
    try:
        node_names = node_registry.list_nodes()
        return {
            "success": True,
            "data": {
                "nodes": node_names,
                "total_count": len(node_names)
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list nodes: {str(e)}")


@router.get("/{node_name}", response_model=Dict[str, Any])
async def get_node_schema(node_name: str):
    """
    Get schema for a specific node
    
    Args:
        node_name: Name of the node to get schema for
        
    Returns:
        Dict containing the node schema
    """
    try:
        schema = node_registry.get_node_schema(node_name)
        if not schema:
            raise HTTPException(status_code=404, detail=f"Node '{node_name}' not found")
        
        return {
            "success": True,
            "data": schema
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve node schema: {str(e)}")


@router.post("/execute", response_model=Dict[str, Any])
async def execute_flow(payload: Dict[str, Any]):
    """
    Execute a node flow described as a small workflow graph.

    Expected payload structure (example):
    {
      "nodes": {
        "q1": {"type": "QueryNode", "parameters": {"query": "Hello"}},
        "lm1": {"type": "LanguageModelNode", "parameters": {"service": "openai", "model": "gpt-3.5-turbo"}}
      },
      "edges": [
        {"from": {"node": "q1", "output": "query"}, "to": {"node": "lm1", "input": "query"}}
      ],
      "inputs": {  // optional external inputs per node
        "someNode": {"someInput": "value"}
      }
    }
    """
    try:
        nodes_cfg: Dict[str, Any] = payload.get("nodes", {})
        edges: List[Dict[str, Any]] = payload.get("edges", [])
        external_inputs: Dict[str, Dict[str, Any]] = payload.get("inputs", {})

        if not nodes_cfg:
            raise HTTPException(status_code=400, detail="'nodes' is required and cannot be empty")

        # Enforce presence of QueryNode and ResponseNode in every workflow
        type_values = [ (cfg.get("type") or cfg.get("name") or "").lower() for cfg in nodes_cfg.values() ]
        print(f"DEBUG: Received node types: {type_values}")
        has_query = any(t == "querynode" or t == "querynode".lower() or t == "querynode" for t in type_values)
        has_response = any(t == "responsenode" or t == "responsenode".lower() or t == "responsenode" for t in type_values)
        print(f"DEBUG: has_query={has_query}, has_response={has_response}")
        if not has_query or not has_response:
            raise HTTPException(status_code=400, detail={
                "message": "Workflow must include at least one QueryNode and one ResponseNode",
                "received_types": type_values,
                "has_query_node": has_query,
                "has_response_node": has_response
            })

        # Build adjacency and dependency maps
        incoming_by_node: Dict[str, List[Dict[str, str]]] = {nid: [] for nid in nodes_cfg.keys()}
        outgoing_by_node: Dict[str, List[Dict[str, str]]] = {nid: [] for nid in nodes_cfg.keys()}
        depends_on: Dict[str, Set[str]] = {nid: set() for nid in nodes_cfg.keys()}

        for edge in edges:
            src = edge.get("from", {})
            dst = edge.get("to", {})
            src_node = src.get("node")
            dst_node = dst.get("node")
            if not src_node or not dst_node:
                raise HTTPException(status_code=400, detail="Each edge must include 'from.node' and 'to.node'")
            if src_node not in nodes_cfg or dst_node not in nodes_cfg:
                raise HTTPException(status_code=400, detail=f"Edge references unknown nodes: {src_node} -> {dst_node}")
            incoming_by_node[dst_node].append({"from": src_node, "output": src.get("output", ""), "input": dst.get("input", "")})
            outgoing_by_node[src_node].append({"to": dst_node, "output": src.get("output", ""), "input": dst.get("input", "")})
            depends_on[dst_node].add(src_node)

        # Helper to instantiate node by type
        def create_node_instance(type_name: str):
            # Allow both class name and registry key (case-insensitive)
            instance = node_registry.create_node(type_name)
            if instance is None:
                # Try lowercased typename as key
                instance = node_registry.create_node(type_name.lower())
            return instance

        # Track execution state
        executed: Set[str] = set()
        results: Dict[str, Dict[str, Any]] = {}
        errors: Dict[str, str] = {}
        response_node_inputs: Dict[str, Dict[str, Any]] = {}

        # Execution loop: process nodes whose dependencies are satisfied
        remaining_nodes = set(nodes_cfg.keys())
        max_iterations = len(remaining_nodes) + 10  # safety
        iterations = 0

        while remaining_nodes and iterations < max_iterations:
            iterations += 1
            progressed = False

            ready_nodes = [nid for nid in list(remaining_nodes) if depends_on[nid].issubset(executed)]
            for node_id in ready_nodes:
                node_spec = nodes_cfg[node_id]
                type_name = node_spec.get("type") or node_spec.get("name")
                if not type_name:
                    errors[node_id] = "Missing 'type' for node"
                    remaining_nodes.remove(node_id)
                    progressed = True
                    continue

                node_instance = create_node_instance(type_name)
                if node_instance is None:
                    errors[node_id] = f"Unknown node type '{type_name}'"
                    remaining_nodes.remove(node_id)
                    progressed = True
                    continue

                # Build inputs from external inputs and upstream edges
                built_inputs: Dict[str, Any] = {}
                built_inputs.update(external_inputs.get(node_id, {}))

                for inc in incoming_by_node.get(node_id, []):
                    src_node = inc["from"]
                    src_output = inc.get("output")
                    dst_input = inc.get("input")

                    if src_node not in results:
                        errors[node_id] = f"Upstream node '{src_node}' has no results"
                        break
                    src_payload = results[src_node]
                    if src_output and src_output in src_payload:
                        built_inputs[dst_input or src_output] = src_payload[src_output]
                    else:
                        # If output not specified, try to merge all outputs
                        for k, v in src_payload.items():
                            if dst_input:
                                built_inputs[dst_input] = v
                            else:
                                built_inputs[k] = v

                if node_id in errors:
                    remaining_nodes.remove(node_id)
                    progressed = True
                    continue

                parameters: Dict[str, Any] = node_spec.get("parameters", {})

                try:
                    output = node_instance.run(built_inputs, parameters)
                    results[node_id] = output if isinstance(output, dict) else {"result": output}
                    executed.add(node_id)
                except Exception as e:
                    errors[node_id] = str(e)

                remaining_nodes.remove(node_id)
                progressed = True

                # Capture inputs for ResponseNode(s) only (for minimal API output)
                tn = (type_name or "").lower()
                if tn == "responsenode":
                    response_node_inputs[node_id] = built_inputs

            if not progressed:
                # Cycle or unresolved dependency
                unresolved = list(remaining_nodes)
                raise HTTPException(status_code=400, detail={
                    "message": "Unresolved dependencies or cyclic graph",
                    "unresolved_nodes": unresolved
                })

        # Minimal response: only what ResponseNode(s) received as input
        return {
            "success": True,
            "data": {
                "response_inputs": response_node_inputs,
                "executed_nodes": list(executed),
                "errors": errors
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute flow: {str(e)}")
