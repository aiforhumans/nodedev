"""Lightweight MCP harness for exercising Xtremetools nodes."""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable


@dataclass
class MCPCallResult:
    """Simple result wrapper mimicking MCP text responses."""

    tool: str
    outputs: tuple[Any, ...]
    telemetry: list[str]
    is_error: bool = False

    def ensure_ascii(self) -> None:
        for item in self.telemetry:
            item.encode("ascii")


class MCPToolAdapter:
    """Wraps a node class so it can be invoked via FakeMCPClient."""

    def __init__(self, node_cls: type[Any], name: str | None = None):
        self.node_cls = node_cls
        self.name = name or node_cls.__name__
        self.function_name = getattr(node_cls, "FUNCTION", None)
        if not self.function_name:
            raise ValueError(f"Node {node_cls.__name__} is missing FUNCTION attribute")

    def build_schema(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "category": getattr(self.node_cls, "CATEGORY", ""),
            "function": self.function_name,
            "return_types": tuple(getattr(self.node_cls, "RETURN_TYPES", ())),
            "return_names": tuple(getattr(self.node_cls, "RETURN_NAMES", ())),
            "input_types": self.node_cls.INPUT_TYPES() if hasattr(self.node_cls, "INPUT_TYPES") else {},
        }

    def invoke(self, **arguments: Any) -> MCPCallResult:
        node = self.node_cls()
        func = getattr(node, self.function_name)
        result = func(**arguments)
        outputs = result if isinstance(result, tuple) else (result,)
        telemetry = [self._coerce_text(value) for value in outputs if isinstance(value, str)]
        return MCPCallResult(tool=self.name, outputs=outputs, telemetry=telemetry)

    @staticmethod
    def _coerce_text(value: Any) -> str:
        if isinstance(value, str):
            return value
        if is_dataclass(value):
            return str(asdict(value))
        return str(value)


class FakeMCPClient:
    """Routes requests to registered tool adapters and records transcripts."""

    def __init__(self, adapters: Iterable[MCPToolAdapter]):
        self._adapters = {adapter.name: adapter for adapter in adapters}
        self.transcript: list[dict[str, Any]] = []

    def call_tool(self, name: str, arguments: dict[str, Any]) -> MCPCallResult:
        if name not in self._adapters:
            raise KeyError(f"Unknown MCP tool: {name}")
        adapter = self._adapters[name]
        result = adapter.invoke(**arguments)
        self.transcript.append({"name": name, "args": arguments, "result": result})
        return result


def build_node_contract(node_name: str, node_cls: type[Any]) -> dict[str, Any]:
    """Create a deterministic contract dictionary for a node class."""

    adapter = MCPToolAdapter(node_cls, name=node_name)
    schema = adapter.build_schema()
    schema["inputs"] = schema.pop("input_types")
    return schema
