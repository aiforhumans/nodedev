"""Utility helpers for workflow generation + JSON guardrails."""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import BaseModel

from .config import get_environment_config
from .logger import get_logger
from .node_discovery import get_type_registry

# Copilot: ensure new functions keep type hints and docstrings.

logger = get_logger("xtremetools.generator")

_STRUCTURED_MODE_ACTIVE: dict[str, bool] = {"active": False}


class GenerationTelemetry(BaseModel):
    """Captures structured details for workflow generation attempts."""

    extraction_method: str
    structured_output: bool
    retry_count: int
    node_count: int | None = None
    link_count: int | None = None
    warnings: list[str] = []


def _read_supported_models_file(path: Path) -> set[str]:
    if not path.exists():
        logger.warning("supported_models.json missing at %s", path)
        return set()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:  # pragma: no cover - invalid user file
        logger.error("Invalid supported_models.json: %s", exc)
        return set()
    models = payload.get("structured_json_capable", [])
    return {str(model).strip() for model in models if model}


@lru_cache(maxsize=1)
def _supported_models() -> set[str]:
    config = get_environment_config()
    return _read_supported_models_file(config.supported_models_path)


def model_supports_structured_json(model_name: str | None) -> bool:
    if not model_name:
        return False
    allowed = _supported_models()
    supported = model_name in allowed
    if not supported:
        logger.warning(
            "Model %s not whitelisted for strict JSON; using fallback mode.",
            model_name,
        )
    _STRUCTURED_MODE_ACTIVE["active"] = supported
    return supported


def get_structured_mode_flag() -> bool:
    return _STRUCTURED_MODE_ACTIVE["active"]


def extract_first_json_block(text: str) -> tuple[str, str]:
    """Return the first plausible JSON block + extraction strategy."""

    clean = text.strip()
    if clean.startswith("{") and clean.endswith("}"):
        return clean, "raw"

    if "```" in clean:
        start = clean.find("```json")
        if start == -1:
            start = clean.find("```")
        if start != -1:
            start = clean.find("\n", start)
            if start != -1:
                end = clean.find("```", start)
                if end != -1:
                    return clean[start:end].strip(), "fence"

    first = clean.find("{")
    last = clean.rfind("}")
    if first != -1 and last > first:
        return clean[first:last + 1], "braces"

    return "{}", "fallback"


def clamp_links_to_registry(workflow_json: str) -> str:
    """Clean up links so they only connect compatible socket types."""

    registry = get_type_registry()
    try:
        workflow = json.loads(workflow_json)
    except json.JSONDecodeError:
        return workflow_json

    nodes = {node["id"]: node for node in workflow.get("nodes", []) if isinstance(node, dict) and isinstance(node.get("id"), int)}
    links = []
    bad_links = 0
    for link in workflow.get("links", []):
        if not (isinstance(link, list) and len(link) >= 6):
            continue
        link_id, source_id, source_out_idx, target_id, target_input_idx, declared_type = link
        source_node = nodes.get(source_id)
        target_node = nodes.get(target_id)
        if not source_node or not target_node:
            bad_links += 1
            continue
        source_outputs = source_node.get("outputs", []) or []
        target_inputs = target_node.get("inputs", []) or []
        if source_out_idx >= len(source_outputs) or target_input_idx >= len(target_inputs):
            bad_links += 1
            continue
        source_type = source_outputs[source_out_idx].get("type")
        target_type = target_inputs[target_input_idx].get("type")
        if not registry.is_link_allowed(source_type, target_type):
            bad_links += 1
            continue
        links.append(link)

    if bad_links:
        logger.warning("Pruned %s incompatible links", bad_links)
    workflow["links"] = links
    workflow["last_link_id"] = max((link[0] for link in links), default=0)
    return json.dumps(workflow, ensure_ascii=False)


__all__ = [
    "GenerationTelemetry",
    "model_supports_structured_json",
    "get_structured_mode_flag",
    "extract_first_json_block",
    "clamp_links_to_registry",
]
