# ComfyUI-Xtremetools

Workspace for custom ComfyUI nodes. Keep this directory mirrored with `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-Xtremetools` for live testing.

## Package layout
- `src/comfyui_xtremetools/` – Python package copied into `ComfyUI/custom_nodes`
	- `__init__.py` – re-exports ASCII-safe alias mappings
	- `alias.py` – discovers everything under `nodes/` and merges `NODE_CLASS_MAPPINGS`
	- `base/` – shared helpers (`InfoFormatter`, base node classes)
	- `nodes/` – custom node implementations (starts with `XtremetoolsPromptJoiner`)
- `web/` – reserved for future client extensions (export via `WEB_DIRECTORY` when needed)

## Bootstrap & testing
1. Create or reuse your Python venv (see repo root `.venv`).
2. From `ComfyUI-Xtremetools`, install dependencies as you add them (currently stdlib only).
3. Run lightweight checks: `C:/nodedev/.venv/Scripts/python.exe -m pytest` (tests folder TBD).
4. Mirror to ComfyUI once new nodes exist. Symlink example:
	 ```cmd
	 mklink /D "C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-Xtremetools" "C:\nodedev\ComfyUI-Xtremetools"
	 ```

## Next steps
1. Flesh out node categories under `nodes/` (prompt tools, vision helpers, etc.).
2. Expand the base classes with API helpers (requests, validation, caching).
3. Add pytest suite mirroring `tests/test_example_node.py` patterns from XDEV repo.
4. Document any external dependencies plus minimum ComfyUI version per node.
