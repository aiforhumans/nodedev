# LM Studio Integration Notes

## Requirements
- Install [LM Studio](https://lmstudio.ai/) locally and launch the server interface.
- Load at least one chat-capable model; the default ComfyUI nodes assume the server listens on `http://localhost:1234`.
- For remote hosts or different ports, supply the custom URL via the `server_url` input on the node or connect the `LM_STUDIO_SERVER` output from `XtremetoolsLMStudioServerSettings`.

## Provided Nodes
- `XtremetoolsLMStudioText` (category `Xtremetools/LM Studio`)
  - Inputs: prompt, optional user/system prompts, scalar overrides, plus three typed settings inputs (`LM_STUDIO_SERVER`, `LM_STUDIO_MODEL`, `LM_STUDIO_GENERATION`).
  - Outputs: generated text plus an info string summarizing model, finish reason, token usage, and latency.
- `XtremetoolsLMStudioServerSettings`
  - Emits server URL + timeout as `LM_STUDIO_SERVER`; reuse it wherever you need a consistent endpoint profile.
- `XtremetoolsLMStudioModelSettings`
  - Captures preferred model plus whether falling back to LM Studio's default model is acceptable.
- `XtremetoolsLMStudioGenerationSettings`
  - Bundles temperature, max tokens, and response format (`text` or `json_object`) into a single output.

### Prompt Helpers (Prompt Engineering Best Practices)
Inspired by research from Anthropic and OpenAI, these nodes implement proven prompt engineering techniques for better LLM outputs.

#### 🎭 Style & Role Prompting
- **`XtremetoolsLMStudioStylePreset`**
  - Implements role prompting patterns (Anthropic best practice) with 8 persona presets:
    - `neutral`: Balanced helpful assistant
    - `concise`: Expert at distilling complex info into brief answers
    - `creative`: Original thinking with practical value
    - `technical`: Subject matter expert with precise terminology
    - `socratic`: Guides through questions for deep understanding
    - `analytical`: Systematic breakdown with reasoned conclusions
    - `casual`: Approachable companion with relatable examples
    - `step_by_step`: Chain-of-thought reasoning before responding
  - Optional custom additions extend base prompts for domain-specific tweaks.

#### ⚖️ Emphasis & Weighting
- **`XtremetoolsLMStudioPromptWeighter`**
  - Parse SDXL-style `(word:weight)` syntax (e.g., `(dramatic:1.5)`, `(subtle:0.5)`)
  - Two modes:
    - `repeat`: Duplicate words based on weight (1.5 → 2 instances, 2.5 → 3 instances)
    - `explicit`: Convert to emphasis instructions ("dramatic" emphasize strongly)
  - Adapted from image generation weight syntax for text-based emphasis control.

#### 🔀 Instruction + Context Separation
- **`XtremetoolsLMStudioDualPrompt`**
  - Inspired by SDXL's dual CLIP text encoders (text_g + text_l)
  - Separate "instruction" (task directive) and "context" (background info) inputs
  - Configurable order (instruction→context or context→instruction)
  - Follows OpenAI's system/user message separation pattern for clearer prompt structure.

#### 🎚️ Quality Control Presets
- **`XtremetoolsLMStudioQualityControl`**
  - 5 generation presets based on creativity/verbosity/precision tradeoffs:
    - `concise_factual`: Low temp (0.3), 150 tokens — focused, deterministic
    - `balanced`: Mid temp (0.7), 512 tokens — general-purpose
    - `creative_verbose`: High temp (0.9), 1024 tokens — imaginative, expansive
    - `exploratory`: Very high temp (1.1), 768 tokens — experimental thinking
    - `precise_technical`: Low temp (0.2), 600 tokens — accuracy-first responses
  - Adjustments for temperature (±0.5) and token count (±512) to fine-tune outputs.

#### 🚫 Negative Prompting
- **`XtremetoolsLMStudioNegativePrompt`**
  - System instructions to avoid specific topics/styles (OpenAI constraint pattern)
  - Topic-based avoidance: comma-separated list with strictness levels (soft/moderate/strict)
  - Style filters: verbose, technical_jargon, speculation, personal_opinions
  - Generates explicit constraints like "You must not discuss: politics, religion."

#### 📚 Few-Shot Learning
- **`XtremetoolsLMStudioFewShotExamples`** (NEW)
  - Implements Anthropic's XML-tagging best practice for example encapsulation
  - Up to 3 input/output example pairs wrapped in `<example><input></input><output></output></example>` tags
  - Proven to significantly improve output quality and format adherence
  - Optional instruction prefix customization (e.g., "Here are examples of the desired format:")
  - Follows research showing 3+ examples yield best results for most tasks.

#### 📋 Structured Output Formatting
- **`XtremetoolsLMStudioStructuredOutput`** (NEW)
  - Explicit output format instructions (critical for reliable structured responses)
  - 5 built-in formats:
    - `xml`: Wrap response in custom XML tags (e.g., `<answer></answer>`)
    - `json`: Valid JSON object with clear key-value pairs
    - `markdown`: Proper headings, lists, code blocks
    - `numbered_list`: Clear numbered points (1., 2., 3.)
    - `bullet_points`: Concise bullet list (- item)
  - **Chain-of-thought toggle**: Enable `<thinking></thinking>` tags for step-by-step reasoning before final answer (OpenAI/Anthropic technique)
  - Custom format support for domain-specific output requirements
  - Research shows explicit format instructions reduce hallucination and improve reliability.

## Prompt Engineering Workflow Patterns

### Pattern 1: System Prompt Construction
```
StylePreset (technical + custom_addition) 
  → NegativePrompt (avoid speculation)
  → Dual Prompt (instruction + context)
  → LM Studio Text
```

### Pattern 2: Few-Shot Learning
```
StylePreset (step_by_step)
  → FewShotExamples (3 input/output pairs)
  → StructuredOutput (xml + thinking enabled)
  → LM Studio Text
```

### Pattern 3: Quality-Controlled Generation
```
QualityControl (creative_verbose + temp_adjust +0.2)
  → PromptWeighter ((dramatic:1.5) in prompt)
  → StructuredOutput (json)
  → LM Studio Text
```

These patterns combine research-backed techniques: role prompting establishes expertise, few-shot examples demonstrate desired behavior, chain-of-thought improves reasoning, and structured output ensures reliable format adherence.

## Base Helper
- `base/lm_studio.py` exposes `LMStudioBaseNode`, which wraps the `/v1/chat/completions` endpoint via `urllib.request`.
- Shared behaviors: message construction, JSON + error handling, latency tracking, and info string formatting.
- Extend this base class for additional nodes (batching, streaming, ControlNet-aware prompt builders, etc.).

## Troubleshooting
- `LMStudioAPIError` surfaces connectivity issues, missing models, and invalid responses; ComfyUI will surface the exception.
- **HTTP 400** usually means LM Studio has no model loaded. Open LM Studio, load a chat model, or set the `model` input on the node to match the identifier listed under `/v1/models`.
- Ensure LM Studio is running before executing the workflow; restarting ComfyUI may be necessary after adding new nodes.
- Use the included pytest suite (`python -m pytest`) to validate alias wiring and HTTP mocks without needing a live LM Studio server.

## MCP Test Harness
- New MCP-specific tests live under `tests/mcp/` and are tagged with the `mcp` marker.
- Run only those suites via `python -m pytest -m mcp`; this exercises the Fake MCP client, node adapters, and workflow round-trip assertions.
- The harness sits entirely on mocked LM Studio + HTTP stubs, so no live GitHub or LM Studio servers are required.
- CI can skip these tests with `-m "not mcp"` when a faster smoke suite is preferred; nightly jobs should include them to catch schema drift early.
