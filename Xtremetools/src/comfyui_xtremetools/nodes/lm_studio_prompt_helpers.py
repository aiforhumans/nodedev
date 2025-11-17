"""SDXL-inspired prompt composition nodes for LM Studio workflows."""
from __future__ import annotations

from typing import Any

from comfyui_xtremetools.base.node_base import XtremetoolsBaseNode


class _LMStudioPromptBase(XtremetoolsBaseNode):
    CATEGORY = "🤖 Xtremetools/🤖 LM Studio/✍️ Prompts"


class XtremetoolsLMStudioStylePreset(_LMStudioPromptBase):
    """Select persona/tone preset using role prompting best practices."""

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("system_prompt", "info")
    FUNCTION = "apply_style"

    STYLE_PRESETS = {
        "neutral": "You are a helpful AI assistant. Your goal is to provide accurate, relevant information while being respectful and professional.",
        "concise": "You are an expert at distilling complex information into clear, brief answers. Prioritize directness over elaboration. Aim for maximum clarity in minimum words.",
        "creative": "You are a creative thinker and problem solver. Approach each request with originality and imagination. Challenge conventional thinking while maintaining practical value.",
        "technical": "You are a technical subject matter expert. Use precise terminology, provide detailed explanations, and cite specific technical details when relevant. Assume a knowledgeable audience.",
        "socratic": "You are a Socratic tutor who values deep understanding. Instead of giving direct answers, guide learners through thoughtful questions that help them discover insights themselves.",
        "analytical": "You are an analytical thinker who examines problems systematically. Break down complex issues into components, evaluate each factor methodically, and present well-reasoned conclusions.",
        "casual": "You are a friendly, approachable AI companion. Use natural, conversational language and relatable examples. Make complex topics accessible without being condescending.",
        "step_by_step": "You are an expert at breaking down complex tasks. For any request involving multiple steps, think step by step before responding. Show your reasoning process clearly.",
    }

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "style": (list(cls.STYLE_PRESETS.keys()),),
            },
            "optional": {
                "custom_addition": ("STRING", {"default": "", "multiline": True}),
            },
        }

    def apply_style(self, style: str, custom_addition: str = "") -> tuple[str, str]:
        base_prompt = self.STYLE_PRESETS.get(style, self.STYLE_PRESETS["neutral"])
        
        if custom_addition.strip():
            system_prompt = f"{base_prompt}\n\n{custom_addition.strip()}"
        else:
            system_prompt = base_prompt

        info = self.build_info("Style Preset")
        info.add(f"Style: {style}")
        info.add(f"Base length: {len(base_prompt)} chars")
        if custom_addition.strip():
            info.add(f"Custom addition: {len(custom_addition.strip())} chars")
        
        return self.ensure_tuple(system_prompt, info.render())


class XtremetoolsLMStudioPromptWeighter(_LMStudioPromptBase):
    """Parse (word:weight) syntax and expand into emphasis instructions."""

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("weighted_prompt", "info")
    FUNCTION = "apply_weights"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "prompt": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "weight_mode": (["repeat", "explicit"],),
            },
        }

    def apply_weights(self, prompt: str, weight_mode: str = "repeat") -> tuple[str, str]:
        import re
        
        # Find all (word:weight) patterns
        pattern = r'\(([^:)]+):(\d*\.?\d+)\)'
        matches = list(re.finditer(pattern, prompt))
        
        if not matches:
            info = self.build_info("Prompt Weighter")
            info.add("No weighted terms found")
            return self.ensure_tuple(prompt, info.render())
        
        weighted_prompt = prompt
        emphasis_count = 0
        
        if weight_mode == "repeat":
            # Replace (word:weight) with repeated words based on weight
            for match in reversed(matches):  # Reverse to preserve indices
                word = match.group(1).strip()
                try:
                    weight = float(match.group(2))
                except ValueError:
                    weight = 1.0
                
                # Convert weight to repetition count (0.5 = skip, 1.0 = once, 1.5 = twice, etc.)
                if weight < 0.5:
                    repeat_count = 0
                elif weight >= 1.5:
                    repeat_count = int(weight) + 1
                else:
                    repeat_count = max(1, int(weight))
                
                replacement = " ".join([word] * repeat_count) if repeat_count > 0 else ""
                weighted_prompt = weighted_prompt[:match.start()] + replacement + weighted_prompt[match.end():]
                emphasis_count += 1
        
        elif weight_mode == "explicit":
            # Build explicit emphasis instructions
            emphasis_list = []
            for match in matches:
                word = match.group(1).strip()
                try:
                    weight = float(match.group(2))
                except ValueError:
                    weight = 1.0
                
                if weight > 1.0:
                    emphasis_list.append(f'"{word}" (emphasize strongly)')
                elif weight > 0.7:
                    emphasis_list.append(f'"{word}" (emphasize)')
                elif weight < 0.5:
                    emphasis_list.append(f'"{word}" (de-emphasize)')
            
            # Remove weight syntax and add explicit instruction
            weighted_prompt = re.sub(pattern, r'\1', prompt)
            if emphasis_list:
                instruction = "Focus on these terms:\n- " + "\n- ".join(emphasis_list)
                weighted_prompt = f"{weighted_prompt}\n\n{instruction}"
                emphasis_count = len(emphasis_list)
        
        info = self.build_info("Prompt Weighter")
        info.add(f"Mode: {weight_mode}")
        info.add(f"Weighted terms: {emphasis_count}")
        info.add(f"Output length: {len(weighted_prompt)} chars")
        
        return self.ensure_tuple(weighted_prompt, info.render())


