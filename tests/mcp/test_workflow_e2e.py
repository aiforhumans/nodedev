"""End-to-end MCP harness workflows."""
from __future__ import annotations

import json

import pytest

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
from comfyui_xtremetools.base.workflow_postprocessor import post_process_workflow

from tests.mcp.harness import FakeMCPClient, MCPToolAdapter

pytestmark = pytest.mark.mcp


def _sample_workflow_json() -> str:
    payload = {
        "last_node_id": 1,
        "last_link_id": 0,
        "nodes": [
            {
                "id": 1,
                "type": "XtremetoolsTestNode",
                "pos": [100, 100],
                "outputs": [],
                "inputs": [],
                "properties": {"Node name for S&R": "XtremetoolsTestNode"},
            }
        ],
        "links": [],
        "groups": [],
    }
    return json.dumps(payload)


def _queue_workflow_response(fake_lm_studio_server, workflow_json: str) -> None:
    fake_lm_studio_server.queue(
        {
            "model": "phi-local",
            "choices": [
                {
                    "message": {"content": workflow_json},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
    )


def test_mcp_workflow_round_trip(fake_lm_studio_server) -> None:
    adapters = [
        MCPToolAdapter(XtremetoolsWorkflowRequest),
        MCPToolAdapter(XtremetoolsWorkflowGenerator),
        MCPToolAdapter(XtremetoolsWorkflowValidator),
        MCPToolAdapter(XtremetoolsWorkflowExporter),
        MCPToolAdapter(XtremetoolsLMStudioServerSettings),
        MCPToolAdapter(XtremetoolsLMStudioModelSettings),
    ]
    client = FakeMCPClient(adapters)

    server_settings = client.call_tool(
        "XtremetoolsLMStudioServerSettings",
        {"server_url": "http://127.0.0.1:9001", "timeout_seconds": 15},
    ).outputs[0]
    model_settings = client.call_tool(
        "XtremetoolsLMStudioModelSettings",
        {"model": "phi-local", "fallback_to_default": True},
    ).outputs[0]

    request_result = client.call_tool(
        "XtremetoolsWorkflowRequest",
        {
            "user_description": "Create a simple diagnostic workflow",
            "workflow_type": "prompt_engineering",
            "output_format": "text",
            "complexity": "simple",
            "required_nodes": "XtremetoolsTestNode",
        },
    )
    request_result.ensure_ascii()
    structured_request = request_result.outputs[0]

    _queue_workflow_response(fake_lm_studio_server, _sample_workflow_json())
    generator_result = client.call_tool(
        "XtremetoolsWorkflowGenerator",
        {
            "workflow_request": structured_request,
            "server_settings": server_settings,
            "model_settings": model_settings,
            "temperature": 0.1,
            "max_tokens": 512,
            "retry_attempts": 1,
            "use_json_response_format": True,
            "debug": False,
            "auto_layout": False,
            "synthesize_links": False,
        },
    )
    generator_result.ensure_ascii()
    workflow_json = generator_result.outputs[0]

    validator_result = client.call_tool(
        "XtremetoolsWorkflowValidator",
        {"workflow_json": workflow_json},
    )
    report, is_valid, _ = validator_result.outputs
    validator_result.ensure_ascii()
    assert is_valid, report

    exporter_result = client.call_tool(
        "XtremetoolsWorkflowExporter",
        {
            "workflow_json": workflow_json,
            "indent": 2,
            "add_metadata": True,
            "add_metadata_note": True,
            "compact": False,
        },
    )
    exporter_result.ensure_ascii()
    formatted = exporter_result.outputs[0]

    processed = post_process_workflow(formatted, apply_layout=True, synthesize_links=True)
    parsed = json.loads(processed)

    assert parsed["nodes"], "Workflow should include nodes after post-processing"
    assert parsed["links"] == [] or isinstance(parsed["links"], list)
    assert parsed["last_node_id"] >= 1