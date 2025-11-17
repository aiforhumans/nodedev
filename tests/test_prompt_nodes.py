"""Prompt and helper node tests."""
from __future__ import annotations

from comfyui_xtremetools.nodes.example_prompt_tool import XtremetoolsPromptJoiner
from comfyui_xtremetools.nodes.lm_studio_prompt_helpers import (
    XtremetoolsLMStudioDualPrompt,
    XtremetoolsLMStudioFewShotExamples,
    XtremetoolsLMStudioNegativePrompt,
    XtremetoolsLMStudioPromptWeighter,
    XtremetoolsLMStudioQualityControl,
    XtremetoolsLMStudioStructuredOutput,
    XtremetoolsLMStudioStylePreset,
)
from comfyui_xtremetools.nodes.test_node import XtremetoolsTestNode


def test_prompt_joiner_returns_tuple() -> None:
    node = XtremetoolsPromptJoiner()
    prompt, info = node.build_prompt("hello", "world", delimiter=", ")

    assert isinstance(prompt, str)
    assert isinstance(info, str)
    assert prompt == "hello, world"


def test_test_node_uppercase_behavior() -> None:
    node = XtremetoolsTestNode()
    text, info = node.emit("ping", repeat_count=2, uppercase=True, delimiter="-")

    assert text == "PING-PING"
    assert "Uppercase: True" in info
    assert "Repeat count: 2" in info


# ---- Style preset tests ----


def test_style_preset_node_applies_style() -> None:
    node = XtremetoolsLMStudioStylePreset()
    prompt, info = node.apply_style("concise")

    assert isinstance(prompt, str)
    assert "concise" in prompt.lower() or "brief" in prompt.lower()
    assert "Style: concise" in info


def test_style_preset_node_with_custom_addition() -> None:
    node = XtremetoolsLMStudioStylePreset()
    prompt, info = node.apply_style("technical", custom_addition="Focus on Python.")

    assert "technical" in prompt.lower()
    assert "Python" in prompt
    assert "Custom addition" in info


def test_style_preset_step_by_step() -> None:
    node = XtremetoolsLMStudioStylePreset()
    prompt, info = node.apply_style("step_by_step")

    assert "step by step" in prompt.lower()
    assert "reasoning" in prompt.lower()
    assert "Style: step_by_step" in info


# ---- Prompt weighter tests ----


def test_prompt_weighter_node_repeat_mode() -> None:
    node = XtremetoolsLMStudioPromptWeighter()
    weighted, info = node.apply_weights("Describe a (sunset:1.5) scene", weight_mode="repeat")

    assert "sunset sunset" in weighted
    assert "Weighted terms: 1" in info


def test_prompt_weighter_node_explicit_mode() -> None:
    node = XtremetoolsLMStudioPromptWeighter()
    weighted, info = node.apply_weights("A (dramatic:1.2) and (calm:0.4) landscape", weight_mode="explicit")

    assert "dramatic" in weighted
    assert "calm" in weighted
    assert "emphasize" in weighted.lower()
    assert "Weighted terms: 2" in info


# ---- Dual prompt tests ----


def test_dual_prompt_node_combines_inputs() -> None:
    node = XtremetoolsLMStudioDualPrompt()
    combined, info = node.combine_prompts("Write a story", "Genre: sci-fi")

    assert "Write a story" in combined
    assert "sci-fi" in combined
    assert "instruction→context" in info


def test_dual_prompt_node_context_first() -> None:
    node = XtremetoolsLMStudioDualPrompt()
    combined, info = node.combine_prompts("Question", "Background info", context_first=True)

    assert combined.index("Background") < combined.index("Question")
    assert "context→instruction" in info


# ---- Quality control tests ----


def test_quality_control_node_applies_preset() -> None:
    node = XtremetoolsLMStudioQualityControl()
    temp, tokens, top_p, info = node.apply_quality_preset("concise_factual")

    assert temp == 0.3
    assert tokens == 150
    assert top_p == 0.9
    assert "Preset: concise_factual" in info


def test_quality_control_node_with_adjustments() -> None:
    node = XtremetoolsLMStudioQualityControl()
    temp, tokens, top_p, info = node.apply_quality_preset(
        "balanced",
        temperature_adjust=0.2,
        tokens_adjust=100,
    )

    assert abs(temp - 0.9) < 0.01
    assert tokens == 612
    assert "Temp adjustment: +0.20" in info
    assert "Token adjustment: +100" in info


# ---- Negative prompt tests ----


def test_negative_prompt_node_builds_instruction() -> None:
    node = XtremetoolsLMStudioNegativePrompt()
    instruction, info = node.build_negative_instruction("politics, religion", strictness="moderate")

    assert "politics" in instruction
    assert "religion" in instruction
    assert "Avoid topics: 2" in info


def test_negative_prompt_node_with_style_filter() -> None:
    node = XtremetoolsLMStudioNegativePrompt()
    instruction, info = node.build_negative_instruction("", avoid_style="verbose", strictness="soft")

    assert "concise" in instruction.lower()
    assert "Style filter: verbose" in info


# ---- Few-shot examples tests ----


def test_few_shot_examples_node_single_example() -> None:
    node = XtremetoolsLMStudioFewShotExamples()
    examples, info = node.build_examples(
        example_1_input="What is 2+2?",
        example_1_output="4",
    )

    assert "<example>" in examples
    assert "<input>" in examples
    assert "<output>" in examples
    assert "2+2" in examples
    assert "4" in examples
    assert "Examples provided: 1" in info


def test_few_shot_examples_node_multiple_examples() -> None:
    node = XtremetoolsLMStudioFewShotExamples()
    examples, info = node.build_examples(
        example_1_input="Q1",
        example_1_output="A1",
        example_2_input="Q2",
        example_2_output="A2",
        example_3_input="Q3",
        example_3_output="A3",
    )

    assert examples.count("<example>") == 3
    assert "Examples provided: 3" in info
    assert "XML-tagged" in info


def test_few_shot_examples_node_empty_examples() -> None:
    node = XtremetoolsLMStudioFewShotExamples()
    examples, info = node.build_examples(
        example_1_input="",
        example_1_output="",
    )

    assert examples == ""
    assert "No valid examples" in info


# ---- Structured output tests ----


def test_structured_output_node_xml_format() -> None:
    node = XtremetoolsLMStudioStructuredOutput()
    instruction, info = node.build_format_instruction(output_format="xml", xml_tag_name="result")

    assert "<result>" in instruction
    assert "</result>" in instruction
    assert "Format: xml" in info


def test_structured_output_node_with_thinking() -> None:
    node = XtremetoolsLMStudioStructuredOutput()
    instruction, info = node.build_format_instruction(output_format="json", include_thinking=True)

    assert "<thinking>" in instruction
    assert "step-by-step" in instruction.lower()
    assert "JSON" in instruction
    assert "Chain-of-thought: enabled" in info


def test_structured_output_node_custom_format() -> None:
    node = XtremetoolsLMStudioStructuredOutput()
    custom_format = "Use haiku format: three lines, 5-7-5 syllables."
    instruction, info = node.build_format_instruction(
        output_format="custom",
        custom_format=custom_format,
    )

    assert "haiku" in instruction
    assert "5-7-5" in instruction
    assert "Format: custom" in info
