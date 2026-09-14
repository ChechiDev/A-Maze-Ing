import pytest

from mazegen.grid import ALL_WALLS, Cell, Grid, Position, Wall


def test_wall_values_match_hexadecimal_encoding() -> None:
    assert int(Wall.NORTH) == 1
    assert int(Wall.EAST) == 2
    assert int(Wall.SOUTH) == 4
    assert int(Wall.WEST) == 8


def test_all_walls_combines_every_wall_bit() -> None:
    assert ALL_WALLS == 15
    assert ALL_WALLS == Wall.NORTH | Wall.EAST | Wall.SOUTH | Wall.WEST


def test_wall_opposites_are_cardinal_pairs() -> None:
    assert Wall.NORTH.opposite == Wall.SOUTH
    assert Wall.SOUTH.opposite == Wall.NORTH
    assert Wall.EAST.opposite == Wall.WEST
    assert Wall.WEST.opposite == Wall.EAST


def test_wall_deltas_use_public_xy_coordinates() -> None:
    assert Wall.NORTH.delta == (0, -1)
    assert Wall.EAST.delta == (1, 0)
    assert Wall.SOUTH.delta == (0, 1)
    assert Wall.WEST.delta == (-1, 0)


@pytest.mark.parametrize(
    "wall",
    (
        Wall.NORTH | Wall.EAST,
        Wall(0),
    ),
)
def test_wall_opposite_rejects_non_single_walls(wall: Wall) -> None:
    with pytest.raises(ValueError, match="single cardinal wall"):
        _ = wall.opposite


@pytest.mark.parametrize(
    "wall",
    (
        Wall.NORTH | Wall.EAST,
        Wall(0),
    ),
)
def test_wall_delta_rejects_non_single_walls(wall: Wall) -> None:
    with pytest.raises(ValueError, match="single cardinal wall"):
        _ = wall.delta


def test_position_stores_public_xy_coordinates() -> None:
    position = Position(1, 2)

    assert position.x == 1
    assert position.y == 2


def test_position_uses_value_equality() -> None:
    assert Position(1, 2) == Position(1, 2)
    assert Position(1, 2) != Position(2, 1)


def test_position_is_immutable() -> None:
    position = Position(1, 2)

    with pytest.raises(AttributeError):
        setattr(position, "x", 3)


def test_position_move_east_matches_required_example() -> None:
    assert Position(1, 2).move(Wall.EAST) == Position(2, 2)


@pytest.mark.parametrize(
    ("wall", "expected"),
    (
        (Wall.NORTH, Position(1, 1)),
        (Wall.EAST, Position(2, 2)),
        (Wall.SOUTH, Position(1, 3)),
        (Wall.WEST, Position(0, 2)),
    ),
)
def test_position_move_uses_public_xy_coordinates(
    wall: Wall,
    expected: Position,
) -> None:
    assert Position(1, 2).move(wall) == expected


@pytest.mark.parametrize(
    "wall",
    (
        Wall.NORTH | Wall.EAST,
        Wall(0),
    ),
)
def test_position_move_rejects_non_single_walls(wall: Wall) -> None:
    with pytest.raises(ValueError, match="single cardinal wall"):
        Position(1, 2).move(wall)


def test_cell_starts_with_all_walls_closed() -> None:
    assert Cell().walls == ALL_WALLS


def test_cell_walls_are_read_only() -> None:
    cell = Cell()

    with pytest.raises(AttributeError):
        setattr(cell, "walls", Wall(0))


@pytest.mark.parametrize(
    "wall",
    (Wall.NORTH, Wall.EAST, Wall.SOUTH, Wall.WEST),
)
def test_cell_has_wall_for_each_initial_cardinal_wall(wall: Wall) -> None:
    assert Cell().has_wall(wall)


def test_cell_open_wall_clears_one_wall() -> None:
    cell = Cell()

    cell.open_wall(Wall.NORTH)

    assert not cell.has_wall(Wall.NORTH)
    assert cell.walls == ALL_WALLS & ~Wall.NORTH


def test_cell_close_wall_sets_one_wall() -> None:
    cell = Cell()
    cell.open_wall(Wall.NORTH)

    cell.close_wall(Wall.NORTH)

    assert cell.has_wall(Wall.NORTH)
    assert cell.walls == ALL_WALLS


def test_cell_open_wall_does_not_change_unrelated_walls() -> None:
    cell = Cell()

    cell.open_wall(Wall.NORTH)

    assert cell.has_wall(Wall.EAST)
    assert cell.has_wall(Wall.SOUTH)
    assert cell.has_wall(Wall.WEST)


def test_cell_close_wall_does_not_change_unrelated_walls() -> None:
    cell = Cell()
    cell.open_wall(Wall.NORTH)
    cell.open_wall(Wall.EAST)

    cell.close_wall(Wall.NORTH)

    assert not cell.has_wall(Wall.EAST)
    assert cell.has_wall(Wall.SOUTH)
    assert cell.has_wall(Wall.WEST)


@pytest.mark.parametrize(
    "wall",
    (
        Wall.NORTH | Wall.EAST,
        Wall(0),
    ),
)
@pytest.mark.parametrize("method_name", ("has_wall", "open_wall", "close_wall"))
def test_cell_wall_operations_reject_non_single_walls(
    wall: Wall,
    method_name: str,
) -> None:
    method = getattr(Cell(), method_name)

    with pytest.raises(ValueError, match="single cardinal wall"):
        method(wall)


