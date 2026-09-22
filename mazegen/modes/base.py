"""Contracts for post-generation maze modes."""

from random import Random
from typing import Protocol

from mazegen.grid import Grid, Position


class MazeMode(Protocol):
    """Protocol implemented by maze mode policies.

    A mode receives a generated or partially generated ``Grid`` and may use
    grid APIs to open or close walls according to concrete mode rules. It must
    respect ``reserved`` cells, preserve or guarantee entry/exit reachability,
    and return the resulting grid. Mode implementations must not perform UI,
    file I/O, logging, or configuration parsing.
    """

    def apply(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
        entry: Position,
        exit: Position,
    ) -> Grid:
        """Apply mode rules and return the resulting grid."""
