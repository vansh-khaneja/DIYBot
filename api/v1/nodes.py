"""
Nodes API endpoints - Handle all node-related operations
"""

from fastapi import APIRouter, HTTPException
from typing import List, Dict, Any
import sys
import os

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
