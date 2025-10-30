import sys
import os

# Add nodes directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'nodes'))

from conditional_node.conditional_node import ConditionalNode


def test_equals_true():
    node = ConditionalNode()
    out = node.run(
        inputs={"left": "Refund Policy", "right": "Refund Policy"},
        parameters={"operator": "equals"}
    )
    assert out["condition"] is True
    assert out["true"] == "Refund Policy"
    assert out["false"] == ""


def test_equals_false():
    node = ConditionalNode()
    out = node.run(
        inputs={"left": "Refund Policy", "right": "Shipping Policy"},
        parameters={"operator": "equals"}
    )
    assert out["condition"] is False
    assert out["true"] == ""
    assert out["false"] == "Refund Policy"


def test_contains_case_insensitive_true():
    node = ConditionalNode()
    out = node.run(
        inputs={"left": "Please tell me about REFUNDS"},
        parameters={"operator": "contains", "right_value": "refunds", "case_sensitive": False}
    )
    assert out["condition"] is True


def test_starts_with_false():
    node = ConditionalNode()
    out = node.run(
        inputs={"left": "hello world"},
        parameters={"operator": "starts_with", "right_value": "world"}
    )
    assert out["condition"] is False


def test_ends_with_true():
    node = ConditionalNode()
    out = node.run(
        inputs={"left": "support@company.com"},
        parameters={"operator": "ends_with", "right_value": "company.com"}
    )
    assert out["condition"] is True


