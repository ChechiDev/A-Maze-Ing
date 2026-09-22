"""Perfect maze mode validation."""

from random import Random

from mazegen.exceptions import InvalidMazeError
from mazegen.grid import Grid, Position
from mazegen.validation import (
    count_loops,
    count_open_edges,
    has_open_3x3_area,
)


class PerfectMode:
    """Validate that a generated grid satisfies perfect maze constraints."""

    def apply(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
        entry: Position,
        exit: Position,
    ) -> Grid:
        """Return grid if it satisfies perfect maze invariants."""
        _ = rng
        playable_positions = set(grid.positions()) - reserved
        if not playable_positions:
            raise InvalidMazeError(
                "perfect maze playable cells must be connected"
            )
        if entry not in playable_positions or exit not in playable_positions:
            raise InvalidMazeError("entry and exit must be reachable")
        reachable = _reachable_playable_positions(
            grid,
            entry,
            playable_positions,
        )
        if playable_positions - reachable:
            raise InvalidMazeError(
                "perfect maze playable cells must be connected"
            )
        if exit not in reachable:
            raise InvalidMazeError("entry and exit must be reachable")
        if has_open_3x3_area(grid):
            raise InvalidMazeError(
                "perfect maze must not contain open 3x3 areas"
            )
        if count_loops(grid, playable_positions) != 0:
            raise InvalidMazeError("perfect maze must not contain loops")
        if count_open_edges(grid, playable_positions) != len(playable_positions) - 1:
            raise InvalidMazeError("perfect maze must not contain loops")
        return grid


def _reachable_playable_positions(
    grid: Grid,
    start: Position,
    playable_positions: set[Position],
) -> set[Position]:
    pending = [start]
    visited = {start}
    while pending:
        position = pending.pop()
        for neighbor, wall in grid.neighbors(position):
            if neighbor not in playable_positions:
                continue
            if neighbor in visited or grid.cell_at(position).has_wall(wall):
                continue
            visited.add(neighbor)
            pending.append(neighbor)
    return visited
