from random import Random

from mazegen.grid import Grid, Position
from mazegen.modes.base import MazeMode


class FakeMode:
    """Minimal mode used to verify the MazeMode contract."""

    def __init__(self) -> None:
        self.received_reserved: set[Position] | None = None

    def apply(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
        entry: Position,
        exit: Position,
    ) -> Grid:
        assert isinstance(reserved, set)
        assert entry in set(grid.positions())
        assert exit in set(grid.positions())
        _ = rng.random()
        self.received_reserved = reserved
        return grid


def test_fake_mode_satisfies_maze_mode_contract() -> None:
    mode: MazeMode = FakeMode()
    grid = Grid(2, 2)

    result = mode.apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(1, 1),
    )

    assert result is grid


def test_fake_mode_receives_reserved_positions() -> None:
    mode = FakeMode()
    grid = Grid(2, 2)
    reserved = {Position(0, 1)}

    mode.apply(
        grid,
        Random(42),
        reserved,
        Position(0, 0),
        Position(1, 1),
    )

    assert mode.received_reserved == reserved
