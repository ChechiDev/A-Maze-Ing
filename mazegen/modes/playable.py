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
        _validate_playable_final_state(grid, reserved, entry)
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


def _validate_playable_final_state(
    grid: Grid,
    reserved: set[Position],
    entry: Position,
) -> None:
    playable = playable_positions(grid, reserved)
    reachable = reachable_playable_positions(grid, entry, reserved)
    if playable - reachable:
        raise InvalidMazeError("playable maze cells must be connected")
    if count_playable_loops(grid, playable) < 2:
        raise InvalidMazeError("playable maze requires at least two loops")
    if not corner_positions(grid) <= reachable:
        raise InvalidMazeError("playable maze corners must be reachable")
    if not center_positions(grid) & reachable:
        raise InvalidMazeError("playable maze center must be reachable")
    if len(find_dead_ends(grid, playable)) > MAX_REAL_DEAD_ENDS:
        raise InvalidMazeError(
            "playable maze must not contain more than two dead ends"
        )
    if has_playable_open_3x3_area(grid, playable):
        raise InvalidMazeError(
            "playable maze must not contain open 3x3 areas"
        )


def _reduce_dead_ends(
    grid: Grid,
    rng: Random,
    playable_positions: set[Position],
    max_dead_ends: int,
) -> None:
    """Open walls until at most `max_dead_ends` dead-ends remain.

    The queue holding the visit order is only rebuilt when it runs out, not
    on every single wall opened: rebuilding it from the (still large) full
    `dead_ends` set after each individual open is what made this scale
    quadratically with the maze size on bigger grids.
    """
    dead_ends = find_dead_ends(grid, playable_positions)
    queue = _shuffled_dead_end_queue(dead_ends, rng)
    cursor = 0
    resolved_since_rescan = False

    while len(dead_ends) > max_dead_ends:
        if cursor >= len(queue):
            if not resolved_since_rescan:
                break  # a full pass opened nothing: no safe wall remains
            queue = _shuffled_dead_end_queue(dead_ends, rng)
            cursor = 0
            resolved_since_rescan = False
            if not queue:
                break

        position = queue[cursor]
        cursor += 1
        if position not in dead_ends:
            continue  # already resolved earlier in this pass

        wall = _open_safe_dead_end_wall(grid, rng, position, playable_positions)
        if wall is None:
            continue
        dead_ends.discard(position)
        dead_ends.discard(position.move(wall))
        resolved_since_rescan = True

    if len(dead_ends) > max_dead_ends:
        raise InvalidMazeError(
            "playable maze must not contain more than two dead ends"
        )


def _shuffled_dead_end_queue(
    dead_ends: set[Position],
    rng: Random,
) -> list[Position]:
    queue = list(dead_ends)
    rng.shuffle(queue)
    return queue


def _open_safe_dead_end_wall(
    grid: Grid,
    rng: Random,
    position: Position,
    playable_positions: set[Position],
) -> Wall | None:
    """Try this dead-end's own candidate walls and open the first safe one."""
    walls = [
        wall
        for neighbor, wall in grid.neighbors(position)
        if neighbor in playable_positions
        and grid.cell_at(position).has_wall(wall)
    ]
    rng.shuffle(walls)
    for wall in walls:
        if _open_wall_if_safe(grid, position, wall, playable_positions):
            return wall
    return None


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
        for x, y in _candidate_block_origins(grid, position, wall)
    )


def _candidate_block_origins(
    grid: Grid,
    position: Position,
    wall: Wall,
) -> tuple[tuple[int, int], ...]:
    """Return the 3x3 block top-left origins that could contain the edge.

    A 3x3 block only depends on the internal walls of its own 9 cells, so
    opening one wall can only affect the (at most 4) blocks whose area
    covers both cells joined by that wall -- checking every other block in
    the grid is redundant work that scales with the whole maze instead of
    with a single candidate.
    """
    neighbor = position.move(wall)
    min_x, max_x = sorted((position.x, neighbor.x))
    min_y, max_y = sorted((position.y, neighbor.y))
    x_start, x_end = max(0, max_x - 2), min(grid.width - 3, min_x)
    y_start, y_end = max(0, max_y - 2), min(grid.height - 3, min_y)
    return tuple(
        (x, y)
        for y in range(y_start, y_end + 1)
        for x in range(x_start, x_end + 1)
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
