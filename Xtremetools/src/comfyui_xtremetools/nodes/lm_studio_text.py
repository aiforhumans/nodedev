"""Text generation node powered by LM Studio local models."""
from __future__ import annotations

from typing import Any

from comfyui_xtremetools.base.lm_studio import (
    LMStudioAPIError,
    LMStudioBaseNode,
    LMStudioGenerationSettings,
    LMStudioModelSettings,
    LMStudioServerSettings,
)


class XtremetoolsLMStudioText(LMStudioBaseNode):
    """Call LM Studio chat completions and return the generated text."""

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "info")
    FUNCTION = "generate"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "prompt": ("STRING", {"default": "Describe the scene", "multiline": True}),
            },
            "optional": {
                "user_input": ("STRING", {"default": "", "multiline": True}),
                "system_prompt": ("STRING", {"default": "You are a helpful assistant.", "multiline": True}),
                "server_url": ("STRING", {"default": cls.DEFAULT_SERVER_URL}),
                "model": ("STRING", {"default": ""}),
                "temperature": ("FLOAT", {"default": 0.7, "min": 0.0, "max": 2.0, "step": 0.05}),
                "max_tokens": ("INT", {"default": 256, "min": 16, "max": 8192}),
                "server_settings": ("LM_STUDIO_SERVER",),
                "model_settings": ("LM_STUDIO_MODEL",),
                "generation_settings": ("LM_STUDIO_GENERATION",),
            },
        }

    def generate(
        self,
        prompt: str,
        user_input: str = "",
        system_prompt: str | None = None,
        server_url: str | None = None,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 256,
        server_settings: LMStudioServerSettings | None = None,
        model_settings: LMStudioModelSettings | None = None,
        generation_settings: LMStudioGenerationSettings | None = None,
    ) -> tuple[str, str]:
        server_config = server_settings or LMStudioServerSettings()
        model_config = model_settings or LMStudioModelSettings()
        generation_config = generation_settings or LMStudioGenerationSettings()

        final_server_url = (server_config.server_url or server_url or self.DEFAULT_SERVER_URL).strip()
        final_model = model or model_config.model
        if model_config.fallback_to_default and not final_model:
            final_model = None

        final_temperature = generation_config.temperature if generation_config.temperature is not None else temperature
        final_max_tokens = generation_config.max_tokens if generation_config.max_tokens is not None else max_tokens
        final_response_format = generation_config.response_format

        timeout = server_config.timeout if server_config.timeout else None

        messages = self.build_messages(prompt, user_input=user_input, system_prompt=system_prompt)

        try:
            result = self.invoke_chat_completion(
                messages=messages,
                server_url=final_server_url,
                model=final_model or None,
                temperature=final_temperature,
                max_tokens=final_max_tokens,
                timeout=timeout,
                response_format=final_response_format,
            )
        except LMStudioAPIError as exc:
            raise LMStudioAPIError(f"LM Studio request failed: {exc}") from exc

        info = self.build_completion_info(result)
        return self.ensure_tuple(result.text, info)


NODE_CLASS_MAPPINGS = {
    "XtremetoolsLMStudioText": XtremetoolsLMStudioText,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XtremetoolsLMStudioText": "LM Studio Text",
}
