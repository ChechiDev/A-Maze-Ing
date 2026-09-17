import pytest

from mazegen.encoder import encode_cell_walls, encode_grid, encode_grid_row
from mazegen.grid import ALL_WALLS, Grid, Position, Wall


def test_encode_cell_walls_returns_lowercase_hex_digit() -> None:
    assert encode_cell_walls(ALL_WALLS) == "f"
    assert encode_cell_walls(Wall.NORTH | Wall.EAST) == "3"
    assert encode_cell_walls(Wall.EAST | Wall.WEST) == "a"
    assert encode_cell_walls(Wall(0)) == "0"
    assert encode_cell_walls(Wall.SOUTH) == "4"


def test_encode_grid_row_returns_initial_closed_row() -> None:
    assert encode_grid_row(Grid(2, 1), 0) == "ff"


def test_encode_grid_row_reflects_open_shared_wall() -> None:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)

    assert encode_grid_row(grid, 0) == "d7"


def test_encode_grid_row_rejects_negative_y() -> None:
    with pytest.raises(ValueError, match="row y is outside the grid"):
        encode_grid_row(Grid(1, 1), -1)


def test_encode_grid_row_rejects_y_at_height() -> None:
    with pytest.raises(ValueError, match="row y is outside the grid"):
        encode_grid_row(Grid(1, 1), 1)


def test_encode_grid_returns_initial_closed_rows() -> None:
    assert encode_grid(Grid(2, 2)) == ["ff", "ff"]


def test_encode_grid_returns_known_two_by_two_grid() -> None:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    grid.open_wall(Position(1, 1), Wall.WEST)

    assert encode_grid(grid) == ["d3", "d6"]
