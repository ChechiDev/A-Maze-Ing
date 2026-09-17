from random import Random

from mazegen.grid import ALL_WALLS, Grid, Position, Wall
from mazegen.strategies.backtracker import RecursiveBacktrackerStrategy
from mazegen.strategies.base import GenerationStrategy
from mazegen.validation import (
    count_loops,
    count_open_edges,
    has_wall_coherence,
    is_connected,
)


def test_recursive_backtracker_satisfies_generation_strategy_contract() -> None:
    strategy: GenerationStrategy = RecursiveBacktrackerStrategy()

    assert isinstance(strategy, RecursiveBacktrackerStrategy)


def test_recursive_backtracker_generates_perfect_two_by_two_grid() -> None:
    grid = Grid(2, 2)
    positions = set(grid.positions())

    RecursiveBacktrackerStrategy().generate(grid, Random(42), set())

    assert is_connected(grid, positions)
    assert count_open_edges(grid, positions) == len(positions) - 1
    assert count_loops(grid, positions) == 0
    assert has_wall_coherence(grid)


def test_recursive_backtracker_generates_perfect_five_by_five_grid() -> None:
    grid = Grid(5, 5)
    positions = set(grid.positions())

    RecursiveBacktrackerStrategy().generate(grid, Random(42), set())

    assert is_connected(grid, positions)
    assert count_open_edges(grid, positions) == len(positions) - 1
    assert count_loops(grid, positions) == 0
    assert has_wall_coherence(grid)


def test_recursive_backtracker_is_deterministic_for_same_seed() -> None:
    first = Grid(5, 5)
    second = Grid(5, 5)
    strategy = RecursiveBacktrackerStrategy()

    strategy.generate(first, Random(42), set())
    strategy.generate(second, Random(42), set())

    assert _wall_signature(first) == _wall_signature(second)


def test_recursive_backtracker_keeps_reserved_cell_closed() -> None:
    grid = Grid(3, 3)
    reserved = {Position(1, 1)}
    transitables = _transitable_positions(grid, reserved)

    RecursiveBacktrackerStrategy().generate(grid, Random(42), reserved)

    _assert_all_walls_closed_for_position(grid, Position(1, 1))
    assert is_connected(grid, transitables)
    assert count_open_edges(grid, transitables) == len(transitables) - 1
    assert count_loops(grid, transitables) == 0
    assert has_wall_coherence(grid)


def test_recursive_backtracker_returns_unchanged_grid_when_all_reserved() -> None:
    grid = Grid(2, 2)
    reserved = set(grid.positions())

    result = RecursiveBacktrackerStrategy().generate(grid, Random(42), reserved)

    assert result is grid
    assert _wall_signature(grid) == (int(ALL_WALLS),) * 4
    assert count_open_edges(grid, set()) == 0


def test_recursive_backtracker_keeps_single_transitable_cell_closed() -> None:
    grid = Grid(2, 1)
    reserved = {Position(1, 0)}

    RecursiveBacktrackerStrategy().generate(grid, Random(42), reserved)

    _assert_all_walls_closed_for_position(grid, Position(0, 0))
    _assert_all_walls_closed_for_position(grid, Position(1, 0))


def _wall_signature(grid: Grid) -> tuple[int, ...]:
    return tuple(int(grid.cell_at(position).walls) for position in grid.positions())


def _transitable_positions(grid: Grid, reserved: set[Position]) -> set[Position]:
    return {position for position in grid.positions() if position not in reserved}


def _assert_all_walls_closed_for_position(
    grid: Grid,
    position: Position,
) -> None:
    for wall in (Wall.NORTH, Wall.EAST, Wall.SOUTH, Wall.WEST):
        assert grid.cell_at(position).has_wall(wall)
