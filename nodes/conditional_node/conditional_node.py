"""
Conditional Node - Evaluates a condition on inputs and branches.

Supports operators: equals, contains, starts_with, ends_with.
Outputs two sockets: "true" and "false" to enable branching.
"""

from typing import Dict, Any, List
import sys
import os

# Add the parent directory to the path to import base_node and ui_components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter, NodeStyling
from ui_components import (
    NodeUIConfig, UIGroup, DialogConfig,
    create_text_input, create_select, create_checkbox,
    UIOption
)


class ConditionalNode(BaseNode):
    """
    Conditional Node - Evaluates a condition and routes accordingly.

    Inputs:
      - left (required): left-hand value (commonly connect from QueryNode's `query`).
      - right (optional): right-hand value (alternatively use parameter `right_value`).

    Parameters:
      - operator: equals | contains | starts_with | ends_with
      - right_value: literal right-hand value if not provided via input
      - case_sensitive: compare with case sensitivity (default False)

    Outputs:
      - true: emits the `left` value when condition is True (for branching)
      - false: emits the `left` value when condition is False (for branching)
      - condition: boolean result for downstream logic or inspection
    """

    def _define_inputs(self) -> List[NodeInput]:
        return [
            NodeInput(
                name="left",
                type="string",
                description="Left-hand value to evaluate (e.g., user query)",
                required=True,
            ),
            NodeInput(
                name="right",
                type="string",
                description="Optional right-hand value; if absent, uses parameter right_value",
                required=False,
            ),
        ]

    def _define_outputs(self) -> List[NodeOutput]:
        return [
            NodeOutput(
                name="true",
                type="string",
                description="Pass-through when condition True (for branching)",
            ),
            NodeOutput(
                name="false",
                type="string",
                description="Pass-through when condition False (for branching)",
            ),
            NodeOutput(
                name="condition",
                type="boolean",
                description="Boolean result of the evaluation",
            ),
        ]

    def _define_parameters(self) -> List[NodeParameter]:
        return [
            NodeParameter(
                name="operator",
                type="string",
                description="Comparison operator",
                required=True,
                default_value="contains",
                options=["equals", "contains", "starts_with", "ends_with"],
            ),
            NodeParameter(
                name="right_value",
                type="string",
                description="Literal right-hand value (used if input `right` not connected)",
                required=False,
                default_value="",
            ),
            NodeParameter(
                name="case_sensitive",
                type="boolean",
                description="Enable case-sensitive comparison",
                required=False,
                default_value=False,
            ),
        ]

    def _define_styling(self) -> NodeStyling:
        # Custom HTML to render a rounded diamond with orange accent, consistent with other nodes
        return NodeStyling(
            html_template="""
            <div class=\"cond-node-outer\">
                <div class=\"cond-node-inner\">
                    <div class=\"cond-icon\">
                        <svg xmlns=\"http://www.w3.org/2000/svg\" width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" stroke=\"currentColor\" stroke-width=\"2\" stroke-linecap=\"round\" stroke-linejoin=\"round\" class=\"lucide lucide-network-icon lucide-network\"><rect x=\"16\" y=\"16\" width=\"6\" height=\"6\" rx=\"1\"/><rect x=\"2\" y=\"16\" width=\"6\" height=\"6\" rx=\"1\"/><rect x=\"9\" y=\"2\" width=\"6\" height=\"6\" rx=\"1\"/><path d=\"M5 16v-3a1 1 0 0 1 1-1h12a1 1 0 0 1 1 1v3\"/><path d=\"M12 12V8\"/></svg>
                    </div>
                    <div class=\"cond-content\">
                        <div class=\"cond-title\">Conditional Node</div>
                        <div class=\"cond-subtitle\">DECISION</div>
                    </div>
                </div>
            </div>
            """,
            custom_css="""
            .cond-node-outer {
                width: 160px; height: 110px; position: relative; /* wider for text */
                border-radius: 4px; /* sharper corners */
                background: #1f1f1f;
                border: 1.5px solid #f59e0b;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                transform-origin: center center;
            }
            .cond-node-outer:hover { border-color: #fbbf24; box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2); }
            .cond-node-inner { position: absolute; inset: 8px; display: grid; grid-template-columns: 18px 1fr; column-gap: 8px; align-items: center; }
            .cond-icon { color: #f59e0b; display: flex; align-items: start; padding-top: 2px; }
            .cond-icon svg { width: 16px; height: 16px; }
            .cond-content { display: flex; flex-direction: column; justify-content: center; min-width: 0; }
            .cond-title { font-size: 12px; font-weight: 700; color: #ffffff; margin-bottom: 2px; line-height: 1.2; white-space: normal; word-break: break-word; }
            .cond-subtitle { font-size: 10px; color: #f59e0b; opacity: 0.9; line-height: 1.2; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
            """,
            icon="", subtitle="", background_color="#1f1f1f", border_color="#f59e0b", text_color="#ffffff",
            shape="custom", width=110, height=110, css_classes="", inline_styles='{}', icon_position=""
        )

    def _define_ui_config(self) -> NodeUIConfig:
        return NodeUIConfig(
            node_id=self.node_id,
            node_name="ConditionalNode",
            groups=[
                UIGroup(
                    name="condition_config",
                    label="Condition Configuration",
                    components=[
                        create_select(
                            name="operator",
                            label="Operator *",
                            required=True,
                            options=[
                                UIOption(label="equals", value="equals"),
                                UIOption(label="contains", value="contains"),
                                UIOption(label="starts_with", value="starts_with"),
                                UIOption(label="ends_with", value="ends_with"),
                            ],
                            default_value="contains",
                        ),
                        create_text_input(
                            name="right_value",
                            label="Right Value (optional if `right` input connected)",
                            required=False,
                            default_value="",
                            placeholder="Enter literal value...",
                        ),
                        create_checkbox(
                            name="case_sensitive",
                            label="Case sensitive",
                            required=False,
                            default_value=False,
                        ),
                    ],
                    styling={
                        "padding": "16px",
                        "background": "#2a2a2a",
                        "border_radius": "8px",
                        "border": "1px solid #404040",
                    },
                )
            ],
            layout="vertical",
            global_styling={"font_family": "Inter, sans-serif", "color_scheme": "light"},
            dialog_config=DialogConfig(
                title="Configure ConditionalNode",
                description="Evaluate a condition and branch outputs to true/false.",
                background_color="#1f1f1f",
                border_color="#f59e0b",
                text_color="#ffffff",
                icon="""<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n  <path d=\"M10 6h4M4 12h16M10 18h4\" stroke=\"#f59e0b\" stroke-width=\"2\" stroke-linecap=\"round\"/>\n</svg>""",
                icon_color="#f59e0b",
                header_background="#1f1f1f",
                footer_background="#1f1f1f",
                button_primary_color="#f59e0b",
                button_secondary_color="#374151",
            ),
        )

    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        left_value = inputs.get("left", "")
        right_value = inputs.get("right")
        if right_value is None:
            right_value = parameters.get("right_value", "")

        operator = parameters.get("operator", "contains")
        case_sensitive = bool(parameters.get("case_sensitive", False))

        # Prepare values
        left_str = "" if left_value is None else str(left_value)
        right_str = "" if right_value is None else str(right_value)

        if not case_sensitive:
            left_cmp = left_str.lower()
            right_cmp = right_str.lower()
        else:
            left_cmp = left_str
            right_cmp = right_str

        # Evaluate
        if operator == "equals":
            result = left_cmp == right_cmp
        elif operator == "contains":
            result = right_cmp in left_cmp
        elif operator == "starts_with":
            result = left_cmp.startswith(right_cmp)
        elif operator == "ends_with":
            result = left_cmp.endswith(right_cmp)
        else:
            # Fallback safe default
            result = False

        # Expose for template
        self.node_data = {"operator": operator}

        # Emit only the active branch to avoid multiple-path routing conflicts
        output: Dict[str, Any] = {"condition": result}
        if result:
            output["true"] = left_str
        else:
            output["false"] = left_str
        return output


