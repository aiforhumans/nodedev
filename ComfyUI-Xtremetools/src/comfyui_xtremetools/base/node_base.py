"""Abstract base classes for Xtremetools nodes."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar

from .info import InfoFormatter


class XtremetoolsBaseNode(ABC):
    """Shared helpers for all Xtremetools custom nodes."""

    CATEGORY: ClassVar[str] = "Xtremetools/Base"
    OUTPUT_NODE: ClassVar[bool] = False

    RETURN_TYPES: ClassVar[tuple[str, ...]] = ()
    RETURN_NAMES: ClassVar[tuple[str, ...]] = ()
    FUNCTION: ClassVar[str]

    @classmethod
    @abstractmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        """Describe required and optional inputs for the node."""

    @staticmethod
    def ensure_tuple(*values: Any) -> tuple[Any, ...]:
        """Return values as a tuple; ComfyUI expects tuple outputs."""
        return tuple(values)

    def build_info(self, title: str, emoji: str = "🛠") -> InfoFormatter:
        """Convenience wrapper to create standardized info strings."""
        return InfoFormatter(title=title, emoji=emoji)


class XtremetoolsUtilityNode(XtremetoolsBaseNode):
    """Base class for lightweight text/utility helpers."""

    CATEGORY: ClassVar[str] = "Xtremetools/Utility"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:  # pragma: no cover - abstract pattern
        return {"required": {}, "optional": {}}
