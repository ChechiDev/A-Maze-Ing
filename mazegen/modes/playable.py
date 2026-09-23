"""Validation helpers for playable maze mode."""

from random import Random

from mazegen.exceptions import InvalidMazeError
from mazegen.grid import Grid, Position, Wall


MAX_REAL_DEAD_ENDS = 2


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
        _ensure_key_cells_available(grid, reserved)

        reachable = reachable_playable_positions(grid, entry, reserved)
        if exit not in reachable:
            raise InvalidMazeError("entry and exit must be reachable")
        if playable_positions(grid, reserved) - reachable:
            raise InvalidMazeError("playable maze cells must be connected")
        _ensure_minimum_loops(
            grid,
            rng,
            playable_positions(grid, reserved),
            2,
        )
        _reduce_dead_ends(
            grid,
            rng,
            playable_positions(grid, reserved),
            MAX_REAL_DEAD_ENDS,
        )
        _ensure_key_cells_reachable(
            grid,
            reserved,
            reachable_playable_positions(grid, entry, reserved),
        )
        if has_playable_open_3x3_area(grid, playable_positions(grid, reserved)):
            raise InvalidMazeError(
                "playable maze must not contain open 3x3 areas"
            )
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
    return corner_positions(grid) & reachable


def corner_positions(grid: Grid) -> set[Position]:
    """Return all unique corner positions for the grid."""
    return {
        Position(0, 0),
        Position(grid.width - 1, 0),
        Position(0, grid.height - 1),
        Position(grid.width - 1, grid.height - 1),
    }


def is_center_reachable(
    grid: Grid,
    reachable: set[Position],
) -> bool:
    """Return whether any geometric center cell is reachable.

    Even dimensions have two central coordinates for that axis, so any cell in
    the central 2x1, 1x2, or 2x2 area counts as a reachable center.
    """
    return bool(center_positions(grid) & reachable)


def center_positions(grid: Grid) -> set[Position]:
    """Return all geometric center candidate positions for the grid."""
    return {
        Position(x, y)
        for x in _center_axis_positions(grid.width)
        for y in _center_axis_positions(grid.height)
    }


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


def _ensure_minimum_loops(
    grid: Grid,
    rng: Random,
    playable_positions: set[Position],
    minimum_loops: int,
) -> None:
    candidates = _internal_wall_candidates(grid, playable_positions)
    rng.shuffle(candidates)
    for position, wall in candidates:
        if count_playable_loops(grid, playable_positions) >= minimum_loops:
            return
        _open_wall_if_safe(grid, position, wall, playable_positions)

    if count_playable_loops(grid, playable_positions) < minimum_loops:
        raise InvalidMazeError("playable maze requires at least two loops")


def _ensure_key_cells_available(
    grid: Grid,
    reserved: set[Position],
) -> None:
    if corner_positions(grid) & reserved:
        raise InvalidMazeError("playable maze corners must be reachable")
    if not center_positions(grid) - reserved:
        raise InvalidMazeError("playable maze center must be reachable")


def _ensure_key_cells_reachable(
    grid: Grid,
    reserved: set[Position],
    reachable: set[Position],
) -> None:
    playable = playable_positions(grid, reserved)
    if not corner_positions(grid) <= playable:
        raise InvalidMazeError("playable maze corners must be reachable")
    if not corner_positions(grid) <= reachable:
        raise InvalidMazeError("playable maze corners must be reachable")
    if not center_positions(grid) & playable:
        raise InvalidMazeError("playable maze center must be reachable")
    if not center_positions(grid) & reachable:
        raise InvalidMazeError("playable maze center must be reachable")


