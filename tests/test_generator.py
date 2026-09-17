import pytest

from mazegen.generator import MazeOptions, MazeResult
from mazegen.grid import Grid, Position


def test_maze_options_is_constructible_with_valid_values() -> None:
    options = MazeOptions(
        width=3,
        height=2,
        entry=Position(0, 0),
        exit=Position(2, 1),
        perfect=True,
        seed=42,
    )

    assert options.width == 3
    assert options.height == 2
    assert options.entry == Position(0, 0)
    assert options.exit == Position(2, 1)
    assert options.perfect is True
    assert options.seed == 42


def test_maze_options_seed_defaults_to_none() -> None:
    options = MazeOptions(
        width=2,
        height=2,
        entry=Position(0, 0),
        exit=Position(1, 1),
        perfect=False,
    )

    assert options.seed is None


def test_maze_options_rejects_non_positive_width() -> None:
    with pytest.raises(ValueError, match="width"):
        MazeOptions(
            width=0,
            height=2,
            entry=Position(0, 0),
            exit=Position(1, 1),
            perfect=True,
        )


def test_maze_options_rejects_non_positive_height() -> None:
    with pytest.raises(ValueError, match="height"):
        MazeOptions(
            width=2,
            height=0,
            entry=Position(0, 0),
            exit=Position(1, 1),
            perfect=True,
        )


def test_maze_options_rejects_entry_outside_bounds() -> None:
    with pytest.raises(ValueError, match="entry"):
        MazeOptions(
            width=3,
            height=2,
            entry=Position(-1, 0),
            exit=Position(2, 1),
            perfect=True,
        )


def test_maze_options_rejects_exit_outside_bounds() -> None:
    with pytest.raises(ValueError, match="exit"):
        MazeOptions(
            width=3,
            height=2,
            entry=Position(0, 0),
            exit=Position(3, 0),
            perfect=True,
        )


def test_maze_options_rejects_equal_entry_and_exit() -> None:
    with pytest.raises(ValueError, match="entry and exit"):
        MazeOptions(
            width=2,
            height=2,
            entry=Position(0, 0),
            exit=Position(0, 0),
            perfect=True,
        )


def test_maze_result_is_constructible() -> None:
    grid = Grid(2, 2)
    result = MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(1, 1),
        shortest_path="ES",
    )

    assert result.grid is grid
    assert result.entry == Position(0, 0)
    assert result.exit == Position(1, 1)
    assert result.shortest_path == "ES"
    assert result.warning is None


def test_maze_result_accepts_optional_warning() -> None:
    result = MazeResult(
        grid=Grid(1, 1),
        entry=Position(0, 0),
        exit=Position(0, 0),
        shortest_path="",
        warning="pattern 42 omitted",
    )

    assert result.warning == "pattern 42 omitted"


def test_generation_dtos_belong_to_core_module() -> None:
    assert MazeOptions.__module__ == "mazegen.generator"
    assert MazeResult.__module__ == "mazegen.generator"
