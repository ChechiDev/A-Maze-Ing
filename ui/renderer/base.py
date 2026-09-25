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


@dataclass(frozen=True, slots=True)
class LineRenderPalette:
    """Symbols used by line-art terminal renderers."""

    horizontal: str = "─"
    vertical: str = "│"
    top_left: str = "┌"
    top_right: str = "┐"
    bottom_left: str = "└"
    bottom_right: str = "┘"
    junction: str = "┼"
    tee_up: str = "┴"
    tee_down: str = "┬"
    tee_left: str = "┤"
    tee_right: str = "├"
    cross: str = "┼"
    entry: str = "E"
    exit: str = "S"
    path: str = "·"
    pattern: str = "4"
    empty: str = " "


class Renderer(Protocol):
    """Protocol implemented by UI renderers."""

    def render(self, result: MazeResult, show_path: bool) -> str:
        """Return a text representation for a generated maze result."""
        ...
