"""Workflow validation + schema enforcement helpers."""
from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field, ValidationError

from .config import get_environment_config
from .logger import get_logger

logger = get_logger("xtremetools.workflow_validator")

# Copilot: generate docstrings + annotations for new validator helpers.

_LAST_VALIDATION_STATE: dict[str, bool | None] = {"passed": None}
_SCHEMA_CACHE: dict[str, Any] | None = None


class SocketModel(BaseModel):
    name: str
    type: str | None = None
    link: int | None = None
    links: list[int] | None = None


class NodeModel(BaseModel):
    id: int
    type: str
    pos: list[float] | None = None
    inputs: list[SocketModel] = Field(default_factory=list)
    outputs: list[SocketModel] = Field(default_factory=list)


class WorkflowModel(BaseModel):
    last_node_id: int
    last_link_id: int
    nodes: list[NodeModel] = Field(default_factory=list)
    links: list[list[Any]] = Field(default_factory=list)
    groups: list[dict[str, Any]] = Field(default_factory=list)
    config: dict[str, Any] = Field(default_factory=dict)
    extra: dict[str, Any] = Field(default_factory=dict)
    version: float | int | str | None = Field(default=0.4)


class WorkflowValidationResult(BaseModel):
    report: str
    is_valid: bool
    workflow_json: str
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


def _load_schema_text() -> str:
    config = get_environment_config()
    path = config.workflow_schema_path
    if not path.exists():
        logger.warning("Workflow schema not found at %s", path)
        return "{}"
    return path.read_text(encoding="utf-8")


def _ensure_schema_loaded() -> dict[str, Any]:
    global _SCHEMA_CACHE
    if _SCHEMA_CACHE is None:
        try:
            _SCHEMA_CACHE = json.loads(_load_schema_text())
        except json.JSONDecodeError as exc:  # pragma: no cover - schema file edited incorrectly
            logger.error("Workflow schema file corrupted: %s", exc)
            _SCHEMA_CACHE = {}
    return _SCHEMA_CACHE


def validate_workflow_json(workflow_json: str, auto_fix: bool = True) -> WorkflowValidationResult:
    """Validate workflow JSON using Pydantic + schema heuristics."""

    errors: list[str] = []
    warnings: list[str] = []
    schema = _ensure_schema_loaded()

    if not workflow_json.strip():
        errors.append("workflow_json payload is empty")
        return WorkflowValidationResult(report="INVALID: empty workflow", is_valid=False, workflow_json="{}", errors=errors)

    try:
        payload = json.loads(workflow_json)
    except json.JSONDecodeError as exc:
        errors.append(f"JSON parse error: {exc}")
        return WorkflowValidationResult(report="INVALID: parse error", is_valid=False, workflow_json="{}", errors=errors)

    try:
        workflow = WorkflowModel(**payload)
    except ValidationError as exc:
        errors.append(f"Schema validation failed: {exc}")
        return WorkflowValidationResult(report="INVALID: schema rejection", is_valid=False, workflow_json=workflow_json, errors=errors)

    node_ids = {node.id for node in workflow.nodes}
    link_ids = set()

    for index, link in enumerate(workflow.links):
        if len(link) != 6:
            errors.append(f"Link {index} malformed: expected 6 fields")
            continue
        link_id = link[0]
        if link_id in link_ids:
            errors.append(f"Duplicate link id {link_id}")
        link_ids.add(link_id)
        source_id, target_id = link[1], link[3]
        if source_id not in node_ids:
            errors.append(f"Link {link_id} references unknown source node {source_id}")
        if target_id not in node_ids:
            errors.append(f"Link {link_id} references unknown target node {target_id}")

    if not errors and auto_fix:
        last_node_expected = max(node_ids, default=0)
        last_link_expected = max(link_ids, default=0)
        if workflow.last_node_id < last_node_expected:
            warnings.append(
                f"last_node_id ({workflow.last_node_id}) < highest node id ({last_node_expected}); auto-fixing"
            )
            workflow.last_node_id = last_node_expected
        if workflow.last_link_id < last_link_expected:
            warnings.append(
                f"last_link_id ({workflow.last_link_id}) < highest link id ({last_link_expected}); auto-fixing"
            )
            workflow.last_link_id = last_link_expected

    report_lines = [
        "XTREMETOOLS WORKFLOW VALIDATION",
        "===============================",
        f"Nodes: {len(workflow.nodes)}",
        f"Links: {len(workflow.links)}",
        f"last_node_id: {workflow.last_node_id}",
        f"last_link_id: {workflow.last_link_id}",
    ]

    required_fields = schema.get("required", []) if isinstance(schema, dict) else []
    for field in required_fields:
        if field not in payload:
            errors.append(f"Missing top-level required field: {field}")

    if errors:
        for issue in errors:
            report_lines.append(f"ERROR: {issue}")
    if warnings:
        for warn in warnings:
            report_lines.append(f"WARN: {warn}")

    is_valid = not errors
    _LAST_VALIDATION_STATE["passed"] = is_valid and not warnings

    updated_json = workflow.model_dump_json(by_alias=True)
    return WorkflowValidationResult(
        report="\n".join(report_lines),
        is_valid=is_valid,
        workflow_json=updated_json,
        errors=errors,
        warnings=warnings,
    )


def get_last_validation_passed() -> bool | None:
    return _LAST_VALIDATION_STATE["passed"]


__all__ = [
    "WorkflowValidationResult",
    "validate_workflow_json",
    "get_last_validation_passed",
]
