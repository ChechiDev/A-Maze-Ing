"""Reusable public API for maze generation."""

from mazegen.exceptions import (
    InvalidConfigurationError,
    InvalidMazeError,
    MazeError,
    UnreachableExitError,
)
from mazegen.generator import MazeGenerator, MazeOptions, MazeResult
from mazegen.grid import Grid, Position, Wall

__all__ = [
    "Grid",
    "InvalidConfigurationError",
    "InvalidMazeError",
    "MazeError",
    "MazeGenerator",
    "MazeOptions",
    "MazeResult",
    "Position",
    "UnreachableExitError",
    "Wall",
]
