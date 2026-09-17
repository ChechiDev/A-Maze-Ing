"""Internal graph validators for maze grids."""

from collections import deque

from mazegen.grid import Grid, Position, Wall


def reachable_positions(grid: Grid, start: Position) -> set[Position]:
    """Return positions reachable from start through open walls."""
    if not grid.in_bounds(start):
        return set()

    visited = {start}
    pending = deque([start])
    while pending:
        position = pending.popleft()
        for neighbor, wall in grid.neighbors(position):
            if neighbor in visited or grid.cell_at(position).has_wall(wall):
                continue
            visited.add(neighbor)
            pending.append(neighbor)
    return visited


def count_open_edges(grid: Grid, positions: set[Position]) -> int:
    """Count undirected open edges between the given positions."""
    edges = 0
    for position in positions:
        if not grid.in_bounds(position):
            continue
        for neighbor, wall in grid.neighbors(position):
            if neighbor in positions and not grid.cell_at(position).has_wall(wall):
                edges += 1
    return edges // 2


def count_loops(grid: Grid, positions: set[Position]) -> int:
    """Return the number of independent loops in the position subgraph."""
    valid_positions = _in_bounds_positions(grid, positions)
    if not valid_positions:
        return 0
    components = _count_connected_components(grid, valid_positions)
    return (
        count_open_edges(grid, valid_positions)
        - len(valid_positions)
        + components
    )


def is_connected(grid: Grid, positions: set[Position]) -> bool:
    """Return whether all given positions are connected through open walls."""
    if not positions:
        return True
    start = next(iter(positions))
    return positions <= reachable_positions(grid, start)


def has_wall_coherence(grid: Grid) -> bool:
    """Return whether every shared wall has matching neighbor state."""
    for position in grid.positions():
        for neighbor, wall in grid.neighbors(position):
            wall_closed = grid.cell_at(position).has_wall(wall)
            opposite_closed = grid.cell_at(neighbor).has_wall(wall.opposite)
            if wall_closed != opposite_closed:
                return False
    return True


def has_open_3x3_area(grid: Grid) -> bool:
    """Return whether any 3x3 block has every internal wall open."""
    if grid.width < 3 or grid.height < 3:
        return False

    return any(
        _is_open_3x3_block(grid, Position(x, y))
        for y in range(grid.height - 2)
        for x in range(grid.width - 2)
    )


def _count_connected_components(grid: Grid, positions: set[Position]) -> int:
    remaining = set(positions)
    components = 0
    while remaining:
        start = next(iter(remaining))
        component = reachable_positions(grid, start) & positions
        remaining -= component
        components += 1
    return components


def _in_bounds_positions(grid: Grid, positions: set[Position]) -> set[Position]:
    return {position for position in positions if grid.in_bounds(position)}


def _is_open_3x3_block(grid: Grid, top_left: Position) -> bool:
    for offset_y in range(3):
        for offset_x in range(3):
            position = Position(top_left.x + offset_x, top_left.y + offset_y)
            if offset_x < 2 and grid.cell_at(position).has_wall(Wall.EAST):
                return False
            if offset_y < 2 and grid.cell_at(position).has_wall(Wall.SOUTH):
                return False
    return True
