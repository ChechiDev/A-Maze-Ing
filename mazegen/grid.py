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


@dataclass(frozen=True, slots=True)
class CellView:
    """Read-only view of a cell inside a grid."""

    _cell: Cell

    @property
    def walls(self) -> Wall:
        """Return the currently closed walls."""
        return self._cell.walls

    def has_wall(self, wall: Wall) -> bool:
        """Return whether the given cardinal wall is closed."""
        return self._cell.has_wall(wall)


class Grid:
    """Rectangular maze grid using public ``x,y`` coordinates."""

    def __init__(self, width: int, height: int) -> None:
        """Create a grid with all cell walls closed."""
        if width <= 0 or height <= 0:
            raise ValueError("grid width and height must be positive")
        self._width = width
        self._height = height
        self._cells = tuple(
            tuple(Cell() for _ in range(width)) for _ in range(height)
        )

    @property
    def width(self) -> int:
        """Return the grid width."""
        return self._width

    @property
    def height(self) -> int:
        """Return the grid height."""
        return self._height

    def in_bounds(self, position: Position) -> bool:
        """Return whether the public position is inside the grid."""
        return 0 <= position.x < self._width and 0 <= position.y < self._height

    def cell_at(self, position: Position) -> CellView:
        """Return a read-only cell view at the public position."""
        return CellView(self._mutable_cell_at(position))

    def neighbors(self, position: Position) -> tuple[tuple[Position, Wall], ...]:
        """Return in-bounds neighbor positions and the wall leading to each."""
        self._ensure_in_bounds(position)
        neighbors: list[tuple[Position, Wall]] = []
        for wall in (Wall.NORTH, Wall.EAST, Wall.SOUTH, Wall.WEST):
            neighbor = position.move(wall)
            if self.in_bounds(neighbor):
                neighbors.append((neighbor, wall))
        return tuple(neighbors)

    def open_wall(self, position: Position, wall: Wall) -> None:
        """Open a wall and its opposite neighbor wall symmetrically."""
        neighbor = position.move(wall)
        self._ensure_in_bounds(position)
        if not self.in_bounds(neighbor):
            raise ValueError("cannot open a wall outside the grid")
        self._mutable_cell_at(position).open_wall(wall)
        self._mutable_cell_at(neighbor).open_wall(wall.opposite)

    def positions(self) -> tuple[Position, ...]:
        """Return all positions in row-major public ``x,y`` order."""
        return tuple(
            Position(x, y)
            for y in range(self._height)
            for x in range(self._width)
        )

    def _ensure_in_bounds(self, position: Position) -> None:
        """Raise a clear error if position is outside the grid."""
        if not self.in_bounds(position):
            raise ValueError("position is outside the grid")

    def _mutable_cell_at(self, position: Position) -> Cell:
        """Return the mutable cell at the public position for grid internals."""
        self._ensure_in_bounds(position)
        return self._cells[position.y][position.x]


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