class XtremetoolsLMStudioDualPrompt(_LMStudioPromptBase):
    """Combine instruction + context inputs (like SDXL dual encoders)."""

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("combined_prompt", "info")
    FUNCTION = "combine_prompts"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "instruction": ("STRING", {"default": "", "multiline": True}),
                "context": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "separator": ("STRING", {"default": "\n\n"}),
                "context_first": ("BOOLEAN", {"default": False}),
            },
        }

    def combine_prompts(
        self,
        instruction: str,
        context: str,
        separator: str = "\n\n",
        context_first: bool = False,
    ) -> tuple[str, str]:
        instruction_clean = instruction.strip()
        context_clean = context.strip()
        
        if not instruction_clean and not context_clean:
            combined = ""
        elif not instruction_clean:
            combined = context_clean
        elif not context_clean:
            combined = instruction_clean
        else:
            if context_first:
                combined = f"{context_clean}{separator}{instruction_clean}"
            else:
                combined = f"{instruction_clean}{separator}{context_clean}"
        
        info = self.build_info("Dual Prompt")
        info.add(f"Instruction: {len(instruction_clean)} chars")
        info.add(f"Context: {len(context_clean)} chars")
        info.add(f"Order: {'context→instruction' if context_first else 'instruction→context'}")
        info.add(f"Combined: {len(combined)} chars")
        
        return self.ensure_tuple(combined, info.render())


class XtremetoolsLMStudioQualityControl(_LMStudioPromptBase):
    """Preset-based controls for creativity, verbosity, and focus."""

    RETURN_TYPES = ("FLOAT", "INT", "FLOAT", "STRING")
    RETURN_NAMES = ("temperature", "max_tokens", "top_p", "info")
    FUNCTION = "apply_quality_preset"

    QUALITY_PRESETS = {
        "concise_factual": {"temperature": 0.3, "max_tokens": 150, "top_p": 0.9},
        "balanced": {"temperature": 0.7, "max_tokens": 512, "top_p": 0.95},
        "creative_verbose": {"temperature": 0.9, "max_tokens": 1024, "top_p": 0.98},
        "exploratory": {"temperature": 1.1, "max_tokens": 768, "top_p": 1.0},
        "precise_technical": {"temperature": 0.2, "max_tokens": 600, "top_p": 0.85},
    }

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "preset": (list(cls.QUALITY_PRESETS.keys()),),
            },
            "optional": {
                "temperature_adjust": ("FLOAT", {"default": 0.0, "min": -0.5, "max": 0.5, "step": 0.05}),
                "tokens_adjust": ("INT", {"default": 0, "min": -512, "max": 512}),
            },
        }

    def apply_quality_preset(
        self,
        preset: str,
        temperature_adjust: float = 0.0,
        tokens_adjust: int = 0,
    ) -> tuple[float, int, float, str]:
        config = self.QUALITY_PRESETS.get(preset, self.QUALITY_PRESETS["balanced"])
        
        temperature = max(0.0, min(2.0, config["temperature"] + temperature_adjust))
        max_tokens = max(16, min(8192, config["max_tokens"] + tokens_adjust))
        top_p = config["top_p"]
        
        info = self.build_info("Quality Control")
        info.add(f"Preset: {preset}")
        info.add(f"Temperature: {temperature:.2f}")
        info.add(f"Max tokens: {max_tokens}")
        info.add(f"Top-p: {top_p:.2f}")
        if temperature_adjust != 0.0:
            info.add(f"Temp adjustment: {temperature_adjust:+.2f}")
        if tokens_adjust != 0:
            info.add(f"Token adjustment: {tokens_adjust:+d}")
        
        return self.ensure_tuple(temperature, max_tokens, top_p, info.render())