def _reduce_dead_ends(
    grid: Grid,
    rng: Random,
    playable_positions: set[Position],
    max_dead_ends: int,
) -> None:
    dead_ends = find_dead_ends(grid, playable_positions)
    while len(dead_ends) > max_dead_ends:
        candidates = _dead_end_wall_candidates(
            grid,
            dead_ends,
            playable_positions,
        )
        rng.shuffle(candidates)
        opened_wall = False
        for position, wall in candidates:
            if _open_wall_if_safe(grid, position, wall, playable_positions):
                opened_wall = True
                break
        if not opened_wall:
            break
        dead_ends = find_dead_ends(grid, playable_positions)

    if len(find_dead_ends(grid, playable_positions)) > max_dead_ends:
        raise InvalidMazeError(
            "playable maze must not contain more than two dead ends"
        )


def _dead_end_wall_candidates(
    grid: Grid,
    dead_ends: set[Position],
    playable_positions: set[Position],
) -> list[tuple[Position, Wall]]:
    candidates: list[tuple[Position, Wall]] = []
    for position in dead_ends:
        for neighbor, wall in grid.neighbors(position):
            if neighbor not in playable_positions:
                continue
            if grid.cell_at(position).has_wall(wall):
                candidates.append((position, wall))
    return candidates


def _open_wall_if_safe(
    grid: Grid,
    position: Position,
    wall: Wall,
    playable_positions: set[Position],
) -> bool:
    if not _can_open_playable_wall(grid, position, wall, playable_positions):
        return False
    if _would_create_playable_open_3x3_area(
        grid,
        position,
        wall,
        playable_positions,
    ):
        return False
    grid.open_wall(position, wall)
    return True


def _would_create_playable_open_3x3_area(
    grid: Grid,
    position: Position,
    wall: Wall,
    playable_positions: set[Position],
) -> bool:
    if grid.width < 3 or grid.height < 3:
        return False
    return any(
        _is_playable_open_3x3_block_with_candidate(
            grid,
            Position(x, y),
            playable_positions,
            position,
            wall,
        )
        for y in range(grid.height - 2)
        for x in range(grid.width - 2)
    )


def _is_playable_open_3x3_block_with_candidate(
    grid: Grid,
    top_left: Position,
    playable_positions: set[Position],
    candidate_position: Position,
    candidate_wall: Wall,
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
            if offset_x < 2 and not _wall_is_open_with_candidate(
                grid,
                position,
                Wall.EAST,
                candidate_position,
                candidate_wall,
            ):
                return False
            if offset_y < 2 and not _wall_is_open_with_candidate(
                grid,
                position,
                Wall.SOUTH,
                candidate_position,
                candidate_wall,
            ):
                return False
    return True


def _wall_is_open_with_candidate(
    grid: Grid,
    position: Position,
    wall: Wall,
    candidate_position: Position,
    candidate_wall: Wall,
) -> bool:
    if _candidate_edge_matches(position, wall, candidate_position, candidate_wall):
        return True
    return not grid.cell_at(position).has_wall(wall)


def _candidate_edge_matches(
    position: Position,
    wall: Wall,
    candidate_position: Position,
    candidate_wall: Wall,
) -> bool:
    return (
        position == candidate_position
        and wall == candidate_wall
    ) or (
        position == candidate_position.move(candidate_wall)
        and wall == candidate_wall.opposite
    )


def _internal_wall_candidates(
    grid: Grid,
    playable_positions: set[Position],
) -> list[tuple[Position, Wall]]:
    candidates: list[tuple[Position, Wall]] = []
    for position in playable_positions:
        for neighbor, wall in grid.neighbors(position):
            if neighbor not in playable_positions:
                continue
            if (neighbor.x, neighbor.y) < (position.x, position.y):
                continue
            candidates.append((position, wall))
    return candidates


def _can_open_playable_wall(
    grid: Grid,
    position: Position,
    wall: Wall,
    playable_positions: set[Position],
) -> bool:
    neighbor = position.move(wall)
    return (
        position in playable_positions
        and grid.in_bounds(neighbor)
        and neighbor in playable_positions
        and grid.cell_at(position).has_wall(wall)
    )


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
