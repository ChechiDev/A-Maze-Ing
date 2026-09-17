from mazegen.grid import Grid, Position, Wall
from mazegen.validation import (
    count_loops,
    count_open_edges,
    has_open_3x3_area,
    has_wall_coherence,
    is_connected,
    reachable_positions,
)


def test_reachable_positions_returns_connected_region() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    assert reachable_positions(grid, Position(0, 0)) == {
        Position(0, 0),
        Position(1, 0),
    }


def test_reachable_positions_returns_empty_set_for_out_of_bounds_start() -> None:
    grid = Grid(1, 1)

    assert reachable_positions(grid, Position(1, 0)) == set()


def test_is_connected_returns_true_for_connected_positions() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert is_connected(grid, set(grid.positions()))


def test_is_connected_returns_false_for_disconnected_positions() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    assert not is_connected(grid, set(grid.positions()))


def test_is_connected_returns_true_for_empty_positions() -> None:
    assert is_connected(Grid(1, 1), set())


def test_count_open_edges_counts_undirected_edges_once() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert count_open_edges(grid, set(grid.positions())) == 2


def test_count_open_edges_ignores_edges_outside_subset() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert count_open_edges(grid, {Position(0, 0), Position(1, 0)}) == 1


def test_count_loops_returns_zero_for_tree() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert count_loops(grid, set(grid.positions())) == 0


def test_count_loops_counts_known_two_by_two_cycle() -> None:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    grid.open_wall(Position(1, 1), Wall.WEST)
    grid.open_wall(Position(0, 1), Wall.NORTH)

    assert count_loops(grid, set(grid.positions())) == 1


def test_count_loops_returns_zero_for_empty_positions() -> None:
    assert count_loops(Grid(1, 1), set()) == 0


def test_has_wall_coherence_returns_true_for_grid_opened_through_api() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    assert has_wall_coherence(grid)


def test_has_wall_coherence_detects_forced_incoherence() -> None:
    grid = Grid(2, 1)
    grid._mutable_cell_at(Position(0, 0)).open_wall(Wall.EAST)

    assert not has_wall_coherence(grid)


def test_has_open_3x3_area_returns_false_for_smaller_grid() -> None:
    assert not has_open_3x3_area(Grid(2, 2))


def test_has_open_3x3_area_detects_fully_open_internal_block() -> None:
    grid = Grid(3, 3)
    _open_3x3_internal_walls(grid)

    assert has_open_3x3_area(grid)


def test_has_open_3x3_area_returns_false_if_internal_wall_is_closed() -> None:
    grid = Grid(3, 3)
    _open_3x3_internal_walls(grid)
    grid._mutable_cell_at(Position(1, 1)).close_wall(Wall.EAST)
    grid._mutable_cell_at(Position(2, 1)).close_wall(Wall.WEST)

    assert not has_open_3x3_area(grid)


def test_has_open_3x3_area_detects_any_matching_block() -> None:
    grid = Grid(4, 4)
    for y in range(1, 4):
        for x in range(1, 3):
            grid.open_wall(Position(x, y), Wall.EAST)
    for y in range(1, 3):
        for x in range(1, 4):
            grid.open_wall(Position(x, y), Wall.SOUTH)

    assert has_open_3x3_area(grid)


def _open_3x3_internal_walls(grid: Grid) -> None:
    for y in range(3):
        for x in range(2):
            grid.open_wall(Position(x, y), Wall.EAST)
    for y in range(2):
        for x in range(3):
            grid.open_wall(Position(x, y), Wall.SOUTH)