class XtremetoolsLMStudioNegativePrompt(_LMStudioPromptBase):
    """Generate system instructions to avoid specific topics/styles."""

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("system_instruction", "info")
    FUNCTION = "build_negative_instruction"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "avoid_topics": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "avoid_style": (["none", "verbose", "technical_jargon", "speculation", "personal_opinions"],),
                "strictness": (["soft", "moderate", "strict"],),
            },
        }

    def build_negative_instruction(
        self,
        avoid_topics: str,
        avoid_style: str = "none",
        strictness: str = "moderate",
    ) -> tuple[str, str]:
        instructions = []
        
        topics = [t.strip() for t in avoid_topics.split(",") if t.strip()]
        if topics:
            if strictness == "strict":
                prefix = "You must not discuss or mention"
            elif strictness == "soft":
                prefix = "Try to avoid discussing"
            else:
                prefix = "Avoid discussing"
            
            instructions.append(f"{prefix}: {', '.join(topics)}.")
        
        style_guidance = {
            "verbose": "Keep responses concise and avoid unnecessary elaboration.",
            "technical_jargon": "Use plain language and avoid technical jargon unless necessary.",
            "speculation": "Stick to facts and avoid speculation or unverified claims.",
            "personal_opinions": "Remain objective and avoid expressing personal opinions.",
        }
        
        if avoid_style != "none" and avoid_style in style_guidance:
            instructions.append(style_guidance[avoid_style])
        
        system_instruction = "\n".join(instructions) if instructions else ""
        
        info = self.build_info("Negative Prompt")
        info.add(f"Avoid topics: {len(topics)}")
        info.add(f"Style filter: {avoid_style}")
        info.add(f"Strictness: {strictness}")
        info.add(f"Instruction length: {len(system_instruction)} chars")
        
        return self.ensure_tuple(system_instruction, info.render())


class XtremetoolsLMStudioFewShotExamples(_LMStudioPromptBase):
    """Build few-shot example section using XML tag encapsulation (Anthropic best practice)."""

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("examples_section", "info")
    FUNCTION = "build_examples"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "example_1_input": ("STRING", {"default": "", "multiline": True}),
                "example_1_output": ("STRING", {"default": "", "multiline": True}),
            },
            "optional": {
                "example_2_input": ("STRING", {"default": "", "multiline": True}),
                "example_2_output": ("STRING", {"default": "", "multiline": True}),
                "example_3_input": ("STRING", {"default": "", "multiline": True}),
                "example_3_output": ("STRING", {"default": "", "multiline": True}),
                "instruction_prefix": ("STRING", {"default": "Here are examples of the desired format:"}),
            },
        }

    def build_examples(
        self,
        example_1_input: str,
        example_1_output: str,
        example_2_input: str = "",
        example_2_output: str = "",
        example_3_input: str = "",
        example_3_output: str = "",
        instruction_prefix: str = "Here are examples of the desired format:",
    ) -> tuple[str, str]:
        examples = []
        
        # Collect valid examples
        example_pairs = [
            (example_1_input, example_1_output),
            (example_2_input, example_2_output),
            (example_3_input, example_3_output),
        ]
        
        for idx, (inp, out) in enumerate(example_pairs, 1):
            inp_clean = inp.strip()
            out_clean = out.strip()
            if inp_clean and out_clean:
                examples.append(
                    f"<example>\n<input>\n{inp_clean}\n</input>\n<output>\n{out_clean}\n</output>\n</example>"
                )
        
        if not examples:
            info = self.build_info("Few-Shot Examples")
            info.add("No valid examples provided")
            return self.ensure_tuple("", info.render())
        
        # Build formatted section
        examples_section = f"{instruction_prefix}\n\n" + "\n\n".join(examples)
        
        info = self.build_info("Few-Shot Examples")
        info.add(f"Examples provided: {len(examples)}")
        info.add(f"Output length: {len(examples_section)} chars")
        info.add("Format: XML-tagged (Anthropic best practice)")
        
        return self.ensure_tuple(examples_section, info.render())


