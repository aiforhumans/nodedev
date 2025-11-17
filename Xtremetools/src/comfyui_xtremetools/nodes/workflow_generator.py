"""Meta-workflow generation nodes for creating ComfyUI workflows dynamically."""

import json
from pathlib import Path
from typing import Any

from ..base.info import InfoFormatter
from ..base.lm_studio import LMStudioBaseNode
from ..base.node_base import XtremetoolsUtilityNode
from ..base.workflow_postprocessor import post_process_workflow
from ..config import get_environment_config
from ..generator import clamp_links_to_registry, extract_first_json_block, model_supports_structured_json
from ..logger import get_logger
from ..node_discovery import refresh_type_registry
from ..workflow_validator import validate_workflow_json

LOGGER = get_logger("xtremetools.nodes.workflow_generator")
_CONFIG = get_environment_config()
try:
    _SCHEMA_TEXT = Path(_CONFIG.workflow_schema_path).read_text(encoding="utf-8")
except FileNotFoundError:
    _SCHEMA_TEXT = "{}"


class XtremetoolsWorkflowRequest(XtremetoolsUtilityNode):
    """
    Captures user requirements for workflow generation and structures them into
    a formal request that can be processed by the WorkflowGenerator node.
    
    This node takes natural language descriptions and organizes them into a
    structured format that helps the AI understand what kind of workflow to create.
    """

    CATEGORY = "🤖 Xtremetools/🔧 Meta-Workflow"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "user_description": (
                    "STRING",
                    {
                        "default": "Create a workflow that generates creative SDXL prompts with few-shot examples",
                        "multiline": True,
                    },
                ),
                "workflow_type": (
                    [
                        "lm_studio_pipeline",
                        "prompt_engineering",
                        "multi_stage_generation",
                        "quality_control",
                        "custom",
                    ],
                    {"default": "lm_studio_pipeline"},
                ),
                "output_format": (
                    "STRING",
                    {
                        "default": "structured text (POSITIVE/NEGATIVE/STYLE)",
                        "multiline": False,
                    },
                ),
                "complexity": (
                    ["simple", "moderate", "complex"],
                    {"default": "moderate"},
                ),
            },
            "optional": {
                "required_nodes": (
                    "STRING",
                    {
                        "default": "",
                        "multiline": True,
                        "placeholder": "Optional: Specific nodes to include (comma-separated)",
                    },
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("structured_request", "info")
    FUNCTION = "build_request"

    def build_request(
        self,
        user_description: str,
        workflow_type: str,
        required_nodes: str = "",
        output_format: str = "SDXL prompt",
        complexity: str = "moderate",
    ) -> tuple[str, str]:
        """
        Build a structured workflow generation request from user inputs.
        
        Args:
            user_description: Natural language description of desired workflow
            workflow_type: Category of workflow to generate
            required_nodes: Optional comma-separated list of required nodes
            output_format: Expected output format
            complexity: Simple, moderate, or complex workflow
            
        Returns:
            Tuple of (structured_request, info_string)
        """
        info = InfoFormatter("Workflow Request")

        # Build structured request
        request_parts = [
            "WORKFLOW GENERATION REQUEST",
            "=" * 50,
            "",
            f"TYPE: {workflow_type}",
            f"COMPLEXITY: {complexity}",
            f"OUTPUT FORMAT: {output_format}",
            "",
            "USER DESCRIPTION:",
            user_description.strip(),
            "",
        ]

        if required_nodes.strip():
            request_parts.extend(
                [
                    "REQUIRED NODES:",
                    required_nodes.strip(),
                    "",
                ]
            )

        request_parts.extend(
            [
                "INSTRUCTIONS:",
                "Generate a complete ComfyUI workflow JSON that accomplishes the above goal.",
                "Include proper node connections, positioning, and documentation Note nodes.",
                "Ensure all link IDs and node IDs are unique and properly referenced.",
                "Position nodes left-to-right with proper spacing (400-500px horizontal, 200-300px vertical).",
            ]
        )

        structured_request = "\n".join(request_parts)

        # Build info output
        info.add(f"Request Type: {workflow_type}")
        info.add(f"Complexity: {complexity}")
        info.add(f"Output Format: {output_format}")
        info.add(f"Description Length: {len(user_description)} characters")
        if required_nodes.strip():
            node_list = [n.strip() for n in required_nodes.split(",")]
            info.add(f"Required Nodes: {len(node_list)} specified")

        return self.ensure_tuple(structured_request, info.render())


class XtremetoolsWorkflowGenerator(LMStudioBaseNode):
    """
    AI-powered workflow generator that creates ComfyUI workflow JSON from
    structured requests using LM Studio.
    
    This node uses a large language model with an extensive system prompt that
    teaches it about all available Xtremetools nodes, their structure, and how
    to create valid ComfyUI workflow JSON.
    """

    CATEGORY = "🤖 Xtremetools/🔧 Meta-Workflow"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "workflow_request": ("STRING", {"forceInput": True}),
                "server_settings": ("LM_STUDIO_SERVER", {"forceInput": True}),
                "model_settings": ("LM_STUDIO_MODEL", {"forceInput": True}),
                "temperature": (
                    "FLOAT",
                    {"default": 0.3, "min": 0.0, "max": 2.0, "step": 0.1},
                ),
                "max_tokens": (
                    "INT",
                    {"default": 4096, "min": 512, "max": 8192, "step": 512},
                ),
                "retry_attempts": (
                    "INT",
                    {"default": 1, "min": 1, "max": 3, "step": 1},
                ),
                "use_json_response_format": (
                    "BOOLEAN",
                    {"default": True},
                ),
                "debug": (
                    "BOOLEAN",
                    {"default": False},
                ),
                "auto_layout": (
                    "BOOLEAN",
                    {"default": True},
                ),
                "synthesize_links": (
                    "BOOLEAN",
                    {"default": True},
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("workflow_json", "info")
    FUNCTION = "generate_workflow"

    # Extensive system prompt teaching the AI about Xtremetools nodes
    SYSTEM_PROMPT = """You are a ComfyUI workflow architect specializing in Xtremetools nodes.

STRICT OUTPUT REQUIREMENT:
Respond ONLY with a single valid ComfyUI workflow JSON object. Do NOT include explanations, commentary, markdown fences, or multiple JSON objects. The first character MUST be '{' and the last MUST be '}'. If generation fails, return {"nodes": [], "links": []}.

AVAILABLE XTREMETOOLS NODES:

1. XtremetoolsLMStudioServerSettings
   - Inputs: base_url (STRING), timeout_seconds (FLOAT)
   - Outputs: LM_STUDIO_SERVER, info (STRING)
   - Purpose: Configure LM Studio server connection

2. XtremetoolsLMStudioModelSettings
   - Inputs: model_path (STRING)
   - Outputs: LM_STUDIO_MODEL, info (STRING)
   - Purpose: Specify which model to use

3. XtremetoolsLMStudioStylePreset
   - Inputs: preset (CHOICE), custom_addition (STRING)
   - Outputs: style_prompt (STRING), info (STRING)
   - Presets: neutral, concise, creative, technical, socratic, analytical, casual, step_by_step
   - Purpose: Add role-based persona prompting

4. XtremetoolsLMStudioFewShotExamples
   - Inputs: example_1_input/output, example_2_input/output, example_3_input/output (all STRING)
   - Outputs: few_shot_text (STRING), info (STRING)
   - Purpose: Provide XML-tagged example pairs for few-shot learning

5. XtremetoolsLMStudioStructuredOutput
   - Inputs: output_format (CHOICE), thinking_enabled (BOOLEAN), custom_format (STRING)
   - Outputs: format_instruction (STRING), info (STRING)
   - Formats: xml, json, markdown, numbered_list, bullet_points
   - Purpose: Request specific output structure

6. XtremetoolsLMStudioNegativePrompt
   - Inputs: avoid_topics (STRING), avoid_style (STRING), strictness (CHOICE)
   - Outputs: negative_instruction (STRING), info (STRING)
   - Strictness: lenient, moderate, strict
   - Purpose: Specify what to avoid in outputs

7. XtremetoolsLMStudioPromptWeighter
   - Inputs: weighted_terms (STRING)
   - Outputs: emphasis_instruction (STRING), info (STRING)
   - Format: (term:weight) syntax, e.g., (photorealistic:1.4)
   - Purpose: Parse and explain emphasis syntax for SDXL prompts

8. XtremetoolsLMStudioDualPrompt
   - Inputs: instruction (STRING), context (STRING)
   - Outputs: combined_prompt (STRING), info (STRING)
   - Purpose: Separate instruction from context data

9. XtremetoolsLMStudioQualityControl
   - Inputs: creativity_preset (CHOICE), temperature_adjustment (FLOAT), max_tokens_adjustment (INT)
   - Outputs: temperature (FLOAT), max_tokens (INT), info (STRING)
   - Presets: concise_factual, balanced, creative_verbose, exploratory, precise_technical
   - Purpose: Fine-tune generation parameters

10. XtremetoolsLMStudioText
    - Inputs: server_settings, model_settings, user_prompt (STRING), system_prompt (STRING, optional), temperature (FLOAT, optional), max_tokens (INT, optional)
    - Outputs: generated_text (STRING), info (STRING)
    - Purpose: Generate text via LM Studio API

11. XtremetoolsLMStudioPromptJoiner
    - Inputs: Up to 6 text inputs (STRING, optional), delimiter (STRING)
    - Outputs: combined_text (STRING), info (STRING)
    - Purpose: Combine multiple prompt components

THIRD-PARTY NODES (commonly used):

- SeargePromptCombiner: Combines two strings with configurable delimiter
  - Inputs: prompt1 (STRING), prompt2 (STRING), separator (STRING)
  - Outputs: combined (STRING)

- Note|pysssss: Documentation/comment node
  - Inputs: text (STRING)
  - No outputs (visual only)

- ShowText|pysssss: Display text output
  - Inputs: text (STRING)
  - No outputs (visual only)

NODE STRUCTURE TEMPLATE:
{
  "id": 1,
  "type": "NodeClassName",
  "pos": [x, y],
  "size": [width, height],
  "flags": {},
  "order": 0,
  "mode": 0,
  "inputs": [
    {"name": "input_name", "type": "TYPE", "link": linkId}
  ],
  "outputs": [
    {"name": "output_name", "type": "TYPE", "links": [linkId1, linkId2]}
  ],
  "properties": {"Node name for S&R": "NodeClassName"},
  "widgets_values": [value1, value2, ...]
}

LINK FORMAT:
[linkId, sourceNodeId, sourceOutputIndex, targetNodeId, targetInputIndex, "TYPE"]

POSITIONING RULES:
- Start at position [100, 100]
- Left-to-right flow: add 400-500 to x for each column
- Vertical spacing: add 200-300 to y between rows
- Group related nodes vertically (same x position, different y)
- Configuration nodes (ServerSettings, ModelSettings) typically at far left
- Output/display nodes (ShowText) typically at far right

WORKFLOW STRUCTURE:
{
  "last_node_id": N,
  "last_link_id": M,
  "nodes": [...],
  "links": [...],
  "groups": [...],
  "config": {},
  "extra": {},
  "version": 0.4
}

GROUPS (optional color-coding):
{
  "title": "Group Name",
  "bounding": [x, y, width, height],
  "color": "#3f789e",
  "font_size": 24,
  "flags": {}
}

IMPORTANT RULES:
1. All link IDs must be unique across the workflow
2. All node IDs must be unique across the workflow
3. Every link must reference existing node IDs
4. Source node outputs must list all outgoing link IDs
5. Target node inputs must reference incoming link IDs
6. Widget values must match node's expected types and defaults
7. Include helpful Note nodes explaining the workflow purpose
8. Use groups to organize related nodes visually

Generate a complete, valid ComfyUI workflow JSON that accomplishes the user's goal.
Output MUST be raw JSON only (no fences, no prose)."""

    def generate_workflow(
        self,
        workflow_request: str,
        server_settings: Any,
        model_settings: Any,
        temperature: float = 0.3,
        max_tokens: int = 4096,
        retry_attempts: int = 1,
        use_json_response_format: bool = True,
        debug: bool = False,
        auto_layout: bool = True,
        synthesize_links: bool = True,
    ) -> tuple[str, str]:
        """Generate ComfyUI workflow JSON from a structured request."""

        info = InfoFormatter("Workflow Generator")
        refresh_type_registry()

        server_url = server_settings.server_url or _CONFIG.lm_studio_server_url
        model_name = model_settings.model or _CONFIG.lm_studio_model

        structured_supported = use_json_response_format and model_supports_structured_json(model_name)
        response_format = {"type": "json_object"} if structured_supported else {"type": "text"}
        info.add(f"Structured JSON mode: {'enabled' if structured_supported else 'fallback parsing'}")

        base_system_prompt = self.SYSTEM_PROMPT
        if structured_supported:
            base_system_prompt += f"\nJSON SCHEMA (STRICT):\n{_SCHEMA_TEXT}\n"
        else:
            base_system_prompt += "\nIf structured mode fails, emit the best possible workflow JSON block so the parser can recover."

        workflow_json = "{}"
        extraction_method = "none"
        last_error: Exception | None = None
        parsed_payload: dict[str, Any] | None = None
        result = None

        for attempt in range(1, retry_attempts + 1):
            system_prompt = base_system_prompt if attempt == 1 else base_system_prompt + f"\nRETRY {attempt}: STRICT JSON ONLY."
            messages = self.build_messages(prompt=workflow_request, system_prompt=system_prompt)
            try:
                result = self.invoke_chat_completion(
                    messages=messages,
                    server_url=server_url,
                    model=model_name,
                    timeout=server_settings.timeout,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format=response_format,
                )
            except Exception as exc:  # pragma: no cover - network issues raised upstream
                last_error = exc
                LOGGER.error("LM Studio call failed: %s", exc)
                continue

            workflow_text = result.text.strip()
            if structured_supported and response_format.get("type") == "json_object":
                candidate = workflow_text
                extraction_method = "structured"
            else:
                candidate, extraction_method = extract_first_json_block(workflow_text)

            try:
                parsed_payload = json.loads(candidate)
                workflow_json = candidate
                last_error = None
                break
            except json.JSONDecodeError as exc:
                last_error = exc
                LOGGER.warning("JSON decode failed (attempt %s): %s", attempt, exc)
                if structured_supported:
                    structured_supported = False
                    response_format = {"type": "text"}
                    info.add("Structured mode failed → falling back to parser path")
                continue

        if result is None:
            info.add("Status: ERROR")
            info.add("No generation result captured")
            return self.ensure_tuple("{}", info.render())

        if parsed_payload is None:
            info.add("Status: ERROR")
            info.add(f"Failed to parse workflow after {retry_attempts} attempts: {last_error}")
            return self.ensure_tuple("{}", info.render())

        node_count = len(parsed_payload.get("nodes", []))
        link_count = len(parsed_payload.get("links", []))
        info.add(f"Nodes: {node_count}")
        info.add(f"Links: {link_count}")

        processed = workflow_json
        if synthesize_links or auto_layout:
            processed = post_process_workflow(processed, apply_layout=auto_layout, synthesize_links=synthesize_links)
        processed = clamp_links_to_registry(processed)

        validation = validate_workflow_json(processed, auto_fix=True)
        processed = validation.workflow_json
        info.add(f"Validation: {'pass' if validation.is_valid else 'fail'}")
        if validation.errors:
            info.add(f"Errors: {len(validation.errors)}")
        if validation.warnings:
            info.add(f"Warnings: {len(validation.warnings)}")

        info.add(f"Extraction: {extraction_method}")
        info.add(f"Response format: {response_format.get('type')}")
        if debug:
            preview = processed[:300].replace("\n", " ")
            info.add(f"Debug Preview: {preview}...")

        return self.ensure_tuple(processed, info.render())


class XtremetoolsWorkflowValidator(XtremetoolsUtilityNode):
    CATEGORY = "🤖 Xtremetools/🔧 Meta-Workflow"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {"required": {"workflow_json": ("STRING", {"forceInput": True})}}

    RETURN_TYPES = ("STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("validation_report", "is_valid", "info")
    FUNCTION = "validate_workflow"

    def validate_workflow(self, workflow_json: str) -> tuple[str, bool, str]:
        result = validate_workflow_json(workflow_json, auto_fix=True)
        info = InfoFormatter("Workflow Validator")
        status = "OK" if result.is_valid else "ERROR"
        info.add(f"Status: {status}")
        info.add(f"Errors: {len(result.errors)}")
        info.add(f"Warnings: {len(result.warnings)}")
        return self.ensure_tuple(result.report, result.is_valid, info.render())


class XtremetoolsWorkflowExporter(XtremetoolsUtilityNode):
    """
    Formats workflow JSON for file export with pretty-printing and metadata.
    
    Adds metadata like generation timestamp and Xtremetools version, and formats
    the JSON with proper indentation for human readability.
    """

    CATEGORY = "🤖 Xtremetools/🔧 Meta-Workflow"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "workflow_json": ("STRING", {"forceInput": True}),
                "indent": (
                    "INT",
                    {"default": 2, "min": 0, "max": 8, "step": 1},
                ),
                "add_metadata": (
                    "BOOLEAN",
                    {"default": True},
                ),
                "add_metadata_note": (
                    "BOOLEAN",
                    {"default": True},
                ),
                "compact": (
                    "BOOLEAN",
                    {"default": False},
                ),
            },
        }

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("formatted_json", "info")
    FUNCTION = "export_workflow"

    def export_workflow(
        self,
        workflow_json: str,
        indent: int = 2,
        add_metadata: bool = True,
        add_metadata_note: bool = True,
        compact: bool = False,
    ) -> tuple[str, str]:
        """
        Format workflow JSON for export.
        
        Args:
            workflow_json: Raw workflow JSON string
            indent: Number of spaces for indentation (0 = compact)
            add_metadata: Whether to add generation metadata
            
        Returns:
            Tuple of (formatted_json, info_string)
        """
        info = InfoFormatter("Workflow Exporter")

        validation = validate_workflow_json(workflow_json, auto_fix=True)
        if not validation.is_valid:
            info.add("Status: ERROR")
            info.add("Export blocked: validation failed")
            return self.ensure_tuple(validation.report, info.render())

        try:
            # Parse JSON
            workflow = json.loads(validation.workflow_json)

            # Add metadata if requested
            if add_metadata:
                if "extra" not in workflow:
                    workflow["extra"] = {}
                workflow["extra"]["generated_by"] = "Xtremetools Workflow Generator"
                workflow["extra"]["generator_version"] = "1.0"
                workflow.setdefault("version", 0.4)

            # Add metadata Note node for human context
            if add_metadata and add_metadata_note:
                note_id = (workflow.get("last_node_id") or 0) + 1
                note_node = {
                    "id": note_id,
                    "type": "Note",
                    "pos": [100, (workflow.get("last_node_id") or 0) * 10 + 50],
                    "size": [300, 100],
                    "flags": {},
                    "order": 0,
                    "mode": 0,
                    "properties": {"Node name for S&R": "Note"},
                    "widgets_values": [
                        "Generated by Xtremetools exporter with metadata."
                    ],
                }
                workflow.setdefault("nodes", []).append(note_node)
                workflow["last_node_id"] = note_id
                info.add("Metadata Note: added")

            # Format with specified indentation
            if compact:
                indent = 0
            if indent == 0:
                formatted = json.dumps(workflow, ensure_ascii=False)
                info.add("Format: Compact (no indentation)")
            else:
                formatted = json.dumps(workflow, indent=indent, ensure_ascii=False)
                info.add(f"Format: Indented ({indent} spaces)")

            # Calculate size
            size_bytes = len(formatted.encode("utf-8"))
            if size_bytes < 1024:
                size_str = f"{size_bytes} bytes"
            elif size_bytes < 1024 * 1024:
                size_str = f"{size_bytes / 1024:.1f} KB"
            else:
                size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

            info.add("Status: OK Formatted")
            info.add(f"Size: {size_str}")
            info.add(f"Metadata Added: {'Yes' if add_metadata else 'No'}")
            info.add("Ready for Export: Copy from ShowText node")

            # Final validation after metadata injection to ensure schema compliance
            final_validation = validate_workflow_json(formatted, auto_fix=True)
            if not final_validation.is_valid:
                info.add("Status: ERROR")
                info.add("Export blocked after metadata injection")
                return self.ensure_tuple(final_validation.report, info.render())
            final_payload = json.loads(final_validation.workflow_json)
            if indent == 0:
                final_output = json.dumps(final_payload, ensure_ascii=False)
            else:
                final_output = json.dumps(final_payload, indent=indent if not compact else None, ensure_ascii=False)

            return self.ensure_tuple(final_output, info.render())

        except json.JSONDecodeError as e:
            error_msg = f"JSON parse error: {str(e)}"
            info.add("Status: ERROR")
            info.add(f"Error: {str(e)[:100]}")
            return self.ensure_tuple(workflow_json, info.render())


# Node registration
NODE_CLASS_MAPPINGS = {
    "XtremetoolsWorkflowRequest": XtremetoolsWorkflowRequest,
    "XtremetoolsWorkflowGenerator": XtremetoolsWorkflowGenerator,
    "XtremetoolsWorkflowValidator": XtremetoolsWorkflowValidator,
    "XtremetoolsWorkflowExporter": XtremetoolsWorkflowExporter,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XtremetoolsWorkflowRequest": "🔧 Workflow Request",
    "XtremetoolsWorkflowGenerator": "🔧 Workflow Generator (AI)",
    "XtremetoolsWorkflowValidator": "🔧 Workflow Validator",
    "XtremetoolsWorkflowExporter": "🔧 Workflow Exporter",
}
