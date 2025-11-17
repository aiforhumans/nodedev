"""Tests for LM Studio settings and text generation nodes."""
from __future__ import annotations

import pytest

from comfyui_xtremetools.base.lm_studio import (
    LMStudioAPIError,
    LMStudioGenerationSettings,
    LMStudioModelSettings,
    LMStudioServerSettings,
)
from comfyui_xtremetools.nodes.lm_studio_settings import (
    XtremetoolsLMStudioGenerationSettings,
    XtremetoolsLMStudioModelSettings,
    XtremetoolsLMStudioServerSettings,
)
from comfyui_xtremetools.nodes.lm_studio_text import XtremetoolsLMStudioText


def test_lm_studio_server_settings_node_outputs_dataclass() -> None:
    node = XtremetoolsLMStudioServerSettings()
    settings, info = node.build_server_settings("http://localhost:9000", timeout_seconds=42)

    assert isinstance(settings, LMStudioServerSettings)
    assert settings.server_url == "http://localhost:9000"
    assert settings.timeout == 42
    assert "Timeout" in info


def test_lm_studio_model_settings_node_outputs_dataclass() -> None:
    node = XtremetoolsLMStudioModelSettings()
    settings, info = node.build_model_settings("phi-local", fallback_to_default=False)

    assert isinstance(settings, LMStudioModelSettings)
    assert settings.model == "phi-local"
    assert settings.fallback_to_default is False
    assert "phi-local" in info


def test_lm_studio_generation_settings_node_outputs_dataclass() -> None:
    node = XtremetoolsLMStudioGenerationSettings()
    settings, info = node.build_generation_settings(
        temperature=0.33,
        max_tokens=128,
        response_format="json_object",
    )

    assert isinstance(settings, LMStudioGenerationSettings)
    assert settings.temperature == 0.33
    assert settings.max_tokens == 128
    assert settings.response_format == {"type": "json_object"}
    assert "json_object" in info


@pytest.mark.usefixtures("fake_lm_studio_server")
def test_lm_studio_node_success(fake_lm_studio_server) -> None:
    fake_lm_studio_server.queue(
        {
            "model": "phi-local",
            "choices": [
                {
                    "message": {"content": "Hello from LM Studio"},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 5},
        }
    )

    node = XtremetoolsLMStudioText()
    text, info = node.generate("Say hi")

    assert text == "Hello from LM Studio"
    assert "Model: phi-local" in info
    assert "Tokens (prompt/completion): 10/5" in info


def test_lm_studio_node_error(fake_lm_studio_server) -> None:
    fake_lm_studio_server.queue({"error": "model not loaded"})
    node = XtremetoolsLMStudioText()

    with pytest.raises(LMStudioAPIError):
        node.generate("Say hi")


def test_lm_studio_request_has_text_response(fake_lm_studio_server) -> None:
    fake_lm_studio_server.queue(
        {
            "model": "phi-local",
            "choices": [
                {
                    "message": {"content": "ok"},
                    "finish_reason": "stop",
                }
            ],
        }
    )

    node = XtremetoolsLMStudioText()
    node.generate("Say hi")

    assert fake_lm_studio_server.requests[0]["body"]["response_format"] == {"type": "text"}


def test_lm_studio_node_honors_settings(fake_lm_studio_server) -> None:
    fake_lm_studio_server.queue(
        {
            "model": "phi-local",
            "choices": [
                {
                    "message": {"content": "ok"},
                    "finish_reason": "stop",
                }
            ],
        }
    )

    server_settings, _ = XtremetoolsLMStudioServerSettings().build_server_settings(
        "http://127.0.0.1:9001",
        timeout_seconds=15,
    )
    model_settings, _ = XtremetoolsLMStudioModelSettings().build_model_settings(
        "phi-local",
        fallback_to_default=False,
    )
    generation_settings, _ = XtremetoolsLMStudioGenerationSettings().build_generation_settings(
        temperature=0.2,
        max_tokens=64,
        response_format="json_object",
    )

    node = XtremetoolsLMStudioText()
    node.generate(
        "Say hi",
        server_settings=server_settings,
        model_settings=model_settings,
        generation_settings=generation_settings,
    )

    recorded = fake_lm_studio_server.requests[0]
    assert recorded["url"].startswith("http://127.0.0.1:9001")
    assert recorded["timeout"] == 15
    assert recorded["body"]["model"] == "phi-local"
    assert recorded["body"]["temperature"] == 0.2
    assert recorded["body"]["max_tokens"] == 64
    assert recorded["body"]["response_format"] == {"type": "json_object"}
