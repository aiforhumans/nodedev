"""Tests for workflow post-processing helpers."""
from __future__ import annotations

import json

from comfyui_xtremetools.base.workflow_postprocessor import post_process_workflow


def test_workflow_postprocessor_synthesize_links(workflow_builder) -> None:
    workflow = workflow_builder(
        last_node_id=2,
        nodes=[
            {
                "id": 1,
                "type": "XtremetoolsLMStudioServerSettings",
                "pos": [100, 100],
                "outputs": [
                    {"name": "out", "type": "LM_STUDIO_SERVER", "links": []}
                ],
            },
            {
                "id": 2,
                "type": "XtremetoolsLMStudioText",
                "pos": [300, 100],
                "inputs": [
                    {"name": "server_settings", "type": "LM_STUDIO_SERVER", "link": None}
                ],
                "outputs": [],
            },
        ],
    )

    result = post_process_workflow(json.dumps(workflow), apply_layout=False, synthesize_links=True)
    parsed = json.loads(result)

    assert len(parsed["links"]) > 0
    assert parsed["nodes"][1]["inputs"][0]["link"] is not None


def test_workflow_postprocessor_apply_layout(workflow_builder) -> None:
    workflow = workflow_builder(
        last_node_id=2,
        nodes=[
            {"id": 1, "type": "XtremetoolsLMStudioServerSettings", "pos": [0, 0], "outputs": []},
            {"id": 2, "type": "ShowText|pysssss", "pos": [0, 0], "inputs": []},
        ],
    )

    result = post_process_workflow(json.dumps(workflow), apply_layout=True, synthesize_links=False)
    parsed = json.loads(result)

    assert parsed["nodes"][0]["pos"] != [0, 0] or parsed["nodes"][1]["pos"] != [0, 0]


def test_workflow_postprocessor_both(workflow_builder) -> None:
    workflow = workflow_builder(
        last_node_id=3,
        nodes=[
            {
                "id": 1,
                "type": "XtremetoolsLMStudioServerSettings",
                "pos": [0, 0],
                "outputs": [
                    {"name": "out", "type": "LM_STUDIO_SERVER", "links": []}
                ],
            },
            {
                "id": 2,
                "type": "XtremetoolsLMStudioText",
                "pos": [0, 0],
                "inputs": [
                    {"name": "server_settings", "type": "LM_STUDIO_SERVER", "link": None}
                ],
                "outputs": [
                    {"name": "generated_text", "type": "STRING", "links": []}
                ],
            },
            {
                "id": 3,
                "type": "ShowText|pysssss",
                "pos": [0, 0],
                "inputs": [
                    {"name": "text", "type": "STRING", "link": None}
                ],
            },
        ],
    )

    result = post_process_workflow(json.dumps(workflow), apply_layout=True, synthesize_links=True)
    parsed = json.loads(result)

    assert len(parsed["links"]) >= 2
    assert all(node["pos"] != [0, 0] for node in parsed["nodes"])
