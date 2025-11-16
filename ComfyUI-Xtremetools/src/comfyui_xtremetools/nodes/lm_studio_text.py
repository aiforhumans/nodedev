"""Text generation node powered by LM Studio local models."""
from __future__ import annotations

from typing import Any

from comfyui_xtremetools.base.lm_studio import LMStudioBaseNode, LMStudioAPIError


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
    ) -> tuple[str, str]:
        messages = self.build_messages(prompt, user_input=user_input, system_prompt=system_prompt)

        try:
            result = self.invoke_chat_completion(
                messages=messages,
                server_url=server_url,
                model=model or None,
                temperature=temperature,
                max_tokens=max_tokens,
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
