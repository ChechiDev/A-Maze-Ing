import pytest

from mazegen.grid import Position
from mazegen.pattern42 import build_pattern42_positions, pattern42_overlaps


def test_pattern42_returns_positions_for_minimum_size() -> None:
    result = build_pattern42_positions(11, 7)

    assert result.warning is None
    assert result.positions


def test_pattern42_returns_warning_for_too_small_width() -> None:
    result = build_pattern42_positions(10, 7)

    assert result.positions == frozenset()
    assert result.warning is not None
    assert "too small" in result.warning


def test_pattern42_returns_warning_for_too_small_height() -> None:
    result = build_pattern42_positions(11, 6)

    assert result.positions == frozenset()
    assert result.warning is not None
    assert "too small" in result.warning


def test_pattern42_positions_are_inside_bounds() -> None:
    width = 25
    height = 20
    result = build_pattern42_positions(width, height)

    assert all(0 <= position.x < width for position in result.positions)
    assert all(0 <= position.y < height for position in result.positions)


def test_pattern42_is_centered() -> None:
    result = build_pattern42_positions(25, 20)

    assert Position(7, 6) in result.positions
    assert Position(17, 12) in result.positions
    assert Position(11, 9) in result.positions


def test_pattern42_matches_current_mask_shape() -> None:
    result = build_pattern42_positions(11, 7)

    assert len(result.positions) == 33
    assert Position(0, 0) in result.positions
    assert Position(4, 0) in result.positions
    assert Position(6, 0) in result.positions
    assert Position(10, 0) in result.positions
    assert Position(0, 3) in result.positions
    assert Position(10, 6) in result.positions
    assert Position(1, 1) not in result.positions


def test_pattern42_rejects_non_positive_width() -> None:
    with pytest.raises(ValueError, match="width"):
        build_pattern42_positions(0, 7)


def test_pattern42_rejects_non_positive_height() -> None:
    with pytest.raises(ValueError, match="height"):
        build_pattern42_positions(11, 0)


def test_pattern42_overlaps_returns_true_for_entry_overlap() -> None:
    positions = build_pattern42_positions(11, 7).positions

    assert pattern42_overlaps(positions, Position(0, 0), Position(1, 1))


def test_pattern42_overlaps_returns_true_for_exit_overlap() -> None:
    positions = build_pattern42_positions(11, 7).positions

    assert pattern42_overlaps(positions, Position(1, 1), Position(10, 6))


def test_pattern42_overlaps_returns_false_without_overlap() -> None:
    positions = build_pattern42_positions(11, 7).positions

    assert not pattern42_overlaps(positions, Position(1, 1), Position(2, 1))
