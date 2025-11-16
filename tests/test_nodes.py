"""Smoke tests for ComfyUI-Xtremetools nodes."""
from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "ComfyUI-Xtremetools" / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from comfyui_xtremetools.alias import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from comfyui_xtremetools.nodes.example_prompt_tool import XtremetoolsPromptJoiner
from comfyui_xtremetools.nodes.test_node import XtremetoolsTestNode


def test_prompt_joiner_returns_tuple() -> None:
    node = XtremetoolsPromptJoiner()
    prompt, info = node.build_prompt("hello", "world", delimiter=", ")

    assert isinstance(prompt, str)
    assert isinstance(info, str)
    assert (prompt, info) == (prompt, info)  # tuple integrity already ensured
    assert prompt == "hello, world"


def test_test_node_uppercase_behavior() -> None:
    node = XtremetoolsTestNode()
    text, info = node.emit("ping", repeat_count=2, uppercase=True, delimiter="-")

    assert text == "PING-PING"
    assert "Uppercase: True" in info
    assert "Repeat count: 2" in info


def test_alias_registry_contains_nodes() -> None:
    assert "XtremetoolsPromptJoiner" in NODE_CLASS_MAPPINGS
    assert "XtremetoolsTestNode" in NODE_CLASS_MAPPINGS
    assert NODE_DISPLAY_NAME_MAPPINGS["XtremetoolsTestNode"] == "Test Node"
