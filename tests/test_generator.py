import pytest
from random import Random

import mazegen
from mazegen import (
    MazeError,
    MazeGenerator as PublicMazeGenerator,
    MazeOptions as PublicMazeOptions,
    MazeResult as PublicMazeResult,
    Position as PublicPosition,
    UnreachableExitError,
)
from mazegen.generator import MazeGenerator, MazeOptions, MazeResult
from mazegen.grid import Grid, Position, Wall
from mazegen.validation import (
    count_loops,
    count_open_edges,
    has_wall_coherence,
    is_connected,
)


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


def test_maze_generator_generates_valid_result() -> None:
    options = MazeOptions(
        width=4,
        height=4,
        entry=Position(0, 0),
        exit=Position(3, 3),
        perfect=True,
        seed=42,
    )

    result = MazeGenerator().generate(options)
    positions = set(result.grid.positions())

    assert isinstance(result.grid, Grid)
    assert result.entry == options.entry
    assert result.exit == options.exit
    assert result.warning is None
    assert set(result.shortest_path) <= set("NESW")
    assert is_connected(result.grid, positions)
    assert count_open_edges(result.grid, positions) == len(positions) - 1
    assert count_loops(result.grid, positions) == 0
    assert has_wall_coherence(result.grid)


def test_maze_generator_reproduces_grid_and_path_for_same_seed() -> None:
    options = MazeOptions(
        width=4,
        height=4,
        entry=Position(0, 0),
        exit=Position(3, 3),
        perfect=True,
        seed=123,
    )
    generator = MazeGenerator()

    first = generator.generate(options)
    second = generator.generate(options)

    assert _wall_signature(first.grid) == _wall_signature(second.grid)
    assert first.shortest_path == second.shortest_path


def test_maze_generator_uses_injected_strategy() -> None:
    options = MazeOptions(
        width=2,
        height=1,
        entry=Position(0, 0),
        exit=Position(1, 0),
        perfect=True,
    )

    result = MazeGenerator(strategy=FakeStrategy()).generate(options)

    assert result.shortest_path == "E"


def test_public_import_exposes_maze_generator() -> None:
    assert PublicMazeGenerator.__name__ == "MazeGenerator"


def test_public_imports_support_generating_maze_result() -> None:
    options = PublicMazeOptions(
        width=2,
        height=2,
        entry=PublicPosition(0, 0),
        exit=PublicPosition(1, 1),
        perfect=True,
        seed=42,
    )

    result = PublicMazeGenerator().generate(options)

    assert isinstance(result, PublicMazeResult)


def test_public_import_exposes_exception_hierarchy() -> None:
    assert issubclass(UnreachableExitError, MazeError)


def test_public_all_contains_expected_names() -> None:
    expected = {
        "Grid",
        "InvalidConfigurationError",
        "InvalidMazeError",
        "MazeError",
        "MazeGenerator",
        "MazeOptions",
        "MazeResult",
        "Position",
        "UnreachableExitError",
        "Wall",
    }

    assert expected <= set(mazegen.__all__)


class FakeStrategy:
    """Minimal strategy for dependency injection tests."""

    def generate(
        self,
        grid: Grid,
        rng: Random,
        reserved: set[Position],
    ) -> Grid:
        _ = rng.random()
        assert reserved == set()
        grid.open_wall(Position(0, 0), Wall.EAST)
        return grid


def _wall_signature(grid: Grid) -> tuple[int, ...]:
    return tuple(int(grid.cell_at(position).walls) for position in grid.positions())