class XtremetoolsLMStudioStructuredOutput(_LMStudioPromptBase):
    """Add explicit output formatting instructions for structured responses."""

    RETURN_TYPES = ("STRING", "STRING")
    RETURN_NAMES = ("format_instruction", "info")
    FUNCTION = "build_format_instruction"

    @classmethod
    def INPUT_TYPES(cls) -> dict[str, Any]:
        return {
            "required": {
                "output_format": (["xml", "json", "markdown", "numbered_list", "bullet_points", "custom"],),
            },
            "optional": {
                "custom_format": ("STRING", {"default": "", "multiline": True}),
                "include_thinking": ("BOOLEAN", {"default": False}),
                "xml_tag_name": ("STRING", {"default": "answer"}),
            },
        }

    def build_format_instruction(
        self,
        output_format: str,
        custom_format: str = "",
        include_thinking: bool = False,
        xml_tag_name: str = "answer",
    ) -> tuple[str, str]:
        instructions = []
        
        # Add thinking instruction if requested (chain-of-thought)
        if include_thinking:
            instructions.append(
                "Before providing your final answer, show your reasoning step-by-step inside <thinking></thinking> tags."
            )
        
        # Add format-specific instructions
        format_templates = {
            "xml": f"Provide your final answer wrapped in <{xml_tag_name}></{xml_tag_name}> tags.",
            "json": "Provide your answer as a valid JSON object with clear key-value pairs.",
            "markdown": "Format your answer using Markdown with proper headings (##), lists, and code blocks where appropriate.",
            "numbered_list": "Provide your answer as a numbered list (1., 2., 3., etc.) with clear, distinct points.",
            "bullet_points": "Provide your answer as bullet points (- ) with concise information for each item.",
        }
        
        if output_format == "custom" and custom_format.strip():
            instructions.append(custom_format.strip())
        elif output_format in format_templates:
            instructions.append(format_templates[output_format])
        
        format_instruction = "\n\n".join(instructions) if instructions else ""
        
        info = self.build_info("Structured Output")
        info.add(f"Format: {output_format}")
        if include_thinking:
            info.add("Chain-of-thought: enabled")
        info.add(f"Instruction length: {len(format_instruction)} chars")
        
        return self.ensure_tuple(format_instruction, info.render())


NODE_CLASS_MAPPINGS = {
    "XtremetoolsLMStudioStylePreset": XtremetoolsLMStudioStylePreset,
    "XtremetoolsLMStudioPromptWeighter": XtremetoolsLMStudioPromptWeighter,
    "XtremetoolsLMStudioDualPrompt": XtremetoolsLMStudioDualPrompt,
    "XtremetoolsLMStudioQualityControl": XtremetoolsLMStudioQualityControl,
    "XtremetoolsLMStudioNegativePrompt": XtremetoolsLMStudioNegativePrompt,
    "XtremetoolsLMStudioFewShotExamples": XtremetoolsLMStudioFewShotExamples,
    "XtremetoolsLMStudioStructuredOutput": XtremetoolsLMStudioStructuredOutput,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XtremetoolsLMStudioStylePreset": "LM Studio Style Preset",
    "XtremetoolsLMStudioPromptWeighter": "LM Studio Prompt Weighter",
    "XtremetoolsLMStudioDualPrompt": "LM Studio Dual Prompt",
    "XtremetoolsLMStudioQualityControl": "LM Studio Quality Control",
    "XtremetoolsLMStudioNegativePrompt": "LM Studio Negative Prompt",
    "XtremetoolsLMStudioFewShotExamples": "LM Studio Few-Shot Examples",
    "XtremetoolsLMStudioStructuredOutput": "LM Studio Structured Output",
}
