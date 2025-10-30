"""
Intent Classification Node - Classifies a query into one of up to 5 intents via LLM.

Inputs:
  - query (required): the user text to classify

Parameters:
  - class_i_label / class_i_instruction (i=1..5)
  - classes_count: number of visible class slots (1-5)
  - temperature: float
  - max_tokens: int
  - service: openai | groq | ollama (advanced, at bottom)
  - model: model name (optional)

Outputs:
  - intent: chosen label
  - confidence: float in [0,1]
  - reason: short rationale
"""

from typing import Dict, Any, List
import sys
import os
import json

# Add the parent directory to the path to import base_node and ui_components
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Add the tools directory to the path
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'tools', 'language_model_tool'))

from base_node import BaseNode, NodeInput, NodeOutput, NodeParameter, NodeStyling
from ui_components import (
    NodeUIConfig, UIGroup, DialogConfig,
    create_select, create_textarea, create_slider, create_number_input,
    UIOption
)

try:
    from language_model_tool import LanguageModelTool
except ImportError:
    LanguageModelTool = None


class IntentClassificationNode(BaseNode):
    """Intent classifier using a configurable LLM and arbitrary class set."""

    def _define_inputs(self) -> List[NodeInput]:
        return [
            NodeInput(
                name="query",
                type="string",
                description="User query to classify",
                required=True,
            ),
        ]

    def _define_outputs(self) -> List[NodeOutput]:
        return [
            NodeOutput(name="intent", type="string", description="Predicted intent label"),
            NodeOutput(name="confidence", type="number", description="Confidence score [0,1]"),
            NodeOutput(name="reason", type="string", description="Brief rationale for the decision"),
        ]

    def _define_parameters(self) -> List[NodeParameter]:
        return [
            # Class slots (up to 5)
            NodeParameter(name="class_1_label", type="string", description="Class 1 label", required=False, default_value=""),
            NodeParameter(name="class_1_instruction", type="string", description="Class 1 description", required=False, default_value=""),
            NodeParameter(name="class_2_label", type="string", description="Class 2 label", required=False, default_value=""),
            NodeParameter(name="class_2_instruction", type="string", description="Class 2 description", required=False, default_value=""),
            NodeParameter(name="class_3_label", type="string", description="Class 3 label", required=False, default_value=""),
            NodeParameter(name="class_3_instruction", type="string", description="Class 3 description", required=False, default_value=""),
            NodeParameter(name="class_4_label", type="string", description="Class 4 label", required=False, default_value=""),
            NodeParameter(name="class_4_instruction", type="string", description="Class 4 description", required=False, default_value=""),
            NodeParameter(name="class_5_label", type="string", description="Class 5 label", required=False, default_value=""),
            NodeParameter(name="class_5_instruction", type="string", description="Class 5 description", required=False, default_value=""),
            # Model config (de-emphasized; bottom)
            NodeParameter(name="service", type="string", description="Language model service", required=False, default_value="openai", options=["openai", "groq", "ollama"]),
            NodeParameter(name="model", type="string", description="Model name (optional)", required=False, default_value=""),
        ]

    def _define_styling(self) -> NodeStyling:
        return NodeStyling(
            html_template="""
            <div class="intent-node">
                <div class="intent-title">Intent Classification</div>
            <div class="intent-sub">Up to 5 classes</div>
            </div>
            """,
            custom_css="""
            .intent-node { padding: 14px 16px; background:#1f1f1f; border:1.5px solid #22d3ee; border-radius:8px; width:300px; }
            .intent-title { color:#fff; font-size:13px; font-weight:600; margin-bottom:4px; }
            .intent-sub { color:#22d3ee; font-size:11px; opacity:.95; }
            """,
            icon="",
            subtitle="",
            background_color="#1f1f1f",
            border_color="#22d3ee",
            text_color="#ffffff",
            shape="custom",
            width=300,
            height=100,
            css_classes="",
            inline_styles='{"height":"auto"}',
            icon_position="",
        )

    def _define_ui_config(self) -> NodeUIConfig:
        try:
            # Build fixed five class components; user may fill any subset
            class_components: List[Any] = []
            for i in range(1, 6):
                class_components.append(
                    create_textarea(
                        name=f"class_{i}_label",
                        label=f"Class {i} Label",
                        required=False,
                        default_value="",
                        rows=1,
                    )
                )
                class_components.append(
                    create_textarea(
                        name=f"class_{i}_instruction",
                        label=f"Class {i} Description",
                        required=False,
                        default_value="",
                        rows=2,
                    )
                )

            return NodeUIConfig(
                node_id=self.node_id,
                node_name="IntentClassificationNode",
                groups=[
                    UIGroup(
                        name="classes_config",
                        label="Classes",
                        components=class_components,
                        styling={"padding": "16px", "background": "#2a2a2a", "border_radius": "8px", "border": "1px solid #404040"},
                    ),
                    UIGroup(
                        name="model_config",
                        label="Model Configuration (Advanced)",
                        components=[
                            create_select(
                                name="service",
                                label="AI Service",
                                required=False,
                                default_value="openai",
                                options=[
                                    UIOption(value="openai", label="OpenAI"),
                                    UIOption(value="groq", label="Groq"),
                                    UIOption(value="ollama", label="Ollama"),
                                ],
                                searchable=True,
                            ),
                            create_select(
                                name="model",
                                label="Model",
                                required=False,
                                default_value="",
                                options=[UIOption(value="", label="Optional: select a service first")],
                                searchable=True,
                            ),
                        ],
                        collapsible=True,
                        collapsed=True,
                        styling={"padding": "16px", "background": "#2a2a2a", "border_radius": "8px", "border": "1px solid #404040"},
                    ),
                ],
                layout="vertical",
                global_styling={"font_family": "Inter, sans-serif", "color_scheme": "light"},
                dialog_config=DialogConfig(
                    title="Configure IntentClassificationNode",
                    description="Provide class labels/instructions and choose an LLM (optional).",
                    background_color="#1f1f1f",
                    border_color="#22d3ee",
                    text_color="#ffffff",
                    icon="""<svg width=\"24\" height=\"24\" viewBox=\"0 0 24 24\" fill=\"none\" xmlns=\"http://www.w3.org/2000/svg\">\n  <path d=\"M12 20a8 8 0 100-16 8 8 0 000 16z\" stroke=\"#22d3ee\" stroke-width=\"2\" fill=\"none\"/>\n  <path d=\"M8 12h8M12 8v8\" stroke=\"#22d3ee\" stroke-width=\"2\" stroke-linecap=\"round\"/>\n</svg>""",
                    icon_color="#22d3ee",
                    header_background="#1f1f1f",
                    footer_background="#1f1f1f",
                    button_primary_color="#22d3ee",
                    button_secondary_color="#374151",
                ),
            )
        except Exception as e:
            # Fail-safe minimal UI if any rendering error occurs
            print(f"[WARN] IntentClassificationNode UI build failed: {e}")
            return NodeUIConfig(
                node_id=self.node_id,
                node_name="IntentClassificationNode",
                groups=[
                    UIGroup(
                        name="fallback",
                        label="Intent Classifier",
                        components=[
                            create_textarea(name="class_1_label", label="Class 1 Label", required=False, default_value="", rows=1),
                            create_textarea(name="class_1_instruction", label="Class 1 Description", required=False, default_value="", rows=2),
                        ],
                    )
                ],
            )

    def execute(self, inputs: Dict[str, Any], parameters: Dict[str, Any]) -> Dict[str, Any]:
        # Tool availability
        if LanguageModelTool is None:
            return {"intent": "", "confidence": 0.0, "reason": "LanguageModelTool not available"}

        query = str(inputs.get("query", "")).strip()

        # Collect class definitions from parameter slots (1..5)
        classes: List[Dict[str, str]] = []
        for i in range(1, 6):
            label_key = f"class_{i}_label"
            instr_key = f"class_{i}_instruction"
            label = str(parameters.get(label_key, "")).strip()
            instruction = str(parameters.get(instr_key, "")).strip()
            if label:
                classes.append({"label": label, "instruction": instruction})
        if not classes:
            classes = [{"label": "other", "instruction": "General / fallback"}]

        # Build instruction list
        class_lines = []
        labels = []
        for item in classes:
            label = str(item.get("label", "")).strip() or "other"
            instruction = str(item.get("instruction", "")).strip() or ""
            labels.append(label)
            class_lines.append(f"- {label}: {instruction}")

        labels_csv = ", ".join(labels)
        guide = "\n".join(class_lines)

        system_prompt = (
            "You are an intent classifier. Choose exactly one label from the allowed list. "
            "Respond ONLY as compact JSON with keys: intent (string, one of allowed labels), "
            "confidence (float 0..1), reason (string)."
        )

        user_prompt = f"""
Allowed labels: {labels_csv}

Guidelines:
{guide}

Query:
{query}

Return JSON only, e.g. {{"intent":"food","confidence":0.92,"reason":"mentions dishes"}}
"""

        service = parameters.get("service", "openai")
        model = parameters.get("model", "")
        temperature = 0.0  # Fixed for classification
        max_tokens = 256  # Fixed for classification

        tool = LanguageModelTool()
        result = tool.generate_response(
            query=user_prompt,
            service=service,
            model=model if model else None,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        intent = ""
        confidence = 0.0
        reason = ""

        if result and result.get("success") and isinstance(result.get("response"), str):
            text = result["response"].strip()
            # Try to extract JSON
            try:
                start = text.find("{")
                end = text.rfind("}")
                if start != -1 and end != -1 and end > start:
                    payload = json.loads(text[start : end + 1])
                else:
                    payload = json.loads(text)
            except Exception:
                payload = {"intent": text[:64]}

            intent = str(payload.get("intent", "")).strip() or ""
            try:
                confidence = float(payload.get("confidence", 0.0))
            except Exception:
                confidence = 0.0
            reason = str(payload.get("reason", "")).strip()

            # Clamp and validate
            if intent not in labels and labels:
                intent = labels[0]
            confidence = max(0.0, min(1.0, confidence))

        return {"intent": intent, "confidence": confidence, "reason": reason}


