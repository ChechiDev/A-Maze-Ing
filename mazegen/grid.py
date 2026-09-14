"""Grid primitives for the reusable maze generation package."""

from enum import IntFlag


class Wall(IntFlag):
    """Cardinal wall bit flags using the required hexadecimal encoding."""

    NORTH = 1
    EAST = 2
    SOUTH = 4
    WEST = 8

    @property
    def opposite(self) -> "Wall":
        """Return the wall at the opposite cardinal direction."""
        return _OPPOSITE_WALLS[self]

    @property
    def delta(self) -> tuple[int, int]:
        """Return the public ``(x, y)`` movement for this wall."""
        return _WALL_DELTAS[self]


ALL_WALLS = Wall.NORTH | Wall.EAST | Wall.SOUTH | Wall.WEST

_OPPOSITE_WALLS: dict[Wall, Wall] = {
    Wall.NORTH: Wall.SOUTH,
    Wall.EAST: Wall.WEST,
    Wall.SOUTH: Wall.NORTH,
    Wall.WEST: Wall.EAST,
}

_WALL_DELTAS: dict[Wall, tuple[int, int]] = {
    Wall.NORTH: (0, -1),
    Wall.EAST: (1, 0),
    Wall.SOUTH: (0, 1),
    Wall.WEST: (-1, 0),
}
