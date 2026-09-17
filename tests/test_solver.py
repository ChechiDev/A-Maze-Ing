import pytest

from mazegen.exceptions import UnreachableExitError
from mazegen.grid import Grid, Position, Wall
from mazegen.solver import ShortestPathSolver


def test_solver_returns_horizontal_path() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert _solve(grid, Position(0, 0), Position(2, 0)) == "EE"


def test_solver_returns_vertical_path() -> None:
    grid = Grid(1, 3)
    grid.open_wall(Position(0, 0), Wall.SOUTH)
    grid.open_wall(Position(0, 1), Wall.SOUTH)

    assert _solve(grid, Position(0, 0), Position(0, 2)) == "SS"


def test_solver_returns_turning_path() -> None:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)

    assert _solve(grid, Position(0, 0), Position(1, 1)) == "ES"


def test_solver_returns_reverse_path() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert _solve(grid, Position(2, 0), Position(0, 0)) == "WW"


def test_solver_returns_shortest_path() -> None:
    grid = Grid(3, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    grid.open_wall(Position(0, 0), Wall.SOUTH)
    grid.open_wall(Position(0, 1), Wall.EAST)
    grid.open_wall(Position(1, 1), Wall.EAST)
    grid.open_wall(Position(2, 1), Wall.NORTH)

    assert _solve(grid, Position(0, 0), Position(2, 0)) == "EE"


def test_solver_raises_when_exit_is_unreachable() -> None:
    grid = Grid(2, 1)

    with pytest.raises(UnreachableExitError, match="exit is not reachable"):
        _solve(grid, Position(0, 0), Position(1, 0))


def test_solver_raises_when_start_is_outside_grid() -> None:
    grid = Grid(1, 1)

    with pytest.raises(ValueError, match="start position is outside the grid"):
        _solve(grid, Position(-1, 0), Position(0, 0))


def test_solver_raises_when_end_is_outside_grid() -> None:
    grid = Grid(1, 1)

    with pytest.raises(ValueError, match="end position is outside the grid"):
        _solve(grid, Position(0, 0), Position(1, 0))


def test_solver_returns_empty_path_when_start_equals_end() -> None:
    grid = Grid(1, 1)

    assert _solve(grid, Position(0, 0), Position(0, 0)) == ""


def _solve(grid: Grid, start: Position, end: Position) -> str:
    return ShortestPathSolver().solve(grid, start, end)
