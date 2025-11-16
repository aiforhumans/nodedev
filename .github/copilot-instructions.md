# ComfyUI-Xtremetools – AI Coding Guide

## Mission & Scope
- Build custom ComfyUI nodes inside `ComfyUI-Xtremetools/src/comfyui_xtremetools`, then mirror this folder into `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-Xtremetools` (see `Docs/MIRRORING.md`).
- Treat this repo as the single source of truth; live ComfyUI installs should either symlink to it or receive automated copies.

## Project Layout
- `ComfyUI-Xtremetools/src/comfyui_xtremetools/` – Python package exported to ComfyUI; `__init__.py` re-exports from the ASCII-safe loader in `alias.py`.
- `base/` – shared helpers like `info.py` (InfoFormatter) and `node_base.py` (XtremetoolsBaseNode). Always extend these instead of rolling custom scaffolds.
- `nodes/` – drop each node module here; they are auto-imported via `alias._iter_node_modules()` so file names matter.
- `web/` – reserved for future frontend extensions; remember to expose `WEB_DIRECTORY` when populated.
- `Docs/` – contains mirroring instructions, best practices from official Comfy docs, and competitive research (`XDEV_NOTES.md`). Use them to align with ecosystem norms.
- `tests/` – currently houses environment checks; expand with pytest suites that mirror XDEV’s tuple/registration tests once nodes grow.

## Node Authoring Conventions
- Every node class must declare `CATEGORY`, `FUNCTION`, `RETURN_TYPES`, `RETURN_NAMES`, and implement `INPUT_TYPES`. Use `XtremetoolsBaseNode.ensure_tuple()` for outputs and `build_info()` for consistent info strings (see `nodes/example_prompt_tool.py`).
- Keep user-facing strings concise and emoji-friendly (InfoFormatter prepends `emoji + title`). Use info blocks for telemetry rather than print statements.
- Place shared behavior in base classes or helpers; look at `Docs/XDEV_NOTES.md` for patterns like API wrappers, JSON parsing, and control of ComfyUI messaging.
- Register nodes by populating local `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` inside each module; the alias loader merges them automatically.

## Development Workflow
- Use the repo venv: `C:/nodedev/.venv/Scripts/python.exe`. Activate before running scripts or tests.
- Quick health check: `C:/nodedev/.venv/Scripts/python.exe tests/check_env.py`.
- Future pytest command: `C:/nodedev/.venv/Scripts/python.exe -m pytest` (structure tests under `tests/`).
- After adding nodes, either recreate the ComfyUI symlink or re-run the `mklink /D` command documented in `Docs/MIRRORING.md`; ComfyUI must be restarted because it caches modules.

## Integration & External References
- Follow official node guidelines summarized in `Docs/BEST_PRACTICES.md` (tensor shapes, widget config, PromptServer messaging).
- Research insights from `Docs/XDEV_NOTES.md` outline how mature packs structure ControlNet helpers, streaming nodes, and test coverage—mirror those expectations when expanding this repo.
- When planning APIs or advanced behaviors, document assumptions in `Docs/` first so future agents see rationale before editing code.

## When Adding Features
- Create or update doc stubs in `Docs/` alongside code changes; keep mirroring/testing instructions current in `README.md`.
- Prefer extending `base/node_base.py` rather than introducing new inheritance trees. If new base behavior is required (e.g., HTTP clients), add it there so every node benefits.
- Update `README.md` with any new workflows (extra build steps, dependencies) and ensure instructions reference actual commands tested in this repo.
