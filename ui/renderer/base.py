"""Contracts shared by maze renderers."""

from dataclasses import dataclass
from typing import Protocol

from mazegen.generator import MazeResult


@dataclass(frozen=True, slots=True)
class RenderPalette:
    """Symbols used by text-based renderers."""

    wall: str = "#"
    path: str = "."
    entry: str = "E"
    exit: str = "S"
    pattern: str = "4"
    empty: str = " "


class Renderer(Protocol):
    """Protocol implemented by UI renderers."""

    def render(self, result: MazeResult, show_path: bool) -> str:
        """Return a text representation for a generated maze result."""
        ...
