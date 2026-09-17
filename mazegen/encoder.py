"""Hexadecimal wall encoding for maze grids."""

from mazegen.grid import Grid, Position, Wall


def encode_cell_walls(walls: Wall) -> str:
    """Return the lowercase hexadecimal digit for closed cell walls."""
    return format(int(walls), "x")


def encode_grid_row(grid: Grid, y: int) -> str:
    """Return one encoded grid row without trailing newline."""
    if not 0 <= y < grid.height:
        raise ValueError("row y is outside the grid")
    return "".join(
        encode_cell_walls(grid.cell_at(Position(x, y)).walls)
        for x in range(grid.width)
    )


def encode_grid(grid: Grid) -> list[str]:
    """Return all encoded grid rows in row-major order."""
    return [encode_grid_row(grid, y) for y in range(grid.height)]
