"""Fetches live ComfyUI object info and builds a type registry."""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .config import get_environment_config
from .logger import get_logger
from .type_registry import TypeRegistry, create_registry

# Copilot: keep docstrings comprehensive for discovery utilities.

logger = get_logger("xtremetools.node_discovery")


@dataclass(slots=True)
class DiscoveryState:
    registry: TypeRegistry
    last_fetch_ts: float | None = None
    last_error: str | None = None


_STATE = DiscoveryState(registry=create_registry())


def resolve_custom_nodes_folder(repo_root: Path | None = None) -> Path:
    """Return the ASCII-only custom nodes folder."""

    root = repo_root or Path(__file__).resolve().parents[3]
    return root / "Xtremetools"


def fetch_object_info(server_url: str | None = None) -> dict[str, Any]:
    """Request /object_info from the configured ComfyUI server."""

    config = get_environment_config()
    base_url = (server_url or config.comfyui_server_url).rstrip("/")
    endpoint = f"{base_url}/object_info"
    logger.info("Fetching ComfyUI object info", extra={"endpoint": endpoint})
    request = urllib.request.Request(endpoint, method="GET")
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.load(response)
    except urllib.error.URLError as exc:  # pragma: no cover - network failure
        _STATE.last_error = str(exc)
        logger.warning("Failed to fetch object info: %s", exc)
        return {}
    _STATE.last_error = None
    return payload or {}


def refresh_type_registry(force: bool = False) -> TypeRegistry:
    """Fetch latest object info and rebuild the registry."""

    if _STATE.last_fetch_ts and not force and (time.time() - _STATE.last_fetch_ts) < 60:
        return _STATE.registry

    payload = fetch_object_info()
    if payload:
        _STATE.registry.build_from_object_info(payload)
        _STATE.last_fetch_ts = time.time()
        logger.info(
            "Refreshed type registry",
            extra={"nodes": len(_STATE.registry.nodes), "compat_rules": len(_STATE.registry.compatibility_overrides)},
        )
    return _STATE.registry


def get_type_registry() -> TypeRegistry:
    """Return the cached registry, refreshing on first access."""

    if not _STATE.registry.nodes:
        refresh_type_registry(force=True)
    return _STATE.registry


def get_last_fetch_timestamp() -> float | None:
    return _STATE.last_fetch_ts


def refresh_types_command() -> str:
    """CLI-friendly helper to refresh the registry on demand."""

    registry = refresh_type_registry(force=True)
    ts = _STATE.last_fetch_ts or 0.0
    human_ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts)) if ts else "unknown"
    summary = f"Type registry refreshed at {human_ts} with {len(registry.nodes)} nodes"
    logger.info(summary)
    return summary


__all__ = [
    "DiscoveryState",
    "resolve_custom_nodes_folder",
    "fetch_object_info",
    "refresh_type_registry",
    "get_type_registry",
    "get_last_fetch_timestamp",
    "refresh_types_command",
]

try:  # pragma: no cover - best-effort during import
    refresh_type_registry(force=True)
except Exception as exc:  # noqa: BLE001 - log and proceed
    logger.warning("Initial type registry refresh failed: %s", exc)
