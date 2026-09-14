"""Grid primitives for the reusable maze generation package."""

from dataclasses import dataclass
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
        _validate_single_wall(self)
        return _OPPOSITE_WALLS[self]

    @property
    def delta(self) -> tuple[int, int]:
        """Return the public ``(x, y)`` movement for this wall."""
        _validate_single_wall(self)
        return _WALL_DELTAS[self]


ALL_WALLS = Wall.NORTH | Wall.EAST | Wall.SOUTH | Wall.WEST


@dataclass(frozen=True, slots=True)
class Position:
    """Public maze coordinates using the ``x,y`` format from config/output."""

    x: int
    y: int

    def move(self, wall: Wall) -> "Position":
        """Return a new position moved one cell through the given wall."""
        delta_x, delta_y = wall.delta
        return Position(self.x + delta_x, self.y + delta_y)


@dataclass(init=False, slots=True)
class Cell:
    """Maze cell storing its currently closed walls."""

    _walls: Wall

    def __init__(self) -> None:
        """Create a cell with all walls closed."""
        self._walls = ALL_WALLS

    @property
    def walls(self) -> Wall:
        """Return the currently closed walls."""
        return self._walls

    def has_wall(self, wall: Wall) -> bool:
        """Return whether the given cardinal wall is closed."""
        _validate_single_wall(wall)
        return bool(self._walls & wall)

    def open_wall(self, wall: Wall) -> None:
        """Open the given cardinal wall without changing other walls."""
        _validate_single_wall(wall)
        self._walls &= ~wall

    def close_wall(self, wall: Wall) -> None:
        """Close the given cardinal wall without changing other walls."""
        _validate_single_wall(wall)
        self._walls |= wall


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


def _validate_single_wall(wall: Wall) -> None:
    """Ensure wall operations receive exactly one cardinal wall."""
    if wall not in _OPPOSITE_WALLS:
        raise ValueError("expected a single cardinal wall")
