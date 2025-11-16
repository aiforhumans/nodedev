# ComfyUI-Xtremetools Workspace

Custom ComfyUI node pack under active development. This repo is the source of truth for the package mirrored into `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-Xtremetools`.

## Repository Layout
- `ComfyUI-Xtremetools/src/comfyui_xtremetools/` – Python package consumed by ComfyUI
  - `alias.py` automatically loads every module under `nodes/`
  - `base/` contains shared helpers (`InfoFormatter`, `XtremetoolsBaseNode`)
  - `nodes/` ships custom nodes such as `XtremetoolsPromptJoiner` and `XtremetoolsTestNode`
- `Docs/` – mirroring steps, best practices, and research notes pulled from official ComfyUI + XDEV references
- `tests/` – pytest suites that verify tuple outputs and registry wiring
- `web/` – placeholder for future client assets; export `WEB_DIRECTORY` once populated

## Getting Started
1. Clone the repository and ensure Python 3.10+ is available.
2. Create/activate the workspace venv (recommended path `C:/nodedev/.venv`).
3. Install dev dependencies:
   ```powershell
   C:/nodedev/.venv/Scripts/python.exe -m pip install -e .[dev]
   ```
4. Run tests:
   ```powershell
   C:/nodedev/.venv/Scripts/python.exe -m pytest
   ```
5. Mirror to ComfyUI using the documented symlink (`Docs/MIRRORING.md`) and restart ComfyUI to reload nodes.

## Development Workflow
- Implement new nodes inside `src/comfyui_xtremetools/nodes/` and derive from `XtremetoolsBaseNode` or `XtremetoolsUtilityNode`.
- Each module must provide `NODE_CLASS_MAPPINGS` and `NODE_DISPLAY_NAME_MAPPINGS`; the alias loader merges them for ComfyUI.
- Emit info strings via `build_info()` and always return tuples using `ensure_tuple()` to satisfy ComfyUI’s contract.
- Add/extend pytest coverage in `tests/` whenever nodes change; CI runs `python -m pytest` on pushes and pull requests.
- Document architectural or workflow decisions under `Docs/` so contributors have historical context.

## Releasing & Distribution
- ComfyUI users can consume the repo by copying/symlinking `ComfyUI-Xtremetools/` into `ComfyUI/custom_nodes`.
- `pyproject.toml` enables editable installs (`pip install -e .`) for linting/testing without the ComfyUI runtime.
- Tag releases in GitHub once the node set and docs for a version are stable; publish release notes that highlight new nodes, breaking changes, and mirroring instructions.

## License
Released under the [MIT License](LICENSE). Contributions are welcome via pull requests following the repository’s testing and documentation guidelines.
