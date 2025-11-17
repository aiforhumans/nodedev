"""Post-processing for generated ComfyUI workflows: DAG layout, link synthesis, and templates."""
from __future__ import annotations

import json
from typing import Any


class WorkflowDAGLayout:
    """Applies topological layout to workflow nodes based on connection patterns."""

    # Known node output types and typical consumers
    NODE_PATTERNS = {
        "XtremetoolsLMStudioServerSettings": {"outputs": ["LM_STUDIO_SERVER"], "consumers": ["XtremetoolsLMStudioText"]},
        "XtremetoolsLMStudioModelSettings": {"outputs": ["LM_STUDIO_MODEL"], "consumers": ["XtremetoolsLMStudioText"]},
        "XtremetoolsLMStudioStylePreset": {"outputs": ["STRING"], "consumers": ["XtremetoolsLMStudioDualPrompt", "XtremetoolsLMStudioPromptJoiner"]},
        "XtremetoolsLMStudioFewShotExamples": {"outputs": ["STRING"], "consumers": ["XtremetoolsLMStudioPromptJoiner"]},
        "XtremetoolsLMStudioStructuredOutput": {"outputs": ["STRING"], "consumers": ["XtremetoolsLMStudioText"]},
        "XtremetoolsLMStudioNegativePrompt": {"outputs": ["STRING"], "consumers": ["XtremetoolsLMStudioPromptJoiner"]},
        "XtremetoolsLMStudioPromptWeighter": {"outputs": ["STRING"], "consumers": ["XtremetoolsLMStudioPromptJoiner"]},
        "XtremetoolsLMStudioDualPrompt": {"outputs": ["STRING"], "consumers": ["XtremetoolsLMStudioText"]},
        "XtremetoolsLMStudioQualityControl": {"outputs": ["FLOAT", "INT"], "consumers": ["XtremetoolsLMStudioText"]},
        "XtremetoolsLMStudioPromptJoiner": {"outputs": ["STRING"], "consumers": ["XtremetoolsLMStudioText", "ShowText|pysssss"]},
        "XtremetoolsLMStudioText": {"outputs": ["STRING"], "consumers": ["ShowText|pysssss"]},
    }

    @staticmethod
    def build_link_map(workflow: dict[str, Any]) -> dict[tuple[int, int], int]:
        """Build a map of (source_node_id, output_index) -> link_id."""
        link_map: dict[tuple[int, int], int] = {}
        for link in workflow.get("links", []):
            if isinstance(link, list) and len(link) >= 3:
                link_id, source_id, source_out_idx = link[0], link[1], link[2]
                link_map[(source_id, source_out_idx)] = link_id
        return link_map

    @staticmethod
    def build_node_map(workflow: dict[str, Any]) -> dict[int, dict[str, Any]]:
        """Build a map of node_id -> node."""
        return {node["id"]: node for node in workflow.get("nodes", []) if isinstance(node, dict)}

    @staticmethod
    def topological_order(nodes_map: dict[int, dict], links: list) -> list[int]:
        """Return node IDs in rough topological order (configs first, outputs last)."""
        config_nodes = []
        processor_nodes = []
        output_nodes = []

        for node_id, node in nodes_map.items():
            ntype = node.get("type", "")
            if "Settings" in ntype or ntype in ["XtremetoolsLMStudioServerSettings", "XtremetoolsLMStudioModelSettings"]:
                config_nodes.append(node_id)
            elif ntype in ["ShowText|pysssss", "Note|pysssss"]:
                output_nodes.append(node_id)
            else:
                processor_nodes.append(node_id)

        return sorted(config_nodes) + sorted(processor_nodes) + sorted(output_nodes)

    @staticmethod
    def assign_positions(nodes_map: dict[int, dict], order: list[int]) -> None:
        """Assign x, y positions to nodes based on topological order."""
        config_cols = {nid: idx for idx, nid in enumerate([nid for nid in order if "Settings" in nodes_map[nid].get("type", "")])}
        processor_cols = {
            nid: idx
            for idx, nid in enumerate([nid for nid in order if "Settings" not in nodes_map[nid].get("type", "") and nodes_map[nid].get("type", "") not in ["ShowText|pysssss", "Note|pysssss"]])
        }
        output_cols = {
            nid: idx
            for idx, nid in enumerate([nid for nid in order if nodes_map[nid].get("type", "") in ["ShowText|pysssss", "Note|pysssss"]])
        }

        for node_id, node in nodes_map.items():
            if node_id in config_cols:
                x = 100 + config_cols[node_id] * 250
                y = 100
            elif node_id in processor_cols:
                x = 100 + processor_cols[node_id] * 250
                y = 250
            else:
                x = 100 + output_cols.get(node_id, 0) * 250
                y = 400

            node["pos"] = [x, y]

    @staticmethod
    def synthesize_links(workflow: dict[str, Any]) -> None:
        """Auto-create links between nodes based on type patterns and available inputs/outputs."""
        nodes_map = WorkflowDAGLayout.build_node_map(workflow)
        next_link_id = max((link[0] for link in workflow.get("links", []) if isinstance(link, list)), default=0) + 1
        new_links = list(workflow.get("links", []))

        for node_id, node in nodes_map.items():
            node_type = node.get("type", "")
            inputs = node.get("inputs", [])

            # Match inputs to outputs from other nodes
            for input_idx, input_spec in enumerate(inputs):
                if input_spec.get("link") is not None:
                    continue  # already has a link

                input_type = input_spec.get("type")
                input_name = input_spec.get("name", "")

                # Find a source node that can provide this
                source_found = False
                for other_id, other_node in nodes_map.items():
                    if other_id == node_id:
                        continue

                    other_type = other_node.get("type", "")
                    outputs = other_node.get("outputs", [])

                    for output_idx, output_spec in enumerate(outputs):
                        output_type = output_spec.get("type")

                        # Match based on type
                        if (input_type == output_type or
                            input_type == "STRING" or
                            (input_type is None and output_type == "STRING")):
                            # Create link
                            link_id = next_link_id
                            new_links.append([link_id, other_id, output_idx, node_id, input_idx, output_type or "STRING"])
                            input_spec["link"] = link_id
                            output_spec.setdefault("links", []).append(link_id)
                            next_link_id += 1
                            source_found = True
                            break

                    if source_found:
                        break

        workflow["links"] = new_links
        workflow["last_link_id"] = next_link_id - 1

    @staticmethod
    def apply_layout(workflow: dict[str, Any]) -> None:
        """Apply DAG layout and link synthesis to workflow."""
        nodes_map = WorkflowDAGLayout.build_node_map(workflow)
        links = workflow.get("links", [])
        order = WorkflowDAGLayout.topological_order(nodes_map, links)
        WorkflowDAGLayout.assign_positions(nodes_map, order)
        WorkflowDAGLayout.synthesize_links(workflow)
        workflow["last_node_id"] = max((node["id"] for node in nodes_map.values()), default=0)


def post_process_workflow(workflow_json: str, apply_layout: bool = True, synthesize_links: bool = True) -> str:
    """Post-process generated workflow JSON.

    Args:
        workflow_json: Raw workflow JSON string
        apply_layout: Whether to apply DAG layout (positioning)
        synthesize_links: Whether to auto-create missing links

    Returns:
        Processed workflow JSON string
    """
    try:
        workflow = json.loads(workflow_json)
    except json.JSONDecodeError:
        return workflow_json

    if synthesize_links:
        WorkflowDAGLayout.synthesize_links(workflow)

    if apply_layout:
        nodes_map = WorkflowDAGLayout.build_node_map(workflow)
        if nodes_map:
            order = WorkflowDAGLayout.topological_order(nodes_map, workflow.get("links", []))
            WorkflowDAGLayout.assign_positions(nodes_map, order)

    workflow.setdefault("last_node_id", max((n.get("id", 0) for n in workflow.get("nodes", [])), default=0))
    workflow.setdefault("last_link_id", max((link[0] for link in workflow.get("links", []) if isinstance(link, list)), default=0))

    return json.dumps(workflow, ensure_ascii=False)
