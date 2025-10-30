"""
Nodes API endpoints - Handle all node-related operations
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any, Set
import traceback
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from nodes.node_registry import node_registry
from language_model_services.openai_service.openai_service import OpenAIService
from language_model_services.groq_service.groq_service import GroqService
from language_model_services.ollama_service.ollama_service import OllamaService

router = APIRouter(prefix="/nodes", tags=["nodes"])


def combine_multiple_inputs(values: List[Any]) -> Any:
    """
    Intelligently combine multiple input values from different connections.
    
    Args:
        values: List of values from multiple connections to the same input
        
    Returns:
        Combined value based on the types and content
    """
    if not values:
        return None
    
    if len(values) == 1:
        return values[0]
    
    # Filter out None/empty values
    non_empty_values = [v for v in values if v is not None and v != ""]
    
    if not non_empty_values:
        return None
    
    if len(non_empty_values) == 1:
        return non_empty_values[0]
    
    # Check if all values are strings
    if all(isinstance(v, str) for v in non_empty_values):
        # Combine strings intelligently
        if all(len(v.strip()) > 0 for v in non_empty_values):
            # If all strings have content, combine them with context
            combined = "\n\n".join(non_empty_values)
            return f"Combined inputs:\n{combined}"
        else:
            # Return the longest non-empty string
            return max(non_empty_values, key=len)
    
    # Check if all values are dictionaries
    if all(isinstance(v, dict) for v in non_empty_values):
        # Merge dictionaries
        combined_dict = {}
        for i, d in enumerate(non_empty_values):
            for key, value in d.items():
                if key in combined_dict:
                    # If key exists, combine the values
                    if isinstance(combined_dict[key], str) and isinstance(value, str):
                        combined_dict[key] = f"{combined_dict[key]}\n{value}"
                    else:
                        combined_dict[f"{key}_{i}"] = value
                else:
                    combined_dict[key] = value
        return combined_dict
    
    # Check if all values are lists
    if all(isinstance(v, list) for v in non_empty_values):
        # Flatten and combine lists
        combined_list = []
        for v in non_empty_values:
            combined_list.extend(v)
        return combined_list
    
    # For mixed types, return as a structured object
    return {
        "combined_inputs": non_empty_values,
        "input_count": len(non_empty_values),
        "input_types": [type(v).__name__ for v in non_empty_values]
    }


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
        
        # Get schemas for all nodes (tolerant to per-node errors)
        schemas: Dict[str, Any] = {}
        schema_errors: Dict[str, str] = {}
        for node_name in node_names:
            try:
                schema = node_registry.get_node_schema(node_name)
                if schema:
                    schemas[node_name] = schema
                else:
                    schema_errors[node_name] = "No schema returned"
            except Exception as e:
                schema_errors[node_name] = str(e)
        
        # Return 200 with partial results; include per-node errors for visibility
        return {
            "success": True,
            "data": {
                "nodes": node_names,
                "schemas": schemas,
                "errors": schema_errors,
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

        print(f"DEBUG: Building edge maps for {len(edges)} edges")
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
        skipped: Set[str] = set()
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

                # Group incoming connections by input name to handle multiple connections
                input_groups = {}
                incoming_list = incoming_by_node.get(node_id, [])
                print(f"\nEXECUTE -> Node '{node_id}' type='{type_name}'")
                print(f"INCOMING -> {incoming_list}")
                for inc in incoming_list:
                    src_node = inc["from"]
                    src_output = inc.get("output")
                    dst_input = inc.get("input")

                    if src_node not in results:
                        errors[node_id] = f"Upstream node '{src_node}' has no results"
                        print(f"ERROR: {errors[node_id]}")
                        break
                    
                    src_payload = results[src_node]
                    input_key = dst_input or src_output or "default"
                    
                    if src_output:
                        # Follow only active sockets: key must exist and be non-empty
                        if src_output in src_payload:
                            candidate = src_payload[src_output]
                            if candidate in (None, "", [], {}):
                                # Inactive socket -> skip this edge
                                print(f"ROUTING: skipping inactive socket '{src_output}' from '{src_node}' -> '{node_id}'")
                                continue
                            value = candidate
                        else:
                            # Requested output not present -> skip this edge entirely
                            print(f"ROUTING: output '{src_output}' missing on '{src_node}', available={list(src_payload.keys())}")
                            continue
                    else:
                        # If output not specified, try to merge all outputs
                        if len(src_payload) == 1:
                            value = list(src_payload.values())[0]
                        else:
                            value = src_payload
                    
                    # Group values by input key
                    if input_key not in input_groups:
                        input_groups[input_key] = []
                    input_groups[input_key].append(value)

                # Combine multiple values for each input
                for input_key, values in input_groups.items():
                    if len(values) == 1:
                        # Single value - use as-is
                        built_inputs[input_key] = values[0]
                    else:
                        # Multiple values - combine intelligently
                        built_inputs[input_key] = combine_multiple_inputs(values)

                # If this node had incoming edges but no active routed inputs, skip silently
                if incoming_list and (not built_inputs):
                    print(f"SKIP: Node '{node_id}' has no active inputs after routing. Skipping execution.")
                    skipped.add(node_id)
                    remaining_nodes.remove(node_id)
                    progressed = True
                    continue

                if node_id in errors:
                    remaining_nodes.remove(node_id)
                    progressed = True
                    continue

                parameters: Dict[str, Any] = node_spec.get("parameters", {})

                try:
                    print(f"INPUTS -> {built_inputs}")
                    print(f"PARAMS -> {parameters}")
                    output = node_instance.run(built_inputs, parameters)
                    results[node_id] = output if isinstance(output, dict) else {"result": output}
                    print(f"OUTPUTS <- {results[node_id]}")
                    executed.add(node_id)
                except Exception as e:
                    tb = traceback.format_exc()
                    errors[node_id] = f"{e}\n{tb}"
                    print(f"EXCEPTION in node '{node_id}' type='{type_name}': {errors[node_id]}")

                remaining_nodes.remove(node_id)
                progressed = True

                # Capture inputs and outputs for ResponseNode(s) only (for minimal API output)
                tn = (type_name or "").lower()
                if tn == "responsenode":
                    # Include both inputs and outputs for ResponseNode
                    response_node_inputs[node_id] = {
                        **built_inputs,  # Inputs received
                        **results[node_id]  # Outputs produced (like final_response)
                    }

            if not progressed:
                # Cycle or unresolved dependency
                unresolved = list(remaining_nodes)
                raise HTTPException(status_code=400, detail={
                    "message": "Unresolved dependencies or cyclic graph",
                    "unresolved_nodes": unresolved
                })

        # Minimal response: only what ResponseNode(s) received as input
        print("FLOW RESULT -> Response node inputs:")
        print(response_node_inputs)
        return {
            "success": True,
            "data": {
                "response_inputs": response_node_inputs,
                "executed_nodes": list(executed),
                "skipped_nodes": list(skipped),
                "errors": errors
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute flow: {str(e)}")


@router.get("/models/{service}", response_model=Dict[str, Any])
async def get_service_models(service: str):
    """
    Get available models for a specific AI service
    
    Args:
        service: The AI service name (openai, groq, ollama)
        
    Returns:
        Dict containing the available models for the service
    """
    try:
        service_lower = service.lower()
        
        if service_lower == "openai":
            service_instance = OpenAIService()
        elif service_lower == "groq":
            service_instance = GroqService()
        elif service_lower == "ollama":
            service_instance = OllamaService()
        else:
            raise HTTPException(status_code=400, detail=f"Unknown service: {service}. Supported services: openai, groq, ollama")
        
        models_data = service_instance.get_models()
        
        return {
            "success": True,
            "data": models_data
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get models for service {service}: {str(e)}")


@router.post("/{node_id}/update-config", response_model=Dict[str, Any])
async def update_node_config(node_id: str, config: Dict[str, Any]):
    """
    Update node configuration and return updated schema
    
    This endpoint allows nodes to update their configuration
    and returns the updated schema with new outputs/inputs.
    
    Args:
        node_id: The node type identifier
        config: Configuration data to update
        
    Returns:
        Updated node schema with new outputs/inputs
    """
    try:
        # Create node instance
        node = node_registry.create_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
        
        
        # Update other parameters if needed
        for param_name, param_value in config.items():
            if hasattr(node, f'update_{param_name}'):
                getattr(node, f'update_{param_name}')(param_value)
        
        # Get updated schema
        updated_schema = node.get_schema()
        
        return {
            "success": True,
            "data": updated_schema
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update node config: {str(e)}")


@router.get("/{node_id}/schema", response_model=Dict[str, Any])
async def get_node_schema(node_id: str):
    """
    Get the current schema for a specific node
    
    Args:
        node_id: The node type identifier
        
    Returns:
        Current node schema
    """
    try:
        node = node_registry.create_node(node_id)
        if not node:
            raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found")
        
        schema = node.get_schema()
        
        return {
            "success": True,
            "data": schema
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get node schema: {str(e)}")