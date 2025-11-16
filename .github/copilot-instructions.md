# ComfyUI-Xtremetools – AI Coding Guide

## Mission & Scope
- Build custom ComfyUI nodes inside `ComfyUI-Xtremetools/src/comfyui_xtremetools`, then mirror this folder into `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-Xtremetools` (see `Docs/MIRRORING.md`).
- Treat this repo as the single source of truth; live ComfyUI installs should either symlink to it or receive automated copies.

## Project Layout
- `ComfyUI-Xtremetools/src/comfyui_xtremetools/` – Python package exported to ComfyUI; `__init__.py` re-exports from the ASCII-safe loader in `alias.py`.
- `base/` – shared helpers like `info.py` (InfoFormatter), `node_base.py` (XtremetoolsBaseNode), and `lm_studio.py` (HTTP utilities + `LMStudioAPIError`). Always extend these instead of rolling custom scaffolds.
- `nodes/` – drop each node module here; they are auto-imported via `alias._iter_node_modules()` so file names matter (`example_prompt_tool.py`, `test_node.py`, `lm_studio_text.py`, etc.).
- `web/` – reserved for future frontend extensions; remember to expose `WEB_DIRECTORY` when populated.
- `Docs/` – contains mirroring instructions, best practices, LM Studio integration notes (`LM_STUDIO.md`), and competitive research (`XDEV_NOTES.md`).
- `tests/` – pytest suites (see `tests/test_nodes.py`) that assert tuple output, registry wiring, and LM Studio HTTP mocks.

## Node Authoring Conventions
- Every node class must declare `CATEGORY`, `FUNCTION`, `RETURN_TYPES`, `RETURN_NAMES`, and implement `INPUT_TYPES`. Use `XtremetoolsBaseNode.ensure_tuple()` for outputs and `build_info()` for consistent info strings (see `nodes/example_prompt_tool.py`).
- Keep user-facing strings concise and emoji-friendly (InfoFormatter prepends `emoji + title`). Use info blocks for telemetry rather than print statements.
- For HTTP-backed nodes (e.g., LM Studio), subclass `LMStudioBaseNode` to reuse `build_messages`, `invoke_chat_completion`, latency tracking, and standardized error surfacing.
- Register nodes by populating local `NODE_CLASS_MAPPINGS` / `NODE_DISPLAY_NAME_MAPPINGS` inside each module; the alias loader merges them automatically.

## Development Workflow
- Use the repo venv: `C:/nodedev/.venv/Scripts/python.exe`. Activate before running scripts or tests.
- Install dev deps via `python -m pip install -e .[dev]` (see `pyproject.toml`).
- Run tests with `python -m pytest`; GitHub Actions (`.github/workflows/ci.yml`) runs the same command on pushes/PRs.
- Quick health check: `python tests/check_env.py`.
- After adding nodes, recreate the ComfyUI symlink or re-run the `mklink /D` command documented in `Docs/MIRRORING.md`; ComfyUI must be restarted because it caches modules.

## Integration & External References
- Follow official node guidelines summarized in `Docs/BEST_PRACTICES.md` (tensor shapes, widget config, PromptServer messaging).
- Use `Docs/LM_STUDIO.md` when modifying LM Studio nodes—covers server requirements, typical error causes (HTTP 400 for missing models), and troubleshooting tips.
- Research insights from `Docs/XDEV_NOTES.md` outline how mature packs structure ControlNet helpers, streaming nodes, and test coverage—mirror those expectations when expanding this repo.
- When planning APIs or advanced behaviors, document assumptions in `Docs/` first so future agents see rationale before editing code.

## When Adding Features
- Create or update doc stubs in `Docs/` alongside code changes; keep mirroring/testing instructions current in `README.md`.
- Prefer extending `base/node_base.py` or `base/lm_studio.py` rather than introducing new inheritance trees. If new base behavior is required (e.g., batching, streaming), add it there so every node benefits.
- Update `README.md` with any new workflows (extra build steps, dependencies) and ensure instructions reference actual commands tested in this repo.
- Always add/extend tests in `tests/test_nodes.py` (or new pytest modules) to cover tuple outputs, registry entries, and network mocks before pushing.
