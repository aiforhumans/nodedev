"""Integration smoke tests for generator → validator → exporter flow."""
from __future__ import annotations

import json

from comfyui_xtremetools import node_discovery
from comfyui_xtremetools.base.lm_studio import LMStudioModelSettings, LMStudioServerSettings
from comfyui_xtremetools.nodes.workflow_generator import (
    XtremetoolsWorkflowExporter,
    XtremetoolsWorkflowGenerator,
    XtremetoolsWorkflowValidator,
)


def _sample_object_info() -> dict:
    return {
        "categories": {
            "core": [
                {
                    "name": "XtremetoolsLMStudioText",
                    "inputs": [
                        {"name": "user_prompt", "type": "STRING"},
                        {"name": "system_prompt", "type": "STRING"},
                    ],
                    "outputs": [{"name": "generated_text", "type": "STRING"}],
                },
                {
                    "name": "ShowText|pysssss",
                    "inputs": [{"name": "text", "type": "STRING"}],
                    "outputs": [],
                },
            ]
        }
    }


def test_generate_validate_export_smoke(monkeypatch, fake_lm_studio_server):
    monkeypatch.setattr(node_discovery, "fetch_object_info", lambda: _sample_object_info())
    node_discovery.refresh_type_registry(force=True)

    fake_lm_studio_server.queue(
        {
            "id": "cmpl-test",
            "model": "ggml-model-q4_k.gguf",
            "choices": [
                {
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": json.dumps(
                            {
                                "nodes": [],
                                "links": [],
                                "groups": [],
                                "last_node_id": 0,
                                "last_link_id": 0,
                            }
                        ),
                    },
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20},
        }
    )

    generator = XtremetoolsWorkflowGenerator()
    validator = XtremetoolsWorkflowValidator()
    exporter = XtremetoolsWorkflowExporter()

    server = LMStudioServerSettings(server_url="http://localhost:1234", timeout=5)
    model = LMStudioModelSettings(model="ggml-model-q4_k.gguf")

    workflow_json, _ = generator.generate_workflow(
        workflow_request="Generate minimal workflow",
        server_settings=server,
        model_settings=model,
        temperature=0.0,
        max_tokens=512,
        retry_attempts=1,
        use_json_response_format=True,
        debug=False,
        auto_layout=False,
        synthesize_links=False,
    )

    report, is_valid, _ = validator.validate_workflow(workflow_json)
    assert is_valid, report

    exported, info = exporter.export_workflow(workflow_json)
    assert exported.strip().startswith("{")
    assert "Status: OK" in info
