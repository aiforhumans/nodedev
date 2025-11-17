"""Workflow-related node tests."""
from __future__ import annotations

import json

from comfyui_xtremetools.nodes.lm_studio_settings import (
    XtremetoolsLMStudioModelSettings,
    XtremetoolsLMStudioServerSettings,
)
from comfyui_xtremetools.nodes.workflow_generator import (
    XtremetoolsWorkflowExporter,
    XtremetoolsWorkflowGenerator,
    XtremetoolsWorkflowRequest,
    XtremetoolsWorkflowValidator,
)


def test_workflow_request_builds_structured_prompt() -> None:
    node = XtremetoolsWorkflowRequest()
    request, info = node.build_request(
        user_description="Create a simple prompt combining workflow",
        workflow_type="prompt_engineering",
        output_format="text",
        complexity="simple",
    )

    assert isinstance(request, str)
    assert isinstance(info, str)
    assert "WORKFLOW GENERATION REQUEST" in request
    assert "TYPE: prompt_engineering" in request
    assert "COMPLEXITY: simple" in request
    assert "Create a simple prompt combining workflow" in request
    assert "Request Type" in info
    assert "simple" in info


def test_workflow_request_with_required_nodes() -> None:
    node = XtremetoolsWorkflowRequest()
    request, info = node.build_request(
        user_description="Test workflow",
        workflow_type="lm_studio_pipeline",
        required_nodes="XtremetoolsLMStudioStylePreset, XtremetoolsLMStudioPromptWeighter",
        output_format="SDXL prompt",
        complexity="moderate",
    )

    assert "REQUIRED NODES:" in request
    assert "StylePreset" in request
    assert "PromptWeighter" in request
    assert "Required Nodes" in info


def test_workflow_request_empty_required_nodes() -> None:
    node = XtremetoolsWorkflowRequest()
    request, _ = node.build_request(
        user_description="Test",
        workflow_type="custom",
        required_nodes="",
        output_format="text",
        complexity="simple",
    )

    assert "REQUIRED NODES:" not in request


def test_workflow_validator_detects_invalid_json() -> None:
    node = XtremetoolsWorkflowValidator()
    report, is_valid, info = node.validate_workflow('{"invalid": json}')

    assert not is_valid
    assert "JSON parse error" in report
    assert "Invalid JSON" in info


def test_workflow_validator_accepts_valid_json(workflow_builder) -> None:
    payload = workflow_builder(
        last_node_id=1,
        nodes=[{"id": 1, "type": "XtremetoolsTestNode", "pos": [100, 100]}],
    )
    node = XtremetoolsWorkflowValidator()
    report, is_valid, info = node.validate_workflow(json.dumps(payload))

    assert is_valid
    assert "VALID" in report
    assert "Valid" in info


def test_workflow_validator_detects_missing_fields() -> None:
    node = XtremetoolsWorkflowValidator()
    report, is_valid, info = node.validate_workflow(json.dumps({"nodes": []}))

    assert not is_valid
    assert "Missing required field" in report
    assert "Invalid" in info


def test_workflow_validator_detects_invalid_links(workflow_builder) -> None:
    payload = workflow_builder(
        last_node_id=2,
        last_link_id=1,
        nodes=[{"id": 1, "type": "TestNode"}],
        links=[[1, 1, 0, 999, 0, "STRING"]],
    )
    node = XtremetoolsWorkflowValidator()
    report, is_valid, _ = node.validate_workflow(json.dumps(payload))

    assert not is_valid
    assert "non-existent" in report
    assert "999" in report


def test_workflow_validator_detects_duplicate_node_ids(workflow_builder) -> None:
    payload = workflow_builder(
        last_node_id=1,
        nodes=[
            {"id": 1, "type": "TestNode"},
            {"id": 1, "type": "AnotherNode"},
        ],
    )
    node = XtremetoolsWorkflowValidator()
    report, is_valid, _ = node.validate_workflow(json.dumps(payload))

    assert not is_valid
    assert "Duplicate node ID" in report


def test_workflow_validator_handles_empty_workflow() -> None:
    node = XtremetoolsWorkflowValidator()
    report, is_valid, _ = node.validate_workflow("{}")

    assert not is_valid
    assert "Empty workflow" in report


def test_workflow_validator_link_symmetry(workflow_builder) -> None:
    payload = workflow_builder(
        last_node_id=2,
        last_link_id=1,
        nodes=[
            {
                "id": 1,
                "type": "XtremetoolsTestNode",
                "outputs": [{"name": "out", "type": "STRING", "links": []}],
            },
            {
                "id": 2,
                "type": "XtremetoolsTestNode",
                "inputs": [{"name": "in", "type": "STRING", "link": None}],
            },
        ],
        links=[[1, 1, 0, 2, 0, "STRING"]],
    )
    node = XtremetoolsWorkflowValidator()
    report, is_valid, info = node.validate_workflow(json.dumps(payload))

    assert not is_valid
    assert "not listed in source" in report
    assert "not listed in target" in report or "not listed in target" in info


def test_workflow_validator_auto_fix_last_ids(workflow_builder) -> None:
    payload = workflow_builder(
        last_node_id=1,
        last_link_id=0,
        nodes=[
            {"id": 1, "type": "XtremetoolsTestNode"},
            {"id": 2, "type": "XtremetoolsTestNode"},
        ],
        links=[[5, 1, 0, 2, 0, "STRING"]],
    )
    node = XtremetoolsWorkflowValidator()
    report, is_valid, info = node.validate_workflow(json.dumps(payload))

    assert "Applied auto-fix" in report or "Applied auto-fix" in info
    assert "last_node_id (1)" in report or "last_link_id (0)" in report


