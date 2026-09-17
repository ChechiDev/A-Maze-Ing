"""Recursive backtracker maze generation strategy."""

from random import Random

from mazegen.grid import Grid, Position, Wall


class RecursiveBacktrackerStrategy:
    """Generate a perfect maze using iterative depth-first search."""

    def generate(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
    ) -> Grid:
        """Open walls to connect every non-reserved position as a tree."""
        transitables = _transitable_positions(grid, reserved)
        if len(transitables) < 2:
            return grid

        start = rng.choice(sorted(transitables, key=lambda position: (
            position.y,
            position.x,
        )))
        visited = {start}
        stack = [start]

        while stack:
            current = stack[-1]
            candidates = _unvisited_neighbors(grid, current, transitables, visited)
            if not candidates:
                stack.pop()
                continue

            neighbor, wall = rng.choice(candidates)
            grid.open_wall(current, wall)
            visited.add(neighbor)
            stack.append(neighbor)

        return grid


def _transitable_positions(grid: Grid, reserved: set[Position]) -> set[Position]:
    return {position for position in grid.positions() if position not in reserved}


def _unvisited_neighbors(
    grid: Grid,
    position: Position,
    transitables: set[Position],
    visited: set[Position],
) -> list[tuple[Position, Wall]]:
    return [
        (neighbor, wall)
        for neighbor, wall in grid.neighbors(position)
        if neighbor in transitables and neighbor not in visited
    ]
