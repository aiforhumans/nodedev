# 🤖Xtremetools – AI Coding Guide

## Architecture Overview
**Source of Truth:** `Xtremetools/src/comfyui_xtremetools` (mirrored to `C:\ComfyUI_windows_portable\ComfyUI\custom_nodes\Xtremetools` via symlink).

**Core Flow:** Node discovery (`alias.py`) → Base classes (`base/node_base.py`, `base/lm_studio.py`) → Specific nodes (`nodes/*.py`) → LM Studio backend for prompt engineering.

**Key Abstraction:** The **alias loader** (`alias.py`) auto-discovers all files under `nodes/` and merges their `NODE_CLASS_MAPPINGS`/`NODE_DISPLAY_NAME_MAPPINGS`—no manual registry edits. ComfyUI imports this package without depending on non-ASCII paths.

## Development Workflow
- **Venv:** `C:/nodedev/.venv/Scripts/python.exe` with `python -m pip install -e .[dev]`
- **Test:** `python -m pytest` (tests all 51 nodes via `tests/test_nodes.py`)
- **Restart ComfyUI after node changes** for the symlink to reload
- **Update docs** when adding nodes or changing workflows (see `Docs/BEST_PRACTICES.md`, `Docs/LM_STUDIO.md`, `Docs/MIRRORING.md`)

## Node Patterns
**Every node must declare:**
- `CATEGORY` (e.g., `"🤖 Xtremetools/🤖 LM Studio"`)
- `RETURN_TYPES`, `RETURN_NAMES` tuples
- `FUNCTION` method name
- `INPUT_TYPES()` classmethod returning `{"required": {...}, "optional": {...}}`

**Return contract:** Always wrap outputs with `ensure_tuple()` to satisfy ComfyUI's tuple requirement. Example:
```python
def execute(self, param1, param2):
    result = compute(param1, param2)
    info = self.build_info("Node Name").add(f"Result: {result}").get()
    return self.ensure_tuple(result, info)
```

**Base classes:**
- `XtremetoolsBaseNode`: Base for all nodes; provides `ensure_tuple()`, `build_info()`, shared `CATEGORY`
- `XtremetoolsUtilityNode`: Lightweight helpers (text, string manipulation) with simpler `INPUT_TYPES()`
- `LMStudioBaseNode`: For HTTP chat endpoints; includes `build_messages()`, `invoke_chat_completion()`, dataclass support

**Telemetry:** Use `InfoFormatter` (from `base/info.py`) for structured output—avoid print/log. Categories use emoji (menu), but info strings must be ASCII-only.

## LM Studio Integration
**Dataclass-driven modularity:** Three settings objects travel through ComfyUI graphs:
- `LMStudioServerSettings`: URL + timeout
- `LMStudioModelSettings`: model name + fallback behavior
- `LMStudioGenerationSettings`: temperature, max_tokens, response_format

**Pattern:** `nodes/lm_studio_settings.py` emits these objects; `XtremetoolsLMStudioText` accepts either raw scalars or structured inputs, allowing flexible composition.

**Prompt engineering nodes** (7 helpers from `nodes/lm_studio_prompt_helpers.py`):
- `StylePreset`: role prompting (8 personas: neutral, concise, creative, technical, socratic, analytical, casual, step_by_step)
- `FewShotExamples`: XML-tagged exemplars (Anthropic best practice)
- `StructuredOutput`: explicit format instructions (XML/JSON/Markdown) + chain-of-thought
- `DualPrompt`: system/user separation for instruction + context
- `QualityControl`: 5 creativity/precision presets (concise_factual → exploratory)
- `PromptWeighter`: SDXL-style `(term:weight)` parsing
- `NegativePrompt`: topic/style constraints (lenient/moderate/strict)

