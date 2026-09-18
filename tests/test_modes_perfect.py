from random import Random

import pytest

from mazegen.exceptions import InvalidMazeError
from mazegen.grid import Grid, Position, Wall
from mazegen.modes.base import MazeMode
from mazegen.modes.perfect import PerfectMode


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


def test_perfect_mode_satisfies_maze_mode_contract() -> None:
    mode: MazeMode = PerfectMode()
    grid = _perfect_two_by_two_grid()

    assert mode.apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(0, 1),
    ) is grid


def test_perfect_mode_accepts_valid_perfect_grid() -> None:
    grid = _perfect_two_by_two_grid()

    result = PerfectMode().apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(0, 1),
    )

    assert result is grid


def test_perfect_mode_does_not_modify_grid() -> None:
    grid = _perfect_two_by_two_grid()
    before = _wall_signature(grid)

    PerfectMode().apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(0, 1),
    )

    assert _wall_signature(grid) == before


def test_perfect_mode_rejects_disconnected_playable_cells() -> None:
    grid = Grid(2, 1)

    with pytest.raises(InvalidMazeError, match="connected"):
        PerfectMode().apply(
            grid,
            Random(42),
            set(),
            Position(0, 0),
            Position(1, 0),
        )


def test_perfect_mode_rejects_loops() -> None:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    grid.open_wall(Position(1, 1), Wall.WEST)
    grid.open_wall(Position(0, 1), Wall.NORTH)

    with pytest.raises(InvalidMazeError, match="loops"):
        PerfectMode().apply(
            grid,
            Random(42),
            set(),
            Position(0, 0),
            Position(0, 1),
        )


def test_perfect_mode_rejects_unreachable_exit() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="connected"):
        PerfectMode().apply(
            grid,
            Random(42),
            set(),
            Position(0, 0),
            Position(2, 0),
        )


def test_perfect_mode_rejects_open_three_by_three_area() -> None:
    grid = Grid(3, 3)
    _open_full_three_by_three(grid)

    with pytest.raises(InvalidMazeError, match="3x3"):
        PerfectMode().apply(
            grid,
            Random(42),
            set(),
            Position(0, 0),
            Position(2, 2),
        )


def test_perfect_mode_excludes_reserved_cells() -> None:
    grid = Grid(3, 3)
    _open_perimeter_tree_around_center(grid)

    result = PerfectMode().apply(
        grid,
        Random(42),
        {Position(1, 1)},
        Position(0, 0),
        Position(0, 1),
    )

    assert result is grid


def test_perfect_mode_does_not_connect_through_reserved_cells() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="connected"):
        PerfectMode().apply(
            grid,
            Random(42),
            {Position(1, 0)},
            Position(0, 0),
            Position(2, 0),
        )


def test_perfect_mode_rejects_entry_in_reserved_cells() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="reachable"):
        PerfectMode().apply(
            grid,
            Random(42),
            {Position(0, 0)},
            Position(0, 0),
            Position(1, 0),
        )


def test_perfect_mode_rejects_exit_in_reserved_cells() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="reachable"):
        PerfectMode().apply(
            grid,
            Random(42),
            {Position(1, 0)},
            Position(0, 0),
            Position(1, 0),
        )


def _perfect_two_by_two_grid() -> Grid:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    grid.open_wall(Position(1, 1), Wall.WEST)
    return grid


def _wall_signature(grid: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(int(grid.cell_at(Position(x, y)).walls) for x in range(grid.width))
        for y in range(grid.height)
    )


def _open_perimeter_tree_around_center(grid: Grid) -> None:
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    grid.open_wall(Position(2, 0), Wall.SOUTH)
    grid.open_wall(Position(2, 1), Wall.SOUTH)
    grid.open_wall(Position(2, 2), Wall.WEST)
    grid.open_wall(Position(1, 2), Wall.WEST)
    grid.open_wall(Position(0, 2), Wall.NORTH)


def _open_full_three_by_three(grid: Grid) -> None:
    for y in range(3):
        for x in range(2):
            grid.open_wall(Position(x, y), Wall.EAST)
    for y in range(2):
        for x in range(3):
            grid.open_wall(Position(x, y), Wall.SOUTH)
