from random import Random

import pytest

from mazegen.exceptions import InvalidMazeError
from mazegen.grid import Grid, Position, Wall
from mazegen.modes.base import MazeMode
from mazegen.modes.playable import (
    PlayableMode,
    center_positions,
    corner_positions,
    count_playable_loops,
    find_dead_ends,
    has_playable_open_3x3_area,
    is_center_reachable,
    reachable_corners,
    reachable_playable_positions,
)


def test_playable_mode_connected_contract_accepts_connected_base() -> None:
    grid = _connected_tree_grid_3x3()

    result = PlayableMode().apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(2, 2),
    )

    assert result is grid


def test_playable_mode_connected_contract_satisfies_maze_mode() -> None:
    mode: MazeMode = PlayableMode()
    grid = _connected_tree_grid_3x3()

    assert mode.apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(2, 2),
    ) is grid


def test_playable_mode_connected_contract_keeps_base_reachable() -> None:
    grid = _connected_tree_grid_3x3()

    PlayableMode().apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(2, 2),
    )

    assert count_playable_loops(grid, set(grid.positions())) >= 2


def test_playable_mode_connected_contract_rejects_disconnected_cells() -> None:
    grid = Grid(2, 1)

    with pytest.raises(InvalidMazeError, match="reachable"):
        PlayableMode().apply(
            grid,
            Random(42),
            set(),
            Position(0, 0),
            Position(1, 0),
        )


def test_playable_mode_connected_contract_excludes_reserved_cells() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="reachable"):
        PlayableMode().apply(
            grid,
            Random(42),
            {Position(1, 0)},
            Position(0, 0),
            Position(2, 0),
        )


def test_playable_mode_connected_contract_accepts_reserved_closed_cell() -> None:
    grid = _connected_tree_grid_4x4_with_reserved_cell()

    result = PlayableMode().apply(
        grid,
        Random(42),
        {Position(1, 1)},
        Position(0, 0),
        Position(3, 3),
    )

    assert result is grid


def test_playable_mode_connected_contract_rejects_entry_in_reserved() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="reachable"):
        PlayableMode().apply(
            grid,
            Random(42),
            {Position(0, 0)},
            Position(0, 0),
            Position(1, 0),
        )


def test_playable_mode_connected_contract_rejects_exit_in_reserved() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="reachable"):
        PlayableMode().apply(
            grid,
            Random(42),
            {Position(1, 0)},
            Position(0, 0),
            Position(1, 0),
        )


def test_playable_mode_loops_creates_at_least_two_loops() -> None:
    grid = _connected_tree_grid_3x3()

    PlayableMode().apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(2, 2),
    )

    assert count_playable_loops(grid, set(grid.positions())) >= 2


def test_playable_mode_loops_are_deterministic_with_seed() -> None:
    first = _connected_tree_grid_3x3()
    second = _connected_tree_grid_3x3()

    PlayableMode().apply(
        first,
        Random(42),
        set(),
        Position(0, 0),
        Position(2, 2),
    )
    PlayableMode().apply(
        second,
        Random(42),
        set(),
        Position(0, 0),
        Position(2, 2),
    )

    assert _wall_signature(first) == _wall_signature(second)


def test_playable_mode_loops_do_not_open_walls_to_reserved_cells() -> None:
    grid = _connected_tree_grid_4x4_with_reserved_cell()

    PlayableMode().apply(
        grid,
        Random(42),
        {Position(1, 1)},
        Position(0, 0),
        Position(3, 3),
    )

    assert _open_edges_touching_reserved(grid, {Position(1, 1)}) == set()


def test_playable_mode_loops_rejects_when_two_loops_are_impossible() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    with pytest.raises(InvalidMazeError, match="two loops"):
        PlayableMode().apply(
            grid,
            Random(42),
            set(),
            Position(0, 0),
            Position(1, 0),
        )


def test_playable_mode_key_cells_accepts_reachable_corners_and_center() -> None:
    grid = _connected_tree_grid_3x3()

    PlayableMode().apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(2, 2),
    )
    reachable = reachable_playable_positions(grid, Position(0, 0), set())

    assert corner_positions(grid) <= reachable
    assert is_center_reachable(grid, reachable)


def test_playable_mode_key_cells_rejects_reserved_corner() -> None:
    grid = _connected_tree_grid_3x3()

    with pytest.raises(InvalidMazeError, match="corners"):
        PlayableMode().apply(
            grid,
            Random(42),
            {Position(0, 2)},
            Position(0, 0),
            Position(2, 2),
        )


