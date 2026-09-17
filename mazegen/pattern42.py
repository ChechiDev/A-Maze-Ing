"""Position helpers for the centered 42 pattern mask."""

from dataclasses import dataclass

from mazegen.grid import Position


@dataclass(frozen=True, slots=True)
class Pattern42Result:
    """Structured result for an optional 42 pattern placement."""

    positions: frozenset[Position]
    warning: str | None = None


def build_pattern42_positions(width: int, height: int) -> Pattern42Result:
    """Return centered reserved positions for the current 42 mask."""
    if width <= 0:
        raise ValueError("width must be positive")
    if height <= 0:
        raise ValueError("height must be positive")
    if width < _PATTERN_WIDTH or height < _PATTERN_HEIGHT:
        return Pattern42Result(
            positions=frozenset(),
            warning="grid is too small for pattern 42",
        )

    top_left_x = (width - _PATTERN_WIDTH) // 2
    top_left_y = (height - _PATTERN_HEIGHT) // 2
    return Pattern42Result(
        positions=frozenset(_mask_positions(top_left_x, top_left_y)),
    )


_PATTERN_42_MASK: tuple[str, ...] = (
    "10001011111",
    "10001000001",
    "10001000001",
    "11111011111",
    "00001010000",
    "00001010000",
    "00001011111",
)

_PATTERN_WIDTH = len(_PATTERN_42_MASK[0])
_PATTERN_HEIGHT = len(_PATTERN_42_MASK)


def _mask_positions(top_left_x: int, top_left_y: int) -> set[Position]:
    _ensure_rectangular_mask()
    return {
        Position(top_left_x + x, top_left_y + y)
        for y, row in enumerate(_PATTERN_42_MASK)
        for x, value in enumerate(row)
        if value == "1"
    }


def _ensure_rectangular_mask() -> None:
    if any(len(row) != _PATTERN_WIDTH for row in _PATTERN_42_MASK):
        raise ValueError("pattern 42 mask must be rectangular")
