"""Utility helpers for standardized info strings."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable


@dataclass
class InfoFormatter:
    """Collects text fragments and renders the info output ComfyUI expects."""

    title: str
    emoji: str = "🛠"
    parts: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        header = f"{self.emoji} {self.title}" if self.emoji else self.title
        self.parts.insert(0, header)

    def add(self, line: str) -> None:
        """Append a single line of text."""
        self.parts.append(line)

    def add_section(self, heading: str, lines: Iterable[str]) -> None:
        """Append a labeled section with multiple lines."""
        self.parts.append(f"\n{heading}")
        self.parts.extend(lines)

    def render(self) -> str:
        """Return the final newline-joined info block."""
        return "\n".join(self.parts)
