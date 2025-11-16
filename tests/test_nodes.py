"""Smoke tests for ComfyUI-Xtremetools nodes."""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = PROJECT_ROOT / "ComfyUI-Xtremetools" / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from comfyui_xtremetools.alias import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
from comfyui_xtremetools.base.lm_studio import LMStudioAPIError
from comfyui_xtremetools.nodes.example_prompt_tool import XtremetoolsPromptJoiner
from comfyui_xtremetools.nodes.lm_studio_text import XtremetoolsLMStudioText
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
    assert "XtremetoolsLMStudioText" in NODE_CLASS_MAPPINGS
    assert NODE_DISPLAY_NAME_MAPPINGS["XtremetoolsTestNode"] == "Test Node"


class _DummyResponse:
    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    def __enter__(self) -> "_DummyResponse":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001
        return None

    def read(self) -> bytes:
        return json.dumps(self._payload).encode("utf-8")


def test_lm_studio_node_success(monkeypatch) -> None:
    payload = {
        "model": "phi-local",
        "choices": [
            {
                "message": {"content": "Hello from LM Studio"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 10, "completion_tokens": 5},
    }

    def fake_urlopen(request, timeout=None):  # noqa: ANN001
        return _DummyResponse(payload)

    monkeypatch.setattr(
        "comfyui_xtremetools.base.lm_studio.urllib.request.urlopen",
        fake_urlopen,
    )

    node = XtremetoolsLMStudioText()
    text, info = node.generate("Say hi")

    assert text == "Hello from LM Studio"
    assert "Model: phi-local" in info
    assert "Tokens (prompt/completion): 10/5" in info


def test_lm_studio_node_error(monkeypatch) -> None:
    payload = {"error": "model not loaded"}

    def fake_urlopen(request, timeout=None):  # noqa: ANN001
        return _DummyResponse(payload)

    monkeypatch.setattr(
        "comfyui_xtremetools.base.lm_studio.urllib.request.urlopen",
        fake_urlopen,
    )

    node = XtremetoolsLMStudioText()
    with pytest.raises(LMStudioAPIError):
        node.generate("Say hi")


def test_lm_studio_request_has_text_response(monkeypatch) -> None:
    captured: dict[str, object] = {}

    payload = {
        "model": "phi-local",
        "choices": [
            {
                "message": {"content": "ok"},
                "finish_reason": "stop",
            }
        ],
    }

    def fake_urlopen(request, timeout=None):  # noqa: ANN001
        captured["body"] = json.loads(request.data.decode("utf-8"))
        return _DummyResponse(payload)

    monkeypatch.setattr(
        "comfyui_xtremetools.base.lm_studio.urllib.request.urlopen",
        fake_urlopen,
    )

    node = XtremetoolsLMStudioText()
    node.generate("Say hi")

    assert captured["body"]["response_format"] == {"type": "text"}