def test_grid_stores_public_dimensions() -> None:
    grid = Grid(2, 3)

    assert grid.width == 2
    assert grid.height == 3


@pytest.mark.parametrize(
    ("width", "height"),
    (
        (0, 1),
        (1, 0),
        (-1, 1),
        (1, -1),
    ),
)
def test_grid_rejects_non_positive_dimensions(
    width: int,
    height: int,
) -> None:
    with pytest.raises(ValueError, match="width and height must be positive"):
        Grid(width, height)


def test_grid_starts_with_all_cell_walls_closed() -> None:
    grid = Grid(2, 2)

    for position in grid.positions():
        assert grid.cell_at(position).walls == ALL_WALLS


@pytest.mark.parametrize(
    ("position", "expected"),
    (
        (Position(0, 0), True),
        (Position(1, 2), True),
        (Position(-1, 0), False),
        (Position(0, -1), False),
        (Position(2, 0), False),
        (Position(0, 3), False),
    ),
)
def test_grid_in_bounds_uses_public_xy_coordinates(
    position: Position,
    expected: bool,
) -> None:
    assert Grid(2, 3).in_bounds(position) is expected


def test_grid_cell_at_returns_cell_for_valid_position() -> None:
    assert isinstance(Grid(2, 2).cell_at(Position(1, 1)), Cell)


def test_grid_cell_at_rejects_out_of_bounds_position() -> None:
    with pytest.raises(ValueError, match="outside the grid"):
        Grid(2, 2).cell_at(Position(2, 0))


def test_grid_cell_at_returns_same_cell_state_for_same_position() -> None:
    grid = Grid(2, 1)

    grid.cell_at(Position(0, 0)).open_wall(Wall.EAST)

    assert not grid.cell_at(Position(0, 0)).has_wall(Wall.EAST)


def test_grid_neighbors_for_top_left_corner() -> None:
    assert Grid(2, 2).neighbors(Position(0, 0)) == (
        (Position(1, 0), Wall.EAST),
        (Position(0, 1), Wall.SOUTH),
    )


def test_grid_neighbors_for_center_position() -> None:
    assert Grid(3, 3).neighbors(Position(1, 1)) == (
        (Position(1, 0), Wall.NORTH),
        (Position(2, 1), Wall.EAST),
        (Position(1, 2), Wall.SOUTH),
        (Position(0, 1), Wall.WEST),
    )


def test_grid_neighbors_rejects_out_of_bounds_position() -> None:
    with pytest.raises(ValueError, match="outside the grid"):
        Grid(2, 2).neighbors(Position(-1, 0))


def test_grid_open_wall_opens_symmetric_neighbor_wall() -> None:
    grid = Grid(2, 1)

    grid.open_wall(Position(0, 0), Wall.EAST)

    assert not grid.cell_at(Position(0, 0)).has_wall(Wall.EAST)
    assert not grid.cell_at(Position(1, 0)).has_wall(Wall.WEST)


def test_grid_open_wall_south_opens_neighbor_north_wall() -> None:
    grid = Grid(1, 2)

    grid.open_wall(Position(0, 0), Wall.SOUTH)

    assert not grid.cell_at(Position(0, 0)).has_wall(Wall.SOUTH)
    assert not grid.cell_at(Position(0, 1)).has_wall(Wall.NORTH)


def test_grid_open_wall_does_not_change_unrelated_walls() -> None:
    grid = Grid(2, 1)

    grid.open_wall(Position(0, 0), Wall.EAST)

    assert grid.cell_at(Position(0, 0)).has_wall(Wall.NORTH)
    assert grid.cell_at(Position(0, 0)).has_wall(Wall.SOUTH)
    assert grid.cell_at(Position(0, 0)).has_wall(Wall.WEST)
    assert grid.cell_at(Position(1, 0)).has_wall(Wall.NORTH)
    assert grid.cell_at(Position(1, 0)).has_wall(Wall.EAST)
    assert grid.cell_at(Position(1, 0)).has_wall(Wall.SOUTH)


@pytest.mark.parametrize("wall", (Wall.NORTH, Wall.WEST))
def test_grid_open_wall_rejects_opening_outside_grid(wall: Wall) -> None:
    grid = Grid(2, 2)

    with pytest.raises(ValueError, match="outside the grid"):
        grid.open_wall(Position(0, 0), wall)

    assert grid.cell_at(Position(0, 0)).walls == ALL_WALLS


def test_grid_open_wall_rejects_start_position_outside_grid() -> None:
    with pytest.raises(ValueError, match="outside the grid"):
        Grid(2, 2).open_wall(Position(2, 0), Wall.EAST)


@pytest.mark.parametrize(
    "wall",
    (
        Wall(0),
        Wall.NORTH | Wall.EAST,
    ),
)
def test_grid_open_wall_rejects_non_single_walls(wall: Wall) -> None:
    with pytest.raises(ValueError, match="single cardinal wall"):
        Grid(2, 2).open_wall(Position(0, 0), wall)


def test_grid_positions_use_row_major_public_xy_order() -> None:
    assert Grid(2, 2).positions() == (
        Position(0, 0),
        Position(1, 0),
        Position(0, 1),
        Position(1, 1),
    )
