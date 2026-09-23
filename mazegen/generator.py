"""Public generation data transfer objects for maze generation."""

from dataclasses import dataclass
from random import Random

from mazegen.exceptions import InvalidConfigurationError
from mazegen.grid import Grid, Position
from mazegen.modes.base import MazeMode
from mazegen.modes.perfect import PerfectMode
from mazegen.modes.playable import PlayableMode
from mazegen.pattern42 import build_pattern42_positions, pattern42_overlaps
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
        perfect_mode: MazeMode | None = None,
        playable_mode: MazeMode | None = None,
    ) -> None:
        """Create a generator with injectable strategy and solver defaults."""
        self._strategy = strategy or RecursiveBacktrackerStrategy()
        self._solver = solver or ShortestPathSolver()
        self._perfect_mode = perfect_mode or PerfectMode()
        self._playable_mode = playable_mode or PlayableMode()

    def generate(self, options: MazeOptions) -> MazeResult:
        """Generate a maze result without performing any UI or file I/O."""
        rng = Random(options.seed)
        grid = Grid(options.width, options.height)
        pattern = build_pattern42_positions(options.width, options.height)
        if pattern42_overlaps(pattern.positions, options.entry, options.exit):
            raise InvalidConfigurationError(
                "entry or exit overlaps pattern 42"
            )
        reserved = set(pattern.positions)
        self._strategy.generate(grid, rng, reserved)
        mode = self._perfect_mode if options.perfect else self._playable_mode
        grid = mode.apply(grid, rng, reserved, options.entry, options.exit)
        shortest_path = self._solver.solve(grid, options.entry, options.exit)
        return MazeResult(
            grid=grid,
            entry=options.entry,
            exit=options.exit,
            shortest_path=shortest_path,
            warning=pattern.warning,
        )


def _is_in_bounds(width: int, height: int, position: Position) -> bool:
    return 0 <= position.x < width and 0 <= position.y < height
