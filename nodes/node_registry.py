"""
Simple Node Registry - Central registry for all available nodes.
"""

from typing import Dict, List, Type, Any, Optional
from .base_node import BaseNode


class NodeRegistry:
    """Simple registry for managing nodes."""
    
    def __init__(self):
        self._nodes: Dict[str, Type[BaseNode]] = {}
    
    def register_node(self, node_class: Type[BaseNode], name: Optional[str] = None) -> None:
        """Register a node class."""
        node_name = name or node_class.__name__.lower()
        self._nodes[node_name] = node_class
    
    def create_node(self, name: str) -> Optional[BaseNode]:
        """Create a node instance by name."""
        node_class = self._nodes.get(name.lower())
        if node_class:
            return node_class()
        return None
    
    def list_nodes(self) -> List[str]:
        """Get list of all registered node names."""
        return list(self._nodes.keys())
    
    def get_node_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get schema for a specific node."""
        node_instance = self.create_node(name)
        if node_instance:
            return node_instance.get_schema()
        return None


# Global registry instance
node_registry = NodeRegistry()


# Convenience functions
def register_node(node_class: Type[BaseNode], name: Optional[str] = None) -> None:
    """Register a node in the global registry"""
    node_registry.register_node(node_class, name)


def create_node(name: str) -> Optional[BaseNode]:
    """Create a node instance by name"""
    return node_registry.create_node(name)


def list_nodes() -> List[str]:
    """List all available nodes"""
    return node_registry.list_nodes()


def get_node_schema(name: str) -> Optional[Dict[str, Any]]:
    """Get schema for a specific node"""
    return node_registry.get_node_schema(name)


