from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import sys
import os

# Add the parent directory to the path to import ui_components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ui_components import NodeUIConfig, UIGroup, UIComponent


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


@dataclass
class NodeStyling:
    """Styling configuration for node appearance"""
    icon: Optional[str] = None  # SVG string, emoji, or image URL
    background_color: Optional[str] = None  # CSS color
    border_color: Optional[str] = None  # CSS color
    text_color: Optional[str] = None  # CSS color
    custom_css: Optional[str] = None  # Additional CSS styles
    subtitle: Optional[str] = None  # Custom subtitle text
    icon_position: str = "left"  # "left", "right", "top", "bottom"
    shape: str = "rectangle"  # "rectangle", "circle", "rounded", "custom"
    width: Optional[int] = None  # Fixed width in pixels
    height: Optional[int] = None  # Fixed height in pixels
    html_template: Optional[str] = None  # Custom HTML template
    css_classes: Optional[str] = None  # Additional CSS classes
    inline_styles: Optional[str] = None  # Additional inline styles as JSON string


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
        self.styling = self._define_styling()
        self.ui_config = self._define_ui_config()
    
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
    
    def _define_styling(self) -> NodeStyling:
        """Define the styling for this node - override in subclasses for custom styling"""
        return NodeStyling()
    
    def _define_ui_config(self) -> Optional[NodeUIConfig]:
        """Define the UI configuration for this node - override in subclasses for custom UI"""
        return None
    
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
            ],
            "styling": {
                "icon": self.styling.icon,
                "background_color": self.styling.background_color,
                "border_color": self.styling.border_color,
                "text_color": self.styling.text_color,
                "custom_css": self.styling.custom_css,
                "subtitle": self.styling.subtitle,
                "icon_position": self.styling.icon_position,
                "shape": self.styling.shape,
                "width": self.styling.width,
                "height": self.styling.height,
                "html_template": self.styling.html_template,
                "css_classes": self.styling.css_classes,
                "inline_styles": self.styling.inline_styles
            },
            "ui_config": {
                "node_id": self.ui_config.node_id,
                "node_name": self.ui_config.node_name,
                "groups": [
                    {
                        "name": group.name,
                        "label": group.label,
                        "description": group.description,
                        "components": [
                            {
                                "type": comp.type,
                                "name": comp.name,
                                "label": comp.label,
                                "description": comp.description,
                                "required": comp.required,
                                "default_value": comp.default_value,
                                "placeholder": comp.placeholder,
                                "disabled": comp.disabled,
                                "visible": comp.visible,
                                "validation": comp.validation,
                                "styling": comp.styling,
                                # Component-specific fields
                                **({"rows": comp.rows} if hasattr(comp, 'rows') else {}),
                                **({"options": comp.options} if hasattr(comp, 'options') else {}),
                                **({"multiple": comp.multiple} if hasattr(comp, 'multiple') else {}),
                                **({"text": comp.text} if hasattr(comp, 'text') else {}),
                                **({"html": comp.html} if hasattr(comp, 'html') else {}),
                                **({"button_text": comp.button_text} if hasattr(comp, 'button_text') else {}),
                                **({"variant": comp.variant} if hasattr(comp, 'variant') else {}),
                            }
                            for comp in group.components
                        ],
                        "collapsible": group.collapsible,
                        "collapsed": group.collapsed,
                        "styling": group.styling
                    }
                    for group in (self.ui_config.groups or [])
                ],
                "global_styling": self.ui_config.global_styling,
                "layout": self.ui_config.layout,
                "columns": self.ui_config.columns,
                "dialog_config": {
                    "title": self.ui_config.dialog_config.title if self.ui_config.dialog_config else None,
                    "description": self.ui_config.dialog_config.description if self.ui_config.dialog_config else None,
                    "width": self.ui_config.dialog_config.width if self.ui_config.dialog_config else None,
                    "height": self.ui_config.dialog_config.height if self.ui_config.dialog_config else None,
                    "background_color": self.ui_config.dialog_config.background_color if self.ui_config.dialog_config else None,
                    "border_color": self.ui_config.dialog_config.border_color if self.ui_config.dialog_config else None,
                    "text_color": self.ui_config.dialog_config.text_color if self.ui_config.dialog_config else None,
                    "icon": self.ui_config.dialog_config.icon if self.ui_config.dialog_config else None,
                    "icon_color": self.ui_config.dialog_config.icon_color if self.ui_config.dialog_config else None,
                    "header_background": self.ui_config.dialog_config.header_background if self.ui_config.dialog_config else None,
                    "footer_background": self.ui_config.dialog_config.footer_background if self.ui_config.dialog_config else None,
                    "button_primary_color": self.ui_config.dialog_config.button_primary_color if self.ui_config.dialog_config else None,
                    "button_secondary_color": self.ui_config.dialog_config.button_secondary_color if self.ui_config.dialog_config else None,
                } if self.ui_config.dialog_config else None
            } if self.ui_config else None
        }
    
    def run(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for node execution with validation
        """
        self.validate_inputs(inputs)
        self.validate_parameters(parameters)
        return self.execute(inputs, parameters)
