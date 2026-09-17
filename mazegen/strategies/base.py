"""Contracts for maze generation strategies."""

from random import Random
from typing import Protocol

from mazegen.grid import Grid, Position


class GenerationStrategy(Protocol):
    """Protocol implemented by maze generation strategies.

    A strategy receives a mutable ``Grid`` and may modify it in-place using
    grid APIs such as ``Grid.open_wall``. It must return the resulting grid.
    The ``reserved`` set contains positions that the strategy should avoid
    opening or modifying when the concrete algorithm supports reservations.
    """

    def generate(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
    ) -> Grid:
        """Generate maze passages and return the resulting grid."""
