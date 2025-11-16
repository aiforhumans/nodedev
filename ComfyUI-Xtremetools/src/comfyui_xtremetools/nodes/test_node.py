"""Diagnostic test node to validate the Xtremetools scaffold."""
from __future__ import annotations

from typing import Any

from comfyui_xtremetools.base.node_base import XtremetoolsUtilityNode


class XtremetoolsTestNode(XtremetoolsUtilityNode):
    """Emit a simple text payload for quick workflow testing."""

    CATEGORY = "Xtremetools/Diagnostics"
    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("text", "info")
    FUNCTION = "emit"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "text": ("STRING", {"default": "Xtremetools test node", "multiline": True}),
                "repeat_count": ("INT", {"default": 1, "min": 1, "max": 5}),
            },
            "optional": {
                "uppercase": ("BOOLEAN", {"default": False}),
                "delimiter": ("STRING", {"default": " "}),
            },
        }

    def emit(self, text: str, repeat_count: int = 1, uppercase: bool = False, delimiter: str = " ") -> tuple[str, str]:
        sanitized = text.strip() or "Xtremetools test node"
        payload = delimiter.join([sanitized] * repeat_count)
        if uppercase:
            payload = payload.upper()

        info = self.build_info("Test Node", emoji="🧪")
        info.add(f"Repeat count: {repeat_count}")
        info.add(f"Uppercase: {uppercase}")
        info.add(f"Delimiter: '{delimiter}'")
        info.add(f"Characters: {len(payload)}")

        return self.ensure_tuple(payload, info.render())


NODE_CLASS_MAPPINGS = {
    "XtremetoolsTestNode": XtremetoolsTestNode,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XtremetoolsTestNode": "Test Node",
}
