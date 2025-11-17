"""Tests for alias-based node discovery."""
from __future__ import annotations

from comfyui_xtremetools.alias import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS


def test_alias_registry_contains_core_nodes(alias_iterator) -> None:
    registry = dict(alias_iterator)

    assert "XtremetoolsPromptJoiner" in registry
    assert "XtremetoolsTestNode" in registry
    assert "XtremetoolsLMStudioText" in registry
    assert "XtremetoolsLMStudioServerSettings" in registry
    assert "XtremetoolsLMStudioModelSettings" in registry
    assert "XtremetoolsLMStudioGenerationSettings" in registry
    assert "XtremetoolsLMStudioStylePreset" in registry
    assert "XtremetoolsLMStudioPromptWeighter" in registry
    assert "XtremetoolsLMStudioDualPrompt" in registry
    assert "XtremetoolsLMStudioQualityControl" in registry
    assert "XtremetoolsLMStudioNegativePrompt" in registry
    assert "XtremetoolsWorkflowRequest" in registry
    assert "XtremetoolsWorkflowGenerator" in registry
    assert "XtremetoolsWorkflowValidator" in registry
    assert "XtremetoolsWorkflowExporter" in registry


def test_display_name_mappings_are_present(alias_display_names) -> None:
    assert alias_display_names["XtremetoolsTestNode"] == "Test Node"
    assert "XtremetoolsLMStudioText" in alias_display_names
    assert alias_display_names["XtremetoolsWorkflowGenerator"] == "🔧 Workflow Generator (AI)"


def test_alias_module_exports_match_singleton_sources() -> None:
    assert NODE_CLASS_MAPPINGS is not None
    assert NODE_DISPLAY_NAME_MAPPINGS is not None
    assert len(NODE_CLASS_MAPPINGS) >= len(NODE_DISPLAY_NAME_MAPPINGS)
