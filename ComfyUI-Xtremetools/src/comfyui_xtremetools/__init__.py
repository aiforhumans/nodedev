"""ComfyUI-Xtremetools package exports.

Expose NODE_CLASS_MAPPINGS so ComfyUI can discover nodes when this
folder is copied into `ComfyUI/custom_nodes`.
"""

from .alias import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
