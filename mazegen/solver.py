"""Shortest-path solving for generated maze grids."""

from collections import deque

from mazegen.exceptions import UnreachableExitError
from mazegen.grid import Grid, Position, Wall


class ShortestPathSolver:
    """Find shortest paths through open maze passages."""

    def solve(self, grid: Grid, start: Position, end: Position) -> str:
        """Return shortest path directions from start to end."""
        _ensure_in_bounds(grid, start, "start")
        _ensure_in_bounds(grid, end, "end")
        if start == end:
            return ""

        parents: dict[Position, tuple[Position, Wall]] = {}
        visited = {start}
        pending = deque([start])
        while pending:
            position = pending.popleft()
            for neighbor, wall in grid.neighbors(position):
                if neighbor in visited or grid.cell_at(position).has_wall(wall):
                    continue
                parents[neighbor] = (position, wall)
                if neighbor == end:
                    return _reconstruct_path(parents, start, end)
                visited.add(neighbor)
                pending.append(neighbor)

        raise UnreachableExitError("exit is not reachable from entry")


def _ensure_in_bounds(grid: Grid, position: Position, name: str) -> None:
    if not grid.in_bounds(position):
        raise ValueError(f"{name} position is outside the grid")


def _reconstruct_path(
    parents: dict[Position, tuple[Position, Wall]],
    start: Position,
    end: Position,
) -> str:
    walls: list[Wall] = []
    position = end
    while position != start:
        parent, wall = parents[position]
        walls.append(wall)
        position = parent
    return "".join(_wall_to_letter(wall) for wall in reversed(walls))


def _wall_to_letter(wall: Wall) -> str:
    letters = {
        Wall.NORTH: "N",
        Wall.EAST: "E",
        Wall.SOUTH: "S",
        Wall.WEST: "W",
    }
    return letters[wall]