def test_playable_mode_key_cells_rejects_unreachable_corner() -> None:
    grid = Grid(3, 3)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    grid.open_wall(Position(2, 0), Wall.SOUTH)
    grid.open_wall(Position(2, 1), Wall.SOUTH)

    with pytest.raises(InvalidMazeError, match="connected|corners"):
        PlayableMode().apply(
            grid,
            Random(42),
            set(),
            Position(0, 0),
            Position(2, 2),
        )


def test_playable_mode_key_cells_rejects_reserved_center() -> None:
    grid = _connected_tree_grid_3x3()

    with pytest.raises(InvalidMazeError, match="center"):
        PlayableMode().apply(
            grid,
            Random(42),
            {Position(1, 1)},
            Position(0, 0),
            Position(2, 2),
        )


def test_playable_mode_dead_ends_reduces_to_internal_threshold() -> None:
    grid = _connected_tree_grid_4x4_with_dead_ends()

    PlayableMode().apply(
        grid,
        Random(42),
        set(),
        Position(0, 0),
        Position(3, 3),
    )

    assert len(find_dead_ends(grid, set(grid.positions()))) <= 2


def test_playable_mode_dead_ends_deterministic_with_seed() -> None:
    first = _connected_tree_grid_4x4_with_dead_ends()
    second = _connected_tree_grid_4x4_with_dead_ends()

    PlayableMode().apply(
        first,
        Random(42),
        set(),
        Position(0, 0),
        Position(3, 3),
    )
    PlayableMode().apply(
        second,
        Random(42),
        set(),
        Position(0, 0),
        Position(3, 3),
    )

    assert _wall_signature(first) == _wall_signature(second)


def test_playable_mode_dead_ends_do_not_open_walls_to_reserved() -> None:
    grid = _connected_tree_grid_4x4_with_reserved_cell()
    reserved = {Position(1, 1)}

    PlayableMode().apply(
        grid,
        Random(42),
        reserved,
        Position(0, 0),
        Position(3, 3),
    )

    assert _open_edges_touching_reserved(grid, reserved) == set()


def test_corner_positions_handles_degenerate_grids() -> None:
    assert corner_positions(Grid(1, 1)) == {Position(0, 0)}
    assert corner_positions(Grid(1, 3)) == {
        Position(0, 0),
        Position(0, 2),
    }
    assert corner_positions(Grid(3, 1)) == {
        Position(0, 0),
        Position(2, 0),
    }


def test_center_positions_handles_even_dimensions() -> None:
    assert center_positions(Grid(4, 4)) == {
        Position(1, 1),
        Position(2, 1),
        Position(1, 2),
        Position(2, 2),
    }
    assert center_positions(Grid(3, 3)) == {Position(1, 1)}


def test_reachable_playable_positions_excludes_reserved_cells() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    reachable = reachable_playable_positions(
        grid,
        Position(0, 0),
        {Position(1, 0)},
    )

    assert reachable == {Position(0, 0)}


def test_find_dead_ends_detects_known_dead_ends() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert find_dead_ends(grid, set(grid.positions())) == {
        Position(0, 0),
        Position(2, 0),
    }


def test_count_playable_loops_detects_known_loop() -> None:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    grid.open_wall(Position(1, 1), Wall.WEST)
    grid.open_wall(Position(0, 1), Wall.NORTH)

    assert count_playable_loops(grid, set(grid.positions())) == 1


def test_count_playable_loops_does_not_traverse_non_playable_bridge() -> None:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)

    assert count_playable_loops(
        grid,
        {Position(0, 0), Position(2, 0)},
    ) == 0


def test_count_playable_loops_returns_zero_for_disconnected_tree_components() -> None:
    grid = Grid(4, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(2, 0), Wall.EAST)

    assert count_playable_loops(grid, set(grid.positions())) == 0


def test_count_playable_loops_ignores_out_of_bounds_positions() -> None:
    grid = Grid(1, 1)

    assert count_playable_loops(
        grid,
        {Position(0, 0), Position(99, 99)},
    ) == 0


def test_reachable_corners_returns_only_reached_corners() -> None:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    reachable = reachable_playable_positions(grid, Position(0, 0), set())

    assert reachable_corners(grid, reachable) == {
        Position(0, 0),
        Position(1, 0),
        Position(1, 1),
    }


def test_is_center_reachable_for_odd_grid() -> None:
    grid = Grid(3, 3)

    assert is_center_reachable(grid, {Position(1, 1)})
    assert not is_center_reachable(grid, {Position(0, 0)})


