"""Snapshot helpers for node contract tests."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

SNAPSHOT_ROOT = Path(__file__).parent / "snapshots"
NODE_CONTRACT_DIR = SNAPSHOT_ROOT / "node_contracts"


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _snapshot_path(node_name: str) -> Path:
    safe_name = node_name.replace("/", "_")
    path = NODE_CONTRACT_DIR / f"{safe_name}.json"
    _ensure_dir(path.parent)
    return path


def _to_serializable(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _to_serializable(val) for key, val in value.items()}
    if isinstance(value, (list, tuple)):
        return [_to_serializable(item) for item in value]
    return value


def assert_node_contract_snapshot(node_name: str, data: dict[str, Any], update: bool) -> None:
    """Compare serialized contract data against stored snapshot."""

    serializable = _to_serializable(data)
    path = _snapshot_path(node_name)

    if update or not path.exists():
        contents = json.dumps(serializable, indent=2, sort_keys=True)
        path.write_text(contents + "\n", encoding="utf-8")
        return

    expected = json.loads(path.read_text(encoding="utf-8"))
    assert serializable == expected, f"Snapshot mismatch for {node_name}. Run pytest --update-node-snapshots to regenerate."