**HTTP Pattern:** `base/lm_studio.py` wraps `/v1/chat/completions`; mocks in tests use `_DummyResponse` (don't call real servers). `.env` parsing + structured logging live in `config.py` and `logger.py` respectively.

## Meta-Workflow Generation
Four nodes automate workflow creation from natural language:
1. **WorkflowRequest** (`nodes/workflow_generator.py`): Structures user descriptions (type, complexity, required_nodes)
2. **WorkflowGenerator**: Calls LM Studio with schema-aware prompts, probes JSON-mode support via `generator.py`, retries when parsing fails, and clamps links via the live type registry.
3. **WorkflowValidator** (`workflow_validator.py`): Pydantic-powered spec enforcement + auto-fix for `last_node_id`/`last_link_id` counters.
4. **WorkflowExporter**: Formats output, injects metadata Note nodes, compact/pretty modes, and blocks exports if post-metadata validation fails.
5. **Self-Check node / CLI**: Surfaces node counts, last `/object_info` timestamp, structured JSON activation, and the last validation outcome.

**Post-processor** (`base/workflow_postprocessor.py`):
- `WorkflowDAGLayout`: Topological ordering (configs left, processors middle, outputs right) + position assignment
- `synthesize_links()`: Auto-creates links between nodes while checking the refreshed type registry for socket compatibility.

**Settings in Generator:**
- `auto_layout=true`: Topologically positions nodes (configs@100, processors@350, outputs@600)
- `synthesize_links=true`: Auto-wires compatible node types (validated via `type_registry.py`)
- `retry_attempts`: 1–3 attempts with JSON repair on parse failure
- `use_json_response_format=true`: Requests `response_format: {"type": "json_object"}` only when the model appears in `config/supported_models.json`; otherwise falls back to parser mode and logs a warning.
- Environment defaults (`COMFYUI_SERVER_URL`, `LM_STUDIO_SERVER_URL`, `LM_STUDIO_MODEL`, `XTREMETOOLS_SUPPORTED_MODELS`, `XTREMETOOLS_WORKFLOW_SCHEMA`) are read from `.env` via `config.py`.

## Testing Conventions
**File:** `tests/test_nodes.py` (51 tests, all passing)

**Test pattern:**
1. Import node class
2. Instantiate and call its main function
3. Assert return type is tuple, check data integrity
4. Verify info string contains expected telemetry

**Example:**
```python
def test_style_preset():
    node = XtremetoolsLMStudioStylePreset()
    prompt, info = node.build_style("creative")
    assert isinstance(prompt, str)
    assert "creative" in info.lower()
    assert isinstance(info, str)
```

**Mocking:** Avoid real LM Studio calls; use `_DummyResponse` fixtures for HTTP responses. For settings dataclasses, serialize→deserialize to verify payload correctness.

## File Organization
```
Xtremetools/src/comfyui_xtremetools/
├── __init__.py           # re-exports alias
├── alias.py              # auto-discovery: loads nodes/, merges mappings
├── base/
│   ├── info.py           # InfoFormatter (ASCII telemetry)
│   ├── node_base.py      # XtremetoolsBaseNode, XtremetoolsUtilityNode
│   ├── lm_studio.py      # LMStudioBaseNode, settings dataclasses, HTTP client
│   └── workflow_postprocessor.py  # DAG layout, link synthesis with registry checks
├── config.py / logger.py # .env + structured logging setup
├── node_discovery.py     # Fetch `/object_info`, refresh registry, expose CLI helper
├── type_registry.py      # Socket compatibility map + link guards
├── workflow_validator.py # Pydantic-enforced workflow JSON spec
├── generator.py          # Structured JSON guardrails + link clamping utilities
└── nodes/                # Auto-discovered by alias
    ├── example_prompt_tool.py     # XtremetoolsPromptJoiner (template)
    ├── lm_studio_text.py          # Main LM Studio generation node
    ├── lm_studio_settings.py      # Three settings emitter nodes
    ├── lm_studio_prompt_helpers.py # 7 prompt engineering nodes
    ├── self_check.py              # Diagnostics node
    └── workflow_generator.py      # Meta-workflow suite (request/generator/validator/exporter)
```

## Key Dependencies & Constraints
- **Python:** ≥3.10 (f-strings, dataclass slots, type hints)
- **ComfyUI:** Standard node interface
- **Runtime deps:** Stdlib + `pydantic` for schema enforcement (remaining deps mocked in tests)
- **Windows-specific paths:** Symlink setup (`Docs/MIRRORING.md`); use `Path` for cross-platform testing

## Documentation Ownership
- **README.md:** Onboarding, quick start, release checklist
- **Docs/BEST_PRACTICES.md:** ComfyUI contract (CATEGORY, INPUT_TYPES, tuple return, registration)
- **Docs/LM_STUDIO.md:** Workflow patterns, few-shot learning, structured output, quality control, HTTP 400 troubleshooting
- **Docs/XDEV_NOTES.md:** Competitive research (other node packs, design rationale)
- **Docs/MIRRORING.md:** Symlink setup and maintenance
- **workflows/README.md:** 10 reference workflows with use cases and architecture diagrams

Update docs when adding novel behavior or changing workflows so future agents understand rationale before editing code.

## Common Pitfalls
- ❌ **Returning non-tuples:** Always wrap with `ensure_tuple()`
- ❌ **Emoji in info strings:** Use ASCII-only telemetry; emoji only in CATEGORY
- ❌ **Manual registry edits:** Let `alias.py` discover nodes; no central mappings
- ❌ **Real LM Studio calls in tests:** Mock with `_DummyResponse`; check payloads
- ❌ **Forgetting to restart ComfyUI:** Symlink won't reload without restart
- ❌ **Unlinked workflows:** Always test with `synthesize_links=true` or manual wiring

## Immediate Next Steps
- Optional: Embed **deterministic few-shot exemplars** in WorkflowGenerator's system prompt (reduces hallucinations)
- Optionally: Create **template library** for common patterns (SDXL persona, quality control, reasoning chains)
- Test with **real LM Studio instance** and refine prompt tuning based on generation quality
