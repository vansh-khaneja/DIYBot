from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class NodeInput:
    """Standardized input structure for nodes"""
    name: str
    type: str
    description: str
    required: bool = True
    default_value: Any = None


@dataclass
class NodeOutput:
    """Standardized output structure for nodes"""
    name: str
    type: str
    description: str


@dataclass
class NodeParameter:
    """Standardized parameter structure for nodes"""
    name: str
    type: str
    description: str
    required: bool = True
    default_value: Any = None
    options: Optional[List[str]] = None


class BaseNode(ABC):
    """
    Base class for all nodes in the chatbot builder.
    Provides a standardized interface for input/output handling and execution.
    """
    
    def __init__(self):
        self.node_id = self.__class__.__name__.lower()
        self.inputs = self._define_inputs()
        self.outputs = self._define_outputs()
        self.parameters = self._define_parameters()
    
    @abstractmethod
    def _define_inputs(self) -> List[NodeInput]:
        """Define the input structure for this node"""
        pass
    
    @abstractmethod
    def _define_outputs(self) -> List[NodeOutput]:
        """Define the output structure for this node"""
        pass
    
    @abstractmethod
    def _define_parameters(self) -> List[NodeParameter]:
        """Define the parameters for this node"""
        pass
    
    @abstractmethod
    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the node logic
        
        Args:
            inputs: Dictionary of input values
            parameters: Dictionary of parameter values
            
        Returns:
            Dictionary of output values
        """
        pass
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate that all required inputs are provided"""
        for input_def in self.inputs:
            if input_def.required and input_def.name not in inputs:
                raise ValueError(f"Required input '{input_def.name}' is missing")
        return True
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """Validate that all required parameters are provided"""
        for param_def in self.parameters:
            if param_def.required and param_def.name not in parameters:
                raise ValueError(f"Required parameter '{param_def.name}' is missing")
        return True
    
    def get_schema(self) -> Dict[str, Any]:
        """Get the complete schema for this node"""
        return {
            "node_id": self.node_id,
            "name": self.__class__.__name__,
            "description": self.__doc__ or "",
            "inputs": [
                {
                    "name": inp.name,
                    "type": inp.type,
                    "description": inp.description,
                    "required": inp.required,
                    "default_value": inp.default_value
                }
                for inp in self.inputs
            ],
            "outputs": [
                {
                    "name": out.name,
                    "type": out.type,
                    "description": out.description
                }
                for out in self.outputs
            ],
            "parameters": [
                {
                    "name": param.name,
                    "type": param.type,
                    "description": param.description,
                    "required": param.required,
                    "default_value": param.default_value,
                    "options": param.options
                }
                for param in self.parameters
            ]
        }
    
    def run(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for node execution with validation
        """
        self.validate_inputs(inputs)
        self.validate_parameters(parameters)
        return self.execute(inputs, parameters)
