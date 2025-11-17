"""Meta-workflow generation nodes for creating ComfyUI workflows dynamically."""

import json
from typing import Any

from ..base.info import InfoFormatter
from ..base.lm_studio import LMStudioBaseNode
from ..base.node_base import XtremetoolsUtilityNode
from ..base.workflow_postprocessor import post_process_workflow


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
        """
        Generate ComfyUI workflow JSON from a structured request.
        
        Args:
            workflow_request: Structured request from WorkflowRequest node
            server_settings: LM Studio server configuration
            model_settings: LM Studio model configuration
            temperature: Generation temperature (low for precise JSON)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Tuple of (workflow_json, info_string)
        """
        info = InfoFormatter("Workflow Generator")

        try:
            current_system_prompt = self.SYSTEM_PROMPT
            workflow_json = "{}"
            extraction_method = "none"
            last_error: Exception | None = None
            parsed: dict[str, Any] | None = None
            result = None

            def _extract_json_only(text: str) -> tuple[str, str]:
                if text.startswith("{") and text.endswith("}"):
                    return text, "raw"
                if "```json" in text:
                    start_marker = "```json"
                    end_marker = "```"
                    start_idx = text.find(start_marker)
                    if start_idx != -1:
                        start_idx += len(start_marker)
                        end_idx = text.find(end_marker, start_idx)
                        if end_idx != -1:
                            return text[start_idx:end_idx].strip(), "fence"
                first = text.find("{")
                last = text.rfind("}")
                if first != -1 and last != -1 and last > first:
                    return text[first:last+1].strip(), "braces"
                return '{"nodes": [], "links": []}', "fallback"

            for attempt in range(1, retry_attempts + 1):
                system_prompt = current_system_prompt if attempt == 1 else current_system_prompt + f"\nRETRY {attempt}: STRICT JSON ONLY."
                messages = self.build_messages(prompt=workflow_request, system_prompt=system_prompt)
                result = self.invoke_chat_completion(
                    messages=messages,
                    server_url=server_settings.server_url,
                    model=model_settings.model,
                    timeout=server_settings.timeout,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    response_format={"type": "json_object"} if use_json_response_format else {"type": "text"},
                )
                workflow_text = result.text.strip()
                workflow_json, extraction_method = _extract_json_only(workflow_text)
                try:
                    parsed = json.loads(workflow_json)
                    last_error = None
                    break
                except json.JSONDecodeError as e:
                    last_error = e
                    cleaned = workflow_json.strip().strip("`")
                    if cleaned != workflow_json:
                        try:
                            parsed = json.loads(cleaned)
                            workflow_json = cleaned
                            extraction_method += "+trim"
                            last_error = None
                            break
                        except json.JSONDecodeError as e2:
                            last_error = e2
                    # continue retry loop

            if result is None:
                raise RuntimeError("No generation result captured")

            if last_error is None and parsed is not None:
                node_count = len(parsed.get("nodes", []))
                link_count = len(parsed.get("links", []))
                info.add("Status: OK Generated Successfully")
                info.add(f"Nodes: {node_count}")
                info.add(f"Links: {link_count}")
            else:
                info.add(f"Status: WARN JSON Parse Error after {retry_attempts} attempts: {str(last_error)[:120]}")
                info.add("Warning: Workflow may need manual correction")

            if len(workflow_json) > 100000:
                workflow_json = workflow_json[:100000]
                info.add("Warning: Output truncated due to size guard (100k chars)")

            # Apply post-processing: layout and link synthesis
            if synthesize_links or auto_layout:
                workflow_json = post_process_workflow(workflow_json, apply_layout=auto_layout, synthesize_links=synthesize_links)
                if synthesize_links:
                    info.add("Post-process: links synthesized")
                if auto_layout:
                    info.add("Post-process: DAG layout applied")

            info.add(f"Extraction: {extraction_method}")
            info.add("Strict JSON enforcement: applied")
            info.add(f"Retry attempts used: {retry_attempts if last_error else parsed is not None and 1 or retry_attempts}")
            info.add(f"Response format: {'json_object' if use_json_response_format else 'text'}")
            if debug:
                preview = workflow_json[:300].replace("\n", " ")
                info.add(f"Debug Preview: {preview}...")

            return self.ensure_tuple(workflow_json, info.render())

        except Exception as e:
            error_msg = f"Workflow generation failed: {str(e)}"
            info.add("Status: ERROR")
            info.add(f"Error: {str(e)[:200]}")
            return self.ensure_tuple("{}", info.render())