def test_workflow_validator_unknown_node_type_warning(workflow_builder) -> None:
    payload = workflow_builder(
        last_node_id=1,
        nodes=[{"id": 1, "type": "NonExistentNodeType", "pos": [0, 0]}],
    )
    node = XtremetoolsWorkflowValidator()
    report, is_valid, info = node.validate_workflow(json.dumps(payload))

    assert is_valid
    assert "Unknown node type" in report or "Unknown node type" in info


# ---- Workflow exporter tests ----


def test_workflow_exporter_formats_json(workflow_builder) -> None:
    workflow = workflow_builder(nodes=[], links=[])
    node = XtremetoolsWorkflowExporter()
    formatted, info = node.export_workflow(json.dumps(workflow), indent=2, add_metadata=False)

    parsed = json.loads(formatted)
    assert "nodes" in parsed
    assert "links" in parsed
    assert "Format" in info
    assert "Indented" in info


def test_workflow_exporter_adds_metadata(workflow_builder) -> None:
    workflow = workflow_builder(nodes=[], links=[])
    node = XtremetoolsWorkflowExporter()
    formatted, info = node.export_workflow(
        json.dumps(workflow),
        indent=2,
        add_metadata=True,
        add_metadata_note=True,
    )

    parsed = json.loads(formatted)
    assert "extra" in parsed
    assert "generated_by" in parsed["extra"]
    assert any(n.get("type") == "Note" for n in parsed.get("nodes", []))
    assert "Metadata Added: Yes" in info


def test_workflow_exporter_compact_format(workflow_builder) -> None:
    workflow = workflow_builder(nodes=[], links=[])
    node = XtremetoolsWorkflowExporter()
    formatted, info = node.export_workflow(
        json.dumps(workflow),
        indent=2,
        add_metadata=False,
        compact=True,
    )

    assert formatted.strip().count("\n") == 0
    assert "Compact" in info


# ---- Workflow generator tests ----


def test_workflow_generator_error_handling(monkeypatch) -> None:
    def fake_urlopen(request, timeout=None):  # noqa: ANN001
        raise RuntimeError("Network error")

    monkeypatch.setattr(
        "comfyui_xtremetools.base.lm_studio.urllib.request.urlopen",
        fake_urlopen,
    )

    server_settings, _ = XtremetoolsLMStudioServerSettings().build_server_settings(
        "http://localhost:1234",
        timeout_seconds=30,
    )
    model_settings, _ = XtremetoolsLMStudioModelSettings().build_model_settings("test-model")

    node = XtremetoolsWorkflowGenerator()
    workflow_json, info = node.generate_workflow(
        "Test request",
        server_settings=server_settings,
        model_settings=model_settings,
        temperature=0.3,
        max_tokens=1024,
    )

    assert workflow_json == "{}"
    assert "Error" in info


class _DummyGenResponse:
    def __init__(self, content: str):
        self._payload = {
            "model": "phi-local",
            "choices": [
                {"message": {"content": content}, "finish_reason": "stop"}
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }

    def __enter__(self):  # noqa: D401
        return self

    def __exit__(self, exc_type, exc, tb):  # noqa: ANN001
        return None

    def read(self) -> bytes:  # noqa: D401
        return json.dumps(self._payload).encode("utf-8")


def _invoke_generator(monkeypatch, content: str):  # noqa: ANN001
    def fake_urlopen(request, timeout=None):  # noqa: ANN001
        return _DummyGenResponse(content)

    monkeypatch.setattr(
        "comfyui_xtremetools.base.lm_studio.urllib.request.urlopen",
        fake_urlopen,
    )

    server_settings, _ = XtremetoolsLMStudioServerSettings().build_server_settings(
        "http://localhost:1234",
        timeout_seconds=30,
    )
    model_settings, _ = XtremetoolsLMStudioModelSettings().build_model_settings("phi-local")

    node = XtremetoolsWorkflowGenerator()
    workflow_json, info = node.generate_workflow(
        "Test request",
        server_settings=server_settings,
        model_settings=model_settings,
        temperature=0.1,
        max_tokens=512,
    )
    return workflow_json, info


def test_workflow_generator_raw_json_extraction(monkeypatch) -> None:
    raw = '{"nodes": [], "links": [], "last_node_id": 0, "last_link_id": 0}'
    workflow_json, info = _invoke_generator(monkeypatch, raw)

    assert workflow_json.strip().startswith("{")
    assert "Extraction: raw" in info
    assert "Strict JSON enforcement" in info


def test_workflow_generator_fenced_json_extraction(monkeypatch) -> None:
    fenced = (
        "Here is the workflow:\n```json\n{\n  \"nodes\": [],\n  \"links\": [],\n"
        "  \"last_node_id\": 0,\n  \"last_link_id\": 0\n}\n```"
    )
    workflow_json, info = _invoke_generator(monkeypatch, fenced)

    assert workflow_json.strip().startswith("{")
    assert "Extraction: fence" in info


def test_workflow_generator_brace_extraction(monkeypatch) -> None:
    mixed = (
        "Prologue... {\n  \"nodes\": [], \n  \"links\": [], \n"
        "  \"last_node_id\": 0, \n  \"last_link_id\": 0\n} Epilogue."
    )
    workflow_json, info = _invoke_generator(monkeypatch, mixed)

    assert workflow_json.strip().startswith("{")
    assert "Extraction: braces" in info


def test_workflow_generator_fallback_extraction(monkeypatch) -> None:
    no_json = "I cannot comply with the request right now."
    workflow_json, info = _invoke_generator(monkeypatch, no_json)

    parsed = json.loads(workflow_json)
    assert parsed.get("nodes") == []
    assert parsed.get("links") == []
    assert "Extraction: fallback" in info