def test_is_center_reachable_for_even_grid() -> None:
    grid = Grid(4, 4)

    assert is_center_reachable(grid, {Position(1, 1)})
    assert is_center_reachable(grid, {Position(2, 1)})
    assert is_center_reachable(grid, {Position(1, 2)})
    assert is_center_reachable(grid, {Position(2, 2)})
    assert not is_center_reachable(grid, {Position(0, 0)})


def test_has_playable_open_three_by_three_area_detects_invalid_area() -> None:
    grid = Grid(3, 3)
    _open_full_three_by_three(grid)

    assert has_playable_open_3x3_area(grid, set(grid.positions()))


def test_reserved_cell_prevents_playable_three_by_three_detection() -> None:
    grid = Grid(3, 3)
    _open_full_three_by_three(grid)
    playable = set(grid.positions()) - {Position(1, 1)}

    assert not has_playable_open_3x3_area(grid, playable)


def test_dead_end_detection_ignores_open_wall_to_reserved_cell() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    assert find_dead_ends(grid, {Position(0, 0)}) == set()


def _open_full_three_by_three(grid: Grid) -> None:
    for y in range(3):
        for x in range(2):
            grid.open_wall(Position(x, y), Wall.EAST)
    for y in range(2):
        for x in range(3):
            grid.open_wall(Position(x, y), Wall.SOUTH)


def _wall_signature(grid: Grid) -> tuple[tuple[int, ...], ...]:
    return tuple(
        tuple(int(grid.cell_at(Position(x, y)).walls) for x in range(grid.width))
        for y in range(grid.height)
    )


def _connected_tree_grid_3x3() -> Grid:
    grid = Grid(3, 3)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    grid.open_wall(Position(2, 0), Wall.SOUTH)
    grid.open_wall(Position(2, 1), Wall.SOUTH)
    grid.open_wall(Position(2, 2), Wall.WEST)
    grid.open_wall(Position(1, 2), Wall.WEST)
    grid.open_wall(Position(0, 2), Wall.NORTH)
    grid.open_wall(Position(0, 1), Wall.EAST)
    return grid


def _open_perimeter_tree_around_center(grid: Grid) -> None:
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    grid.open_wall(Position(2, 0), Wall.SOUTH)
    grid.open_wall(Position(2, 1), Wall.SOUTH)
    grid.open_wall(Position(2, 2), Wall.WEST)
    grid.open_wall(Position(1, 2), Wall.WEST)
    grid.open_wall(Position(0, 2), Wall.NORTH)


def _connected_tree_grid_4x4_with_reserved_cell() -> Grid:
    grid = Grid(4, 4)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    grid.open_wall(Position(2, 0), Wall.EAST)
    grid.open_wall(Position(3, 0), Wall.SOUTH)
    grid.open_wall(Position(3, 1), Wall.SOUTH)
    grid.open_wall(Position(3, 2), Wall.SOUTH)
    grid.open_wall(Position(3, 3), Wall.WEST)
    grid.open_wall(Position(2, 3), Wall.WEST)
    grid.open_wall(Position(1, 3), Wall.WEST)
    grid.open_wall(Position(0, 3), Wall.NORTH)
    grid.open_wall(Position(0, 2), Wall.NORTH)
    grid.open_wall(Position(2, 1), Wall.SOUTH)
    grid.open_wall(Position(2, 2), Wall.WEST)
    grid.open_wall(Position(1, 2), Wall.WEST)
    return grid


def _connected_tree_grid_4x4_with_dead_ends() -> Grid:
    grid = Grid(4, 4)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    grid.open_wall(Position(2, 0), Wall.EAST)
    grid.open_wall(Position(3, 0), Wall.SOUTH)
    grid.open_wall(Position(3, 1), Wall.SOUTH)
    grid.open_wall(Position(3, 2), Wall.SOUTH)
    grid.open_wall(Position(3, 3), Wall.WEST)
    grid.open_wall(Position(2, 3), Wall.WEST)
    grid.open_wall(Position(1, 3), Wall.WEST)
    grid.open_wall(Position(0, 3), Wall.NORTH)
    grid.open_wall(Position(0, 2), Wall.NORTH)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    grid.open_wall(Position(2, 0), Wall.SOUTH)
    grid.open_wall(Position(1, 3), Wall.NORTH)
    grid.open_wall(Position(2, 3), Wall.NORTH)
    return grid


def _open_edges_touching_reserved(
    grid: Grid,
    reserved: set[Position],
) -> set[tuple[Position, Position]]:
    edges = set()
    for position in reserved:
        for neighbor, wall in grid.neighbors(position):
            if not grid.cell_at(position).has_wall(wall):
                edges.add((position, neighbor))
    return edges
