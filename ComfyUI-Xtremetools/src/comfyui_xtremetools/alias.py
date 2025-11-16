"""ASCII-friendly alias loader for ComfyUI-Xtremetools nodes.

This module discovers node modules under :mod:`comfyui_xtremetools.nodes`
and merges their exported `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS`
so ComfyUI can import this package without depending on any non-ASCII paths.
"""
from __future__ import annotations

import importlib
from collections.abc import Iterable
from pathlib import Path
from types import ModuleType

PACKAGE_ROOT = Path(__file__).resolve().parent
NODES_ROOT = PACKAGE_ROOT / "nodes"

NODE_CLASS_MAPPINGS: dict[str, type] = {}
NODE_DISPLAY_NAME_MAPPINGS: dict[str, str] = {}


def _iter_node_modules() -> Iterable[str]:
    """Yield dotted module paths for node modules under ``nodes``."""
    if not NODES_ROOT.exists():  # Nothing to load yet
        return []

    modules: list[str] = []
    for path in NODES_ROOT.iterdir():
        if path.is_file() and path.suffix == ".py" and path.name != "__init__.py":
            modules.append(f"comfyui_xtremetools.nodes.{path.stem}")
        elif path.is_dir() and (path / "__init__.py").exists():
            modules.append(f"comfyui_xtremetools.nodes.{path.name}")
    return modules


def _collect(module: ModuleType) -> None:
    class_map = getattr(module, "NODE_CLASS_MAPPINGS", {})
    display_map = getattr(module, "NODE_DISPLAY_NAME_MAPPINGS", {})

    NODE_CLASS_MAPPINGS.update(class_map)
    NODE_DISPLAY_NAME_MAPPINGS.update(display_map)


def _bootstrap() -> None:
    for module_path in _iter_node_modules():
        module = importlib.import_module(module_path)
        _collect(module)


_bootstrap()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
