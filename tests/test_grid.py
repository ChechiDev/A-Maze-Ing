import pytest

from mazegen.grid import ALL_WALLS, Wall


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
