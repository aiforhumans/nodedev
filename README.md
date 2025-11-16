# ComfyUI-Xtremetools

Custom nodes, utilities, and research notes for ComfyUI workflows. This repository is the source of truth that should be symlinked or copied into `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-Xtremetools` (see `Docs/MIRRORING.md`).

## Highlights
- **Shared foundations:** `base/` exposes InfoFormatter helpers, tuple-safe base nodes, and the `LMStudioBaseNode` HTTP client.
- **Example + diagnostic nodes:** `XtremetoolsPromptJoiner`, `XtremetoolsTestNode`, and `XtremetoolsLMStudioText` demonstrate prompt utilities and LLM integration.
- **Research-driven docs:** `Docs/BEST_PRACTICES.md`, `Docs/XDEV_NOTES.md`, and `Docs/LM_STUDIO.md` capture official guidance plus lessons learned from other node packs.
- **Editable installs + CI:** `pyproject.toml` enables `pip install -e .[dev]`, and `.github/workflows/ci.yml` runs `pytest` on every push/PR.

## Repository Layout
```
ComfyUI-Xtremetools/
├── src/comfyui_xtremetools/
│   ├── __init__.py          # re-exports alias loader
│   ├── alias.py             # aggregates NODE_CLASS_MAPPINGS
│   ├── base/
│   │   ├── info.py          # InfoFormatter
│   │   ├── node_base.py     # XtremetoolsBaseNode + Utility base
│   │   └── lm_studio.py     # LMStudioBaseNode + HTTP helpers
│   └── nodes/               # Custom nodes auto-discovered by alias
├── Docs/                    # mirroring, best practices, LM Studio notes
├── tests/                   # pytest suites (mocked LM Studio calls)
└── web/                     # future client assets (export WEB_DIRECTORY when used)
```

## Getting Started
1. **Clone & venv**
   ```powershell
   git clone <repo>
   cd nodedev
   python -m venv .venv
   .\.venv\Scripts\activate
   ```
2. **Install dev dependencies**
   ```powershell
   python -m pip install -U pip
   python -m pip install -e .[dev]
   ```
3. **Run tests**
   ```powershell
   python -m pytest
   ```
4. **Mirror into ComfyUI** (requires elevated shell)
   ```cmd
   mklink /D "C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\ComfyUI-Xtremetools" "C:\nodedev\ComfyUI-Xtremetools"
   ```
5. Restart ComfyUI to pick up the new/updated nodes.

## Contributing Nodes
- Place new modules under `src/comfyui_xtremetools/nodes/` and extend `XtremetoolsBaseNode`, `XtremetoolsUtilityNode`, or `LMStudioBaseNode`.
- Declare `CATEGORY`, `FUNCTION`, `RETURN_TYPES`, `RETURN_NAMES`, and implement `INPUT_TYPES`.
- Always expose `NODE_CLASS_MAPPINGS`/`NODE_DISPLAY_NAME_MAPPINGS`; the alias loader stitches them together.
- Use `build_info()` to emit emoji-friendly telemetry and `ensure_tuple()` to satisfy ComfyUI’s tuple contract.
- Add or update pytest coverage (`tests/test_nodes.py`) to cover tuple outputs, registry entries, and LM Studio HTTP mocks.
- Document noteworthy behavior under `Docs/` (especially LM Studio assumptions or new mirroring steps).

## LM Studio Integration
- `base/lm_studio.py` wraps LM Studio’s `/v1/chat/completions` endpoint with error handling, latency tracking, and structured info outputs.
- `nodes/lm_studio_text.py` provides a ready-to-use text generation node that accepts prompt/system/user text, temperature, max tokens, server URL, and optional model.
- See `Docs/LM_STUDIO.md` for setup requirements, HTTP 400 troubleshooting (usually “model not loaded”), and future extension ideas (batching, streaming, model discovery).

## Release Checklist
1. Ensure `pytest` passes locally and in CI.
2. Update READMEs/docs for any new nodes, dependencies, or workflows.
3. Tag the repository and publish release notes summarizing new nodes, breaking changes, and mirroring reminders.

## License
Distributed under the [MIT License](LICENSE). Contributions and issue reports are welcome.
