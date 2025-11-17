"""Example prompt helper node to validate the scaffold."""
from __future__ import annotations

from typing import Any

from comfyui_xtremetools.base.node_base import XtremetoolsUtilityNode


class XtremetoolsPromptJoiner(XtremetoolsUtilityNode):
    """Simple text node that concatenates two prompt fragments."""

    CATEGORY = "🤖 Xtremetools/🧩 Prompt Tools"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("prompt", "info")
    FUNCTION = "build_prompt"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "primary": ("STRING", {"default": "Describe the scene", "multiline": True}),
                "secondary": ("STRING", {"default": "Add lighting details", "multiline": True}),
            },
            "optional": {
                "delimiter": ("STRING", {"default": " | "}),
            },
        }

    def build_prompt(self, primary: str, secondary: str, delimiter: str = " | ") -> tuple[str, str]:
        parts = [segment.strip() for segment in (primary, secondary) if segment.strip()]
        prompt = delimiter.join(parts)

        info = self.build_info("Prompt Joiner")
        info.add(f"Primary length: {len(primary)}")
        info.add(f"Secondary length: {len(secondary)}")
        info.add(f"Delimiter: '{delimiter}'")

        return self.ensure_tuple(prompt, info.render())


NODE_CLASS_MAPPINGS = {
    "XtremetoolsPromptJoiner": XtremetoolsPromptJoiner,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XtremetoolsPromptJoiner": "Prompt Joiner",
}
