"""Smoke tests for node discovery and registry handling."""
from __future__ import annotations

from comfyui_xtremetools import node_discovery


def test_custom_nodes_folder_is_ascii():
    path = node_discovery.resolve_custom_nodes_folder()
    assert path.name == "Xtremetools"
    # path may not exist when repo is a partial checkout, but when it does it must be ASCII only
    assert all(ord(ch) < 128 for ch in path.name)


def test_refresh_types_command(monkeypatch):
    sample_payload = {
        "categories": {
            "core": [
                {
                    "name": "SampleNode",
                    "inputs": [{"name": "prompt", "type": "STRING"}],
                    "outputs": [{"name": "text", "type": "STRING"}],
                }
            ]
        }
    }

    monkeypatch.setattr(node_discovery, "fetch_object_info", lambda: sample_payload)
    node_discovery.refresh_type_registry(force=True)
    summary = node_discovery.refresh_types_command()
    assert "Type registry refreshed" in summary
