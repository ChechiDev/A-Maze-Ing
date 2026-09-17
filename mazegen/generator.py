"""Public generation data transfer objects for maze generation."""

from dataclasses import dataclass
from random import Random

from mazegen.grid import Grid, Position
from mazegen.solver import ShortestPathSolver
from mazegen.strategies.backtracker import RecursiveBacktrackerStrategy
from mazegen.strategies.base import GenerationStrategy


@dataclass(frozen=True, slots=True)
class MazeOptions:
    """Options required to generate a maze through the reusable API."""

    width: int
    height: int
    entry: Position
    exit: Position
    perfect: bool
    seed: int | None = None

    def __post_init__(self) -> None:
        """Validate options that protect the reusable core API."""
        if self.width <= 0:
            raise ValueError("width must be positive")
        if self.height <= 0:
            raise ValueError("height must be positive")
        if not _is_in_bounds(self.width, self.height, self.entry):
            raise ValueError("entry must be inside the maze bounds")
        if not _is_in_bounds(self.width, self.height, self.exit):
            raise ValueError("exit must be inside the maze bounds")
        if self.entry == self.exit:
            raise ValueError("entry and exit must be different")


@dataclass(frozen=True, slots=True)
class MazeResult:
    """Generated maze data returned by the reusable API."""

    grid: Grid
    entry: Position
    exit: Position
    shortest_path: str
    warning: str | None = None


class MazeGenerator:
    """Reusable maze generation API."""

    def __init__(
        self,
        strategy: GenerationStrategy | None = None,
        solver: ShortestPathSolver | None = None,
    ) -> None:
        """Create a generator with injectable strategy and solver defaults."""
        self._strategy = strategy or RecursiveBacktrackerStrategy()
        self._solver = solver or ShortestPathSolver()

    def generate(self, options: MazeOptions) -> MazeResult:
        """Generate a maze result without performing any UI or file I/O."""
        rng = Random(options.seed)
        grid = Grid(options.width, options.height)
        reserved: set[Position] = set()
        self._strategy.generate(grid, rng, reserved)
        shortest_path = self._solver.solve(grid, options.entry, options.exit)
        return MazeResult(
            grid=grid,
            entry=options.entry,
            exit=options.exit,
            shortest_path=shortest_path,
        )


def _is_in_bounds(width: int, height: int, position: Position) -> bool:
    return 0 <= position.x < width and 0 <= position.y < height
