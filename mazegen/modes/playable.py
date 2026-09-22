"""Validation helpers for playable maze mode."""

from random import Random

from mazegen.exceptions import InvalidMazeError
from mazegen.grid import Grid, Position, Wall


class PlayableMode:
    """Validate the connected base required by playable maze mode."""

    def apply(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
        entry: Position,
        exit: Position,
    ) -> Grid:
        """Return grid if playable cells are connected and endpoints reachable."""
        _ = rng
        if not grid.in_bounds(entry) or not grid.in_bounds(exit):
            raise InvalidMazeError("entry and exit must be reachable")
        if entry in reserved or exit in reserved:
            raise InvalidMazeError("entry and exit must be reachable")

        reachable = reachable_playable_positions(grid, entry, reserved)
        if exit not in reachable:
            raise InvalidMazeError("entry and exit must be reachable")
        if playable_positions(grid, reserved) - reachable:
            raise InvalidMazeError("playable maze cells must be connected")
        return grid


def playable_positions(grid: Grid, reserved: set[Position]) -> set[Position]:
    """Return grid positions that are not reserved."""
    return set(grid.positions()) - reserved


def reachable_playable_positions(
    grid: Grid,
    start: Position,
    reserved: set[Position],
) -> set[Position]:
    """Return positions reachable from start without crossing reserved cells."""
    if not grid.in_bounds(start) or start in reserved:
        return set()

    playable = playable_positions(grid, reserved)
    pending = [start]
    visited = {start}
    while pending:
        position = pending.pop()
        for neighbor, wall in _open_playable_neighbors(grid, position, playable):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            pending.append(neighbor)
    return visited


def count_playable_loops(
    grid: Grid,
    playable_positions: set[Position],
) -> int:
    """Count independent loops inside playable positions."""
    valid_positions = _in_bounds_playable_positions(grid, playable_positions)
    if not valid_positions:
        return 0
    return (
        _count_open_playable_edges(grid, valid_positions)
        - len(valid_positions)
        + _count_playable_components(grid, valid_positions)
    )


def find_dead_ends(
    grid: Grid,
    playable_positions: set[Position],
) -> set[Position]:
    """Return playable positions with one open playable edge."""
    return {
        position
        for position in playable_positions
        if _open_playable_degree(grid, position, playable_positions) == 1
    }


def reachable_corners(
    grid: Grid,
    reachable: set[Position],
) -> set[Position]:
    """Return grid corners included in the reachable positions."""
    corners = {
        Position(0, 0),
        Position(grid.width - 1, 0),
        Position(0, grid.height - 1),
        Position(grid.width - 1, grid.height - 1),
    }
    return corners & reachable


def is_center_reachable(
    grid: Grid,
    reachable: set[Position],
) -> bool:
    """Return whether any geometric center cell is reachable.

    Even dimensions have two central coordinates for that axis, so any cell in
    the central 2x1, 1x2, or 2x2 area counts as a reachable center.
    """
    return bool(_center_positions(grid) & reachable)


def has_playable_open_3x3_area(
    grid: Grid,
    playable_positions: set[Position],
) -> bool:
    """Return whether a playable 3x3 block has every internal wall open."""
    if grid.width < 3 or grid.height < 3:
        return False

    return any(
        _is_playable_open_3x3_block(grid, Position(x, y), playable_positions)
        for y in range(grid.height - 2)
        for x in range(grid.width - 2)
    )


def _open_playable_neighbors(
    grid: Grid,
    position: Position,
    playable_positions: set[Position],
) -> tuple[tuple[Position, Wall], ...]:
    return tuple(
        (neighbor, wall)
        for neighbor, wall in grid.neighbors(position)
        if neighbor in playable_positions
        and not grid.cell_at(position).has_wall(wall)
    )


def _open_playable_degree(
    grid: Grid,
    position: Position,
    playable_positions: set[Position],
) -> int:
    if position not in playable_positions or not grid.in_bounds(position):
        return 0
    return len(_open_playable_neighbors(grid, position, playable_positions))


def _in_bounds_playable_positions(
    grid: Grid,
    playable_positions: set[Position],
) -> set[Position]:
    return {position for position in playable_positions if grid.in_bounds(position)}


def _count_open_playable_edges(
    grid: Grid,
    playable_positions: set[Position],
) -> int:
    edges = 0
    for position in playable_positions:
        edges += len(_open_playable_neighbors(grid, position, playable_positions))
    return edges // 2


def _count_playable_components(
    grid: Grid,
    playable_positions: set[Position],
) -> int:
    remaining = set(playable_positions)
    components = 0
    while remaining:
        start = next(iter(remaining))
        remaining -= _reachable_within_playable(grid, start, playable_positions)
        components += 1
    return components


def _reachable_within_playable(
    grid: Grid,
    start: Position,
    playable_positions: set[Position],
) -> set[Position]:
    pending = [start]
    visited = {start}
    while pending:
        position = pending.pop()
        for neighbor, wall in _open_playable_neighbors(
            grid,
            position,
            playable_positions,
        ):
            if neighbor in visited:
                continue
            visited.add(neighbor)
            pending.append(neighbor)
    return visited


def _center_positions(grid: Grid) -> set[Position]:
    return {
        Position(x, y)
        for x in _center_axis_positions(grid.width)
        for y in _center_axis_positions(grid.height)
    }


def _center_axis_positions(size: int) -> set[int]:
    if size % 2 == 1:
        return {size // 2}
    return {size // 2 - 1, size // 2}


def _is_playable_open_3x3_block(
    grid: Grid,
    top_left: Position,
    playable_positions: set[Position],
) -> bool:
    block_positions = {
        Position(top_left.x + offset_x, top_left.y + offset_y)
        for offset_y in range(3)
        for offset_x in range(3)
    }
    if not block_positions <= playable_positions:
        return False

    for offset_y in range(3):
        for offset_x in range(3):
            position = Position(top_left.x + offset_x, top_left.y + offset_y)
            if offset_x < 2 and grid.cell_at(position).has_wall(Wall.EAST):
                return False
            if offset_y < 2 and grid.cell_at(position).has_wall(Wall.SOUTH):
                return False
    return True
