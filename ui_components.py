"""
UI Component Definitions for Declarative Node Configuration

This module defines the UI components that can be used in node configurations
to create dynamic, declarative user interfaces.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum


class UIComponentType(Enum):
    """Types of UI components that can be rendered"""
    TEXT_INPUT = "text_input"
    TEXTAREA = "textarea"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    CHECKBOX = "checkbox"
    RADIO = "radio"
    NUMBER_INPUT = "number_input"
    SLIDER = "slider"
    COLOR_PICKER = "color_picker"
    FILE_UPLOAD = "file_upload"
    DATE_PICKER = "date_picker"
    LABEL = "label"
    DIVIDER = "divider"
    BUTTON = "button"
    TOGGLE = "toggle"


@dataclass
class UIOption:
    """Option for select, radio, and multi-select components"""
    value: str
    label: str
    disabled: bool = False


@dataclass
class UIComponent:
    """Base UI component definition"""
    name: str
    label: str
    type: UIComponentType
    description: Optional[str] = None
    required: bool = False
    default_value: Any = None
    placeholder: Optional[str] = None
    disabled: bool = False
    visible: bool = True
    validation: Optional[Dict[str, Any]] = None
    styling: Optional[Dict[str, Any]] = None


@dataclass
class TextInputComponent(UIComponent):
    """Text input component"""
    type: UIComponentType = UIComponentType.TEXT_INPUT
    max_length: Optional[int] = None
    min_length: Optional[int] = None
    pattern: Optional[str] = None


@dataclass
class TextareaComponent(UIComponent):
    """Textarea component"""
    type: UIComponentType = UIComponentType.TEXTAREA
    rows: int = 3
    max_length: Optional[int] = None
    min_length: Optional[int] = None


@dataclass
class SelectComponent(UIComponent):
    """Select dropdown component"""
    type: UIComponentType = UIComponentType.SELECT
    options: List[UIOption] = None
    multiple: bool = False
    searchable: bool = False


@dataclass
class MultiSelectComponent(UIComponent):
    """Multi-select component"""
    type: UIComponentType = UIComponentType.MULTI_SELECT
    options: List[UIOption] = None
    searchable: bool = False
    max_selections: Optional[int] = None


@dataclass
class CheckboxComponent(UIComponent):
    """Checkbox component"""
    type: UIComponentType = UIComponentType.CHECKBOX
    checked_value: Any = True
    unchecked_value: Any = False


@dataclass
class RadioComponent(UIComponent):
    """Radio button group component"""
    type: UIComponentType = UIComponentType.RADIO
    options: List[UIOption] = None
    orientation: str = "vertical"  # "vertical" or "horizontal"


@dataclass
class NumberInputComponent(UIComponent):
    """Number input component"""
    type: UIComponentType = UIComponentType.NUMBER_INPUT
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    precision: Optional[int] = None


@dataclass
class SliderComponent(UIComponent):
    """Slider component"""
    type: UIComponentType = UIComponentType.SLIDER
    min_value: float = 0
    max_value: float = 100
    step: float = 1
    show_value: bool = True
    orientation: str = "horizontal"  # "horizontal" or "vertical"


@dataclass
class ColorPickerComponent(UIComponent):
    """Color picker component"""
    type: UIComponentType = UIComponentType.COLOR_PICKER
    format: str = "hex"  # "hex", "rgb", "hsl"
    show_preset_colors: bool = True


@dataclass
class FileUploadComponent(UIComponent):
    """File upload component"""
    type: UIComponentType = UIComponentType.FILE_UPLOAD
    accept: Optional[str] = None  # MIME types or file extensions
    multiple: bool = False
    max_file_size: Optional[int] = None  # in bytes
    max_files: Optional[int] = None


@dataclass
class DatePickerComponent(UIComponent):
    """Date picker component"""
    type: UIComponentType = UIComponentType.DATE_PICKER
    format: str = "YYYY-MM-DD"
    min_date: Optional[str] = None
    max_date: Optional[str] = None


@dataclass
class LabelComponent(UIComponent):
    """Label component for display only"""
    type: UIComponentType = UIComponentType.LABEL
    text: str = ""
    html: bool = False  # Whether to render as HTML


@dataclass
class DividerComponent(UIComponent):
    """Divider component"""
    type: UIComponentType = UIComponentType.DIVIDER
    orientation: str = "horizontal"  # "horizontal" or "vertical"
    thickness: int = 1
    color: str = "#e5e7eb"


@dataclass
class ButtonComponent(UIComponent):
    """Button component"""
    type: UIComponentType = UIComponentType.BUTTON
    button_text: str = "Click Me"
    button_type: str = "button"  # "button", "submit", "reset"
    variant: str = "primary"  # "primary", "secondary", "danger", "success"
    size: str = "medium"  # "small", "medium", "large"
    icon: Optional[str] = None


@dataclass
class ToggleComponent(UIComponent):
    """Toggle switch component"""
    type: UIComponentType = UIComponentType.TOGGLE
    on_value: Any = True
    off_value: Any = False
    size: str = "medium"  # "small", "medium", "large"




@dataclass
class UIGroup:
    """Group of UI components"""
    name: str
    label: str
    description: Optional[str] = None
    components: List[UIComponent] = None
    collapsible: bool = False
    collapsed: bool = False
    styling: Optional[Dict[str, Any]] = None


@dataclass
class DialogConfig:
    """Configuration for the dialog/modal that contains the UI components."""
    title: str
    description: str
    width: str = "max-w-2xl"
    height: str = "max-h-[90vh]"
    background_color: str = "#1f2937"
    border_color: str = "#374151"
    text_color: str = "#ffffff"
    icon: Optional[str] = None
    icon_color: Optional[str] = None
    header_background: Optional[str] = None
    footer_background: Optional[str] = None
    button_primary_color: Optional[str] = None
    button_secondary_color: Optional[str] = None

@dataclass
class NodeUIConfig:
    """Complete UI configuration for a node"""
    node_id: str
    node_name: str
    groups: List[UIGroup] = None
    global_styling: Optional[Dict[str, Any]] = None
    layout: str = "vertical"  # "vertical", "horizontal", "grid"
    columns: Optional[int] = None  # For grid layout
    dialog_config: Optional[DialogConfig] = None


def create_text_input(name: str, label: str, **kwargs) -> TextInputComponent:
    """Helper function to create a text input component"""
    return TextInputComponent(
        name=name,
        label=label,
        type=UIComponentType.TEXT_INPUT,
        **kwargs
    )


def create_textarea(name: str, label: str, **kwargs) -> TextareaComponent:
    """Helper function to create a textarea component"""
    return TextareaComponent(
        name=name,
        label=label,
        type=UIComponentType.TEXTAREA,
        **kwargs
    )


def create_select(name: str, label: str, options: List[UIOption], **kwargs) -> SelectComponent:
    """Helper function to create a select component"""
    return SelectComponent(
        name=name,
        label=label,
        type=UIComponentType.SELECT,
        options=options,
        **kwargs
    )


def create_multi_select(name: str, label: str, options: List[UIOption], **kwargs) -> MultiSelectComponent:
    """Helper function to create a multi-select component"""
    return MultiSelectComponent(
        name=name,
        label=label,
        type=UIComponentType.MULTI_SELECT,
        options=options,
        **kwargs
    )


def create_checkbox(name: str, label: str, **kwargs) -> CheckboxComponent:
    """Helper function to create a checkbox component"""
    return CheckboxComponent(
        name=name,
        label=label,
        type=UIComponentType.CHECKBOX,
        **kwargs
    )


def create_radio(name: str, label: str, options: List[UIOption], **kwargs) -> RadioComponent:
    """Helper function to create a radio component"""
    return RadioComponent(
        name=name,
        label=label,
        type=UIComponentType.RADIO,
        options=options,
        **kwargs
    )


def create_number_input(name: str, label: str, **kwargs) -> NumberInputComponent:
    """Helper function to create a number input component"""
    return NumberInputComponent(
        name=name,
        label=label,
        type=UIComponentType.NUMBER_INPUT,
        **kwargs
    )


def create_slider(name: str, label: str, **kwargs) -> SliderComponent:
    """Helper function to create a slider component"""
    return SliderComponent(
        name=name,
        label=label,
        type=UIComponentType.SLIDER,
        **kwargs
    )


def create_color_picker(name: str, label: str, **kwargs) -> ColorPickerComponent:
    """Helper function to create a color picker component"""
    return ColorPickerComponent(
        name=name,
        label=label,
        type=UIComponentType.COLOR_PICKER,
        **kwargs
    )


def create_file_upload(name: str, label: str, **kwargs) -> FileUploadComponent:
    """Helper function to create a file upload component"""
    return FileUploadComponent(
        name=name,
        label=label,
        type=UIComponentType.FILE_UPLOAD,
        **kwargs
    )


def create_date_picker(name: str, label: str, **kwargs) -> DatePickerComponent:
    """Helper function to create a date picker component"""
    return DatePickerComponent(
        name=name,
        label=label,
        type=UIComponentType.DATE_PICKER,
        **kwargs
    )


def create_label(text: str, **kwargs) -> LabelComponent:
    """Helper function to create a label component"""
    return LabelComponent(
        name=f"label_{hash(text)}",
        label="",
        type=UIComponentType.LABEL,
        text=text,
        **kwargs
    )


def create_divider(**kwargs) -> DividerComponent:
    """Helper function to create a divider component"""
    return DividerComponent(
        name=f"divider_{hash(str(kwargs))}",
        label="",
        type=UIComponentType.DIVIDER,
        **kwargs
    )


def create_button(name: str, button_text: str, **kwargs) -> ButtonComponent:
    """Helper function to create a button component"""
    return ButtonComponent(
        name=name,
        label="",
        type=UIComponentType.BUTTON,
        button_text=button_text,
        **kwargs
    )


def create_toggle(name: str, label: str, **kwargs) -> ToggleComponent:
    """Helper function to create a toggle component"""
    return ToggleComponent(
        name=name,
        label=label,
        type=UIComponentType.TOGGLE,
        **kwargs
    )


