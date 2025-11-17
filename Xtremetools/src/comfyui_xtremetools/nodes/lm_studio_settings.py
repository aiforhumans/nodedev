"""Composable nodes that emit LM Studio configuration objects."""
from __future__ import annotations

from typing import Any

from comfyui_xtremetools.base.lm_studio import (
    LMStudioBaseNode,
    LMStudioGenerationSettings,
    LMStudioModelSettings,
    LMStudioServerSettings,
)


class _LMStudioSettingsBase(LMStudioBaseNode):
    CATEGORY = "🤖 Xtremetools/🤖 LM Studio/⚙️ Settings"


class XtremetoolsLMStudioServerSettings(_LMStudioSettingsBase):
    """Build server configuration shared by downstream LM Studio nodes."""

    RETURN_TYPES = ("LM_STUDIO_SERVER", "STRING")
    RETURN_NAMES = ("server_settings", "info")
    FUNCTION = "build_server_settings"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "server_url": ("STRING", {"default": cls.DEFAULT_SERVER_URL}),
                "timeout_seconds": ("FLOAT", {"default": float(cls.DEFAULT_TIMEOUT), "min": 1.0, "max": 300.0}),
            },
            "optional": {},
        }

    def build_server_settings(self, server_url: str, timeout_seconds: float = 60.0) -> tuple[LMStudioServerSettings, str]:
        normalized_url = (server_url or self.DEFAULT_SERVER_URL).strip() or self.DEFAULT_SERVER_URL
        timeout = max(timeout_seconds, 1.0)
        settings = LMStudioServerSettings(server_url=normalized_url, timeout=timeout)

        info = self.build_info("Server Settings", emoji="SVR")
        info.add(f"URL: {normalized_url}")
        info.add(f"Timeout: {timeout:.0f}s")
        return self.ensure_tuple(settings, info.render())


class XtremetoolsLMStudioModelSettings(_LMStudioSettingsBase):
    """Configure model selection (and fallback) separately from prompts."""

    RETURN_TYPES = ("LM_STUDIO_MODEL", "STRING")
    RETURN_NAMES = ("model_settings", "info")
    FUNCTION = "build_model_settings"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "model": ("STRING", {"default": ""}),
                "fallback_to_default": ("BOOLEAN", {"default": True}),
            },
            "optional": {},
        }

    def build_model_settings(
        self,
        model: str,
        fallback_to_default: bool = True,
    ) -> tuple[LMStudioModelSettings, str]:
        normalized = model.strip()
        settings = LMStudioModelSettings(model=normalized or None, fallback_to_default=fallback_to_default)

        info = self.build_info("Model Settings", emoji="MDL")
        info.add(f"Preferred model: {normalized or 'default'}")
        info.add(f"Fallback allowed: {fallback_to_default}")
        return self.ensure_tuple(settings, info.render())


class XtremetoolsLMStudioGenerationSettings(_LMStudioSettingsBase):
    """Manage sampling + response format knobs as a reusable output."""

    RETURN_TYPES = ("LM_STUDIO_GENERATION", "STRING")
    RETURN_NAMES = ("generation_settings", "info")
    FUNCTION = "build_generation_settings"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
                "max_tokens": ("INT", {"default": 256, "min": 16, "max": 8192}),
                "response_format": (
                    "STRING",
                    {"default": "text", "choices": ["text", "json_object"]},
                ),
            },
            "optional": {},
        }

    def build_generation_settings(
        self,
        temperature: float,
        max_tokens: int,
        response_format: str = "text",
    ) -> tuple[LMStudioGenerationSettings, str]:
        format_payload: dict[str, Any]
        if response_format == "json_object":
            format_payload = {"type": "json_object"}
        else:
            format_payload = {"type": "text"}

        settings = LMStudioGenerationSettings(
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=format_payload,
        )

        info = self.build_info("Generation Settings", emoji="GEN")
        info.add(f"Temperature: {temperature}")
        info.add(f"Max tokens: {max_tokens}")
        info.add(f"Format: {format_payload['type']}")
        return self.ensure_tuple(settings, info.render())


NODE_CLASS_MAPPINGS = {
    "XtremetoolsLMStudioServerSettings": XtremetoolsLMStudioServerSettings,
    "XtremetoolsLMStudioModelSettings": XtremetoolsLMStudioModelSettings,
    "XtremetoolsLMStudioGenerationSettings": XtremetoolsLMStudioGenerationSettings,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XtremetoolsLMStudioServerSettings": "LM Studio Server Settings",
    "XtremetoolsLMStudioModelSettings": "LM Studio Model Settings",
    "XtremetoolsLMStudioGenerationSettings": "LM Studio Generation Settings",
}
