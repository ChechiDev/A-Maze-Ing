"""ASCII renderer for generated maze results."""

from mazegen.generator import MazeResult
from mazegen.grid import ALL_WALLS, Position, Wall
from ui.renderer.base import RenderPalette


class AsciiRenderer:
    """Render maze results as deterministic ASCII text."""

    def __init__(self, palette: RenderPalette | None = None) -> None:
        """Create a renderer using the provided palette or defaults."""
        self._palette = palette or RenderPalette()

    def render(self, result: MazeResult, show_path: bool) -> str:
        """Return an ASCII representation of the generated maze result."""
        canvas = self._build_canvas(result)
        if show_path:
            self._draw_path(canvas, result)
        self._mark_position(canvas, result.entry, self._palette.entry)
        self._mark_position(canvas, result.exit, self._palette.exit)
        return "\n".join("".join(row) for row in canvas) + "\n"

    def _build_canvas(self, result: MazeResult) -> list[list[str]]:
        rows = result.grid.height * 2 + 1
        columns = result.grid.width * 2 + 1
        canvas = [
            [self._palette.wall for _ in range(columns)]
            for _ in range(rows)
        ]

        for position in result.grid.positions():
            canvas_y, canvas_x = _canvas_coordinates(position)
            cell = result.grid.cell_at(position)
            if cell.walls == ALL_WALLS:
                canvas[canvas_y][canvas_x] = self._palette.pattern
                continue

            canvas[canvas_y][canvas_x] = self._palette.empty
            for wall in Wall:
                if not cell.has_wall(wall):
                    wall_y, wall_x = _canvas_wall_coordinates(position, wall)
                    canvas[wall_y][wall_x] = self._palette.empty
        return canvas

    def _draw_path(
        self,
        canvas: list[list[str]],
        result: MazeResult,
    ) -> None:
        position = result.entry
        for step in result.shortest_path:
            wall = _wall_for_step(step)
            if wall is None:
                continue
            position = position.move(wall)
            if position in {result.entry, result.exit}:
                continue
            self._mark_position(canvas, position, self._palette.path)

    def _mark_position(
        self,
        canvas: list[list[str]],
        position: Position,
        symbol: str,
    ) -> None:
        canvas_y, canvas_x = _canvas_coordinates(position)
        canvas[canvas_y][canvas_x] = symbol


def _canvas_coordinates(position: Position) -> tuple[int, int]:
    return position.y * 2 + 1, position.x * 2 + 1


def _canvas_wall_coordinates(
    position: Position,
    wall: Wall,
) -> tuple[int, int]:
    canvas_y, canvas_x = _canvas_coordinates(position)
    delta_x, delta_y = wall.delta
    return canvas_y + delta_y, canvas_x + delta_x


def _wall_for_step(step: str) -> Wall | None:
    return _PATH_STEPS.get(step)


_PATH_STEPS = {
    "N": Wall.NORTH,
    "E": Wall.EAST,
    "S": Wall.SOUTH,
    "W": Wall.WEST,
}
