"""Smoke tests for MCP node contracts."""
from __future__ import annotations

import pytest

from tests.mcp.harness import build_node_contract
from tests.snapshot_utils import assert_node_contract_snapshot

pytestmark = pytest.mark.mcp


def test_node_contracts_include_core_fields(alias_iterator, update_node_snapshots) -> None:
    for name, node_cls in alias_iterator:
        contract = build_node_contract(name, node_cls)
        assert contract["name"] == name
        assert contract["function"], f"{name} missing FUNCTION"
        assert isinstance(contract["inputs"], dict)
        assert isinstance(contract["return_types"], tuple)
        assert isinstance(contract["return_names"], tuple)
        assert len(contract["return_types"]) == len(contract["return_names"])
        assert contract["category"].startswith("🤖 Xtremetools")
        assert_node_contract_snapshot(name, contract, update_node_snapshots)