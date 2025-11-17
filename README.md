# 🤖Xtremetools

Custom nodes, utilities, and research notes for ComfyUI workflows. This repository is the source of truth that should be symlinked or copied into `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\🤖Xtremetools` (see `Docs/MIRRORING.md`).

## Highlights
- **Shared foundations:** `base/` exposes InfoFormatter helpers, tuple-safe base nodes, and the `LMStudioBaseNode` HTTP client.
- **Example + diagnostic nodes:** `XtremetoolsPromptJoiner`, `XtremetoolsTestNode`, and `XtremetoolsLMStudioText` demonstrate prompt utilities and LLM integration.
- **Composable LM Studio settings:** dedicated nodes emit server/model/generation configs so bigger graphs stay modular.
- **Research-driven docs:** `Docs/BEST_PRACTICES.md`, `Docs/XDEV_NOTES.md`, and `Docs/LM_STUDIO.md` capture official guidance plus lessons learned from other node packs.
- **Editable installs + CI:** `pyproject.toml` enables `pip install -e .[dev]`, and `.github/workflows/ci.yml` runs `pytest` on every push/PR.

## Repository Layout
```
🤖Xtremetools/
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
   mklink /D "C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\🤖Xtremetools" "C:\nodedev\🤖Xtremetools"
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
- `base/lm_studio.py` wraps LM Studio's `/v1/chat/completions` endpoint with error handling, latency tracking, and structured info outputs. It now exposes dataclasses (`LMStudioServerSettings`, `LMStudioModelSettings`, `LMStudioGenerationSettings`) that travel through Comfy graphs.
- `nodes/lm_studio_text.py` consumes those settings objects (or plain inputs) so prompts, server profiles, and sampling knobs can live in separate reusable subgraphs.
- `nodes/lm_studio_settings.py` ships three helpers:
  - `XtremetoolsLMStudioServerSettings` → outputs connection URL + timeout.
  - `XtremetoolsLMStudioModelSettings` → tracks preferred model/fallback rules.
  - `XtremetoolsLMStudioGenerationSettings` → bundles temperature, max tokens, and response format.
- `nodes/lm_studio_prompt_helpers.py` provides **research-backed prompt engineering** with 7 nodes implementing best practices from Anthropic & OpenAI:
  - `XtremetoolsLMStudioStylePreset` → role prompting with 8 persona presets (includes `step_by_step` for chain-of-thought).
  - `XtremetoolsLMStudioPromptWeighter` → parse SDXL-style `(word:weight)` syntax for emphasis control.
  - `XtremetoolsLMStudioDualPrompt` → system/user message separation (instruction + context).
  - `XtremetoolsLMStudioQualityControl` → 5 creativity/precision presets with fine-tuning adjustments.
  - `XtremetoolsLMStudioNegativePrompt` → constraint-based topic/style avoidance.
  - `XtremetoolsLMStudioFewShotExamples` → XML-tagged example pairs (Anthropic best practice for format adherence).
  - `XtremetoolsLMStudioStructuredOutput` → explicit format instructions (XML/JSON/Markdown) with optional chain-of-thought reasoning.
- See `Docs/LM_STUDIO.md` for workflow patterns (few-shot learning, structured output, quality control), setup requirements, and HTTP 400 troubleshooting.

## Release Checklist
1. Ensure `pytest` passes locally and in CI.
2. Update READMEs/docs for any new nodes, dependencies, or workflows.
3. Tag the repository and publish release notes summarizing new nodes, breaking changes, and mirroring reminders.

## Meta-Workflow Generation (Advanced)

The meta-workflow nodes automate workflow creation from natural language requests:

- **XtremetoolsWorkflowRequest**: Structures user descriptions into formal generation requests with complexity, node requirements, and output format specifications.
- **XtremetoolsWorkflowGenerator (AI)**: Invokes LM Studio to synthesize ComfyUI workflow JSON, with retry logic, deterministic JSON-only output enforcement, and automatic DAG layout + link synthesis.
  - Set `use_json_response_format: true` for stricter, more deterministic outputs.
  - Set `synthesize_links: true` (default) to auto-create links between nodes based on type compatibility.
  - Set `auto_layout: true` (default) to assign positions and organize nodes topologically (configs left, processors middle, outputs right).
  - Use `retry_attempts` to harden prompt and re-invoke on JSON parse failures.
- **XtremetoolsWorkflowValidator**: Validates generated workflows for structural correctness—detects orphaned links, duplicate node IDs, missing required fields, and applies auto-fixes to `last_node_id`/`last_link_id` counters.
- **XtremetoolsWorkflowExporter**: Formats and exports workflows with optional metadata injection, Note node generation, and compact/pretty-print modes.

### Example Meta-Workflow Pattern

```
[User Description] → Workflow Request
                    ↓
                [LM Server Config] ┐
                [Model Config]     ├→ Workflow Generator → [Raw JSON]
                                  ↓                          ↓
                            [Retry Logic,            [Post-processor:
                             Link Synthesis,         DAG Layout,
                             JSON Enforcement]       Link Creation]
                                                     ↓
                                              [Structured Workflow]
                                              ↓
                                          Validator → [Validation Report]
                                              ↓
                                          Exporter → [Formatted JSON + Metadata]
```

### Deterministic Few-Shot Exemplars (Planned)

Future iterations will embed reference workflows for common patterns (SDXL persona prompting, multi-stage generation, quality control pipelines) directly in the generator's system prompt to improve consistency and reduce hallucinations.

## License
Distributed under the [MIT License](LICENSE). Contributions and issue reports are welcome.
