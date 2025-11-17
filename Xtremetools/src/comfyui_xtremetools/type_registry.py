"""Typed registry of ComfyUI node socket information."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from pydantic import BaseModel, Field

from .logger import get_logger

# Copilot: keep docstrings + annotations aligned for registry helpers.

logger = get_logger("xtremetools.type_registry")


class SocketDefinition(BaseModel):
    name: str
    type: str | None = None


class NodeSignature(BaseModel):
    type: str
    inputs: list[SocketDefinition] = Field(default_factory=list)
    outputs: list[SocketDefinition] = Field(default_factory=list)


class TypeRegistry(BaseModel):
    """Lightweight compatibility registry built from ComfyUI /object_info."""

    nodes: dict[str, NodeSignature] = Field(default_factory=dict)
    compatibility_overrides: dict[str, set[str]] = Field(default_factory=dict)

    def register(self, node_type: str, inputs: Iterable[dict[str, Any]], outputs: Iterable[dict[str, Any]]) -> None:
        signature = NodeSignature(
            type=node_type,
            inputs=[SocketDefinition(**{"name": raw.get("name", ""), "type": raw.get("type")}) for raw in inputs],
            outputs=[SocketDefinition(**{"name": raw.get("name", ""), "type": raw.get("type")}) for raw in outputs],
        )
        self.nodes[node_type] = signature
        logger.debug("Registered node type %s", node_type)

    def is_link_allowed(self, output_type: str | None, input_type: str | None) -> bool:
        if not output_type or not input_type:
            return False
        if output_type == input_type:
            return True
        allowed_targets = self.compatibility_overrides.get(output_type, set())
        return input_type in allowed_targets

    def build_from_object_info(self, payload: dict[str, Any]) -> None:
        self.nodes.clear()
        category_map = payload.get("categories", {})
        for nodes in category_map.values():
            for node in nodes:
                node_type = node.get("name") or node.get("display_name")
                if not node_type:
                    continue
                inputs = node.get("inputs", [])
                outputs = node.get("outputs", [])
                self.register(node_type, inputs, outputs)

        # Build loose STRING compatibility heuristics
        string_outputs: set[str] = set()
        for signature in self.nodes.values():
            if any(sock.type == "STRING" for sock in signature.outputs):
                string_outputs.add(signature.type)

        for signature in self.nodes.values():
            for socket in signature.inputs:
                if socket.type == "STRING":
                    for provider in string_outputs:
                        self.compatibility_overrides.setdefault("STRING", set()).add("STRING")
                        self.compatibility_overrides.setdefault(provider, set()).add("STRING")

    def describe(self) -> dict[str, Any]:
        return {
            "nodes": len(self.nodes),
            "compatibility_rules": {key: sorted(value) for key, value in self.compatibility_overrides.items()},
        }


def create_registry() -> TypeRegistry:
    registry = TypeRegistry()
    return registry


__all__ = [
    "SocketDefinition",
    "NodeSignature",
    "TypeRegistry",
    "create_registry",
]