class XtremetoolsWorkflowValidator(XtremetoolsUtilityNode):
    """
    Validates generated workflow JSON for structural correctness.
    
    Checks for:
    - Valid JSON syntax
    - Required fields (nodes, links, last_node_id, last_link_id)
    - Node ID uniqueness
    - Link reference validity
    - Orphaned links
    """

    CATEGORY = "🤖 Xtremetools/🔧 Meta-Workflow"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "workflow_json": ("STRING", {"forceInput": True}),
            },
        }

    RETURN_TYPES = ("STRING", "BOOLEAN", "STRING")
    RETURN_NAMES = ("validation_report", "is_valid", "info")
    FUNCTION = "validate_workflow"

    # Minimal internal schema description for structural expectations
    _REQUIRED_TOP_LEVEL = ["nodes", "links", "last_node_id", "last_link_id"]
    _NODE_REQUIRED_FIELDS = ["id", "type"]
    _LINK_LENGTH = 6

    def _collect_node_link_maps(self, nodes: list[dict]) -> tuple[dict[int, set[int]], dict[int, set[int]]]:
        """Build maps of node id -> outgoing link ids, and node id -> incoming link ids."""
        outgoing: dict[int, set[int]] = {}
        incoming: dict[int, set[int]] = {}
        for node in nodes:
            node_id = node.get("id")
            if isinstance(node_id, int):
                # outputs
                out_links: set[int] = set()
                for out in node.get("outputs", []) or []:
                    if isinstance(out, dict):
                        for lid in out.get("links", []) or []:
                            if isinstance(lid, int):
                                out_links.add(lid)
                outgoing[node_id] = out_links
                # inputs
                in_links: set[int] = set()
                for inp in node.get("inputs", []) or []:
                    if isinstance(inp, dict):
                        lid = inp.get("link")
                        if isinstance(lid, int):
                            in_links.add(lid)
                incoming[node_id] = in_links
        return outgoing, incoming

    def validate_workflow(self, workflow_json: str) -> tuple[str, bool, str]:
        """
        Validate workflow JSON structure and references.
        
        Args:
            workflow_json: JSON string to validate
            
        Returns:
            Tuple of (validation_report, is_valid, info_string)
        """
        info = InfoFormatter("Workflow Validator")
        issues = []
        warnings = []

        # Check if empty
        if not workflow_json or workflow_json.strip() == "{}":
            issues.append("Empty workflow JSON")
            info.add("Status: ERROR Invalid")
            info.add("Issues: 1")
            return self.ensure_tuple("\n".join(issues), False, info.render())

        # Parse JSON
        try:
            workflow = json.loads(workflow_json)
        except json.JSONDecodeError as e:
            issues.append(f"JSON parse error: {str(e)}")
            info.add("Status: ERROR Invalid JSON")
            info.add(f"Error: {str(e)[:100]}")
            return self.ensure_tuple("\n".join(issues), False, info.render())

        # Check required top-level fields (schema)
        for field in self._REQUIRED_TOP_LEVEL:
            if field not in workflow:
                issues.append(f"Missing required field: '{field}'")

        # Validate nodes
        nodes = workflow.get("nodes", [])
        if not isinstance(nodes, list):
            issues.append("'nodes' must be an array")
        else:
            node_ids = set()
            for idx, node in enumerate(nodes):
                if not isinstance(node, dict):
                    issues.append(f"Node {idx}: Not a valid object")
                    continue

                if "id" not in node:
                    issues.append(f"Node {idx}: Missing 'id' field")
                else:
                    node_id = node["id"]
                    if node_id in node_ids:
                        issues.append(f"Node {node_id}: Duplicate node ID")
                    node_ids.add(node_id)

                if "type" not in node:
                    issues.append(f"Node {node.get('id', idx)}: Missing 'type' field")

                if "pos" not in node:
                    warnings.append(
                        f"Node {node.get('id', idx)}: Missing 'pos' (position)"
                    )

        # Validate links basic structure
        links = workflow.get("links", [])
        if not isinstance(links, list):
            issues.append("'links' must be an array")
        else:
            link_ids = set()
            for link in links:
                if not isinstance(link, list) or len(link) != self._LINK_LENGTH:
                    issues.append(f"Invalid link format: {link}")
                    continue

                link_id, source_id, source_out, target_id, target_in, link_type = link

                # Check duplicate link IDs
                if link_id in link_ids:
                    issues.append(f"Link {link_id}: Duplicate link ID")
                link_ids.add(link_id)

                # Check node references
                if nodes and isinstance(nodes, list):
                    if source_id not in node_ids:
                        issues.append(
                            f"Link {link_id}: References non-existent source node {source_id}"
                        )
                    if target_id not in node_ids:
                        issues.append(
                            f"Link {link_id}: References non-existent target node {target_id}"
                        )

        # Check last_node_id consistency & auto-fix suggestion
        if nodes and isinstance(nodes, list) and node_ids:
            expected_last_node_id = max(node_ids)
            actual_last_node_id = workflow.get("last_node_id", 0)
            if actual_last_node_id < expected_last_node_id:
                warnings.append(
                    f"last_node_id ({actual_last_node_id}) is less than highest node ID ({expected_last_node_id})"
                )
                workflow["last_node_id"] = expected_last_node_id  # auto-fix
                warnings.append("Applied auto-fix: last_node_id updated")

        # Check last_link_id consistency & auto-fix suggestion
        if links and isinstance(links, list) and link_ids:
            expected_last_link_id = max(link_ids)
            actual_last_link_id = workflow.get("last_link_id", 0)
            if actual_last_link_id < expected_last_link_id:
                warnings.append(
                    f"last_link_id ({actual_last_link_id}) is less than highest link ID ({expected_last_link_id})"
                )
                workflow["last_link_id"] = expected_last_link_id  # auto-fix
                warnings.append("Applied auto-fix: last_link_id updated")

        # Link symmetry validation
        if not issues:
            outgoing_map, incoming_map = self._collect_node_link_maps(nodes if isinstance(nodes, list) else [])
            for link in links if isinstance(links, list) else []:
                if not (isinstance(link, list) and len(link) == self._LINK_LENGTH):
                    continue
                link_id, source_id, _source_out_idx, target_id, _target_in_idx, _type = link
                if isinstance(source_id, int) and link_id not in outgoing_map.get(source_id, set()):
                    issues.append(f"Link {link_id}: not listed in source node {source_id} outputs")
                if isinstance(target_id, int) and link_id not in incoming_map.get(target_id, set()):
                    issues.append(f"Link {link_id}: not listed in target node {target_id} inputs")

        # Unknown node type warnings (non-fatal)
        from comfyui_xtremetools.alias import NODE_CLASS_MAPPINGS as _REGISTRY  # local import to avoid cycles
        for node in nodes if isinstance(nodes, list) else []:
            ntype = node.get("type")
            if isinstance(ntype, str) and ntype not in _REGISTRY:
                warnings.append(f"Unknown node type: {ntype}")

        # Build report
        report_parts = ["WORKFLOW VALIDATION REPORT", "=" * 50, ""]

        if not issues and not warnings:
            report_parts.append("OK VALID - No issues found")
            is_valid = True
            info.add("Status: OK Valid")
        else:
            is_valid = len(issues) == 0

            if issues:
                report_parts.append(f"ERRORS ({len(issues)}):")
                for issue in issues:
                    report_parts.append(f"  ERROR: {issue}")
                report_parts.append("")

            if warnings:
                report_parts.append(f"WARNINGS ({len(warnings)}):")
                for warning in warnings:
                    report_parts.append(f"  WARN: {warning}")
                report_parts.append("")

            status = "WARN Valid with warnings" if is_valid else "ERROR Invalid"
            report_parts.append(f"STATUS: {status}")
            info.add(f"Status: {status}")

        info.add(f"Nodes Checked: {len(nodes)}")
        info.add(f"Links Checked: {len(links)}")
        info.add(f"Errors: {len(issues)}")
        info.add(f"Warnings: {len(warnings)}")

        report = "\n".join(report_parts)
        return self.ensure_tuple(report, is_valid, info.render())


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

        try:
            # Parse JSON
            workflow = json.loads(workflow_json)

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

            return self.ensure_tuple(formatted, info.render())

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
