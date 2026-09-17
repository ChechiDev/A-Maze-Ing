"""Public generation data transfer objects for maze generation."""

from dataclasses import dataclass

from mazegen.grid import Grid, Position


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


def _is_in_bounds(width: int, height: int, position: Position) -> bool:
    return 0 <= position.x < width and 0 <= position.y < height
