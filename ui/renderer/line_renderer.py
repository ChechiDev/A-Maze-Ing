"""Line-art renderer for generated maze results."""

from mazegen.generator import MazeResult
from mazegen.grid import ALL_WALLS, Position, Wall
from ui.renderer.base import LineRenderPalette


class LineRenderer:
    """Render maze results using terminal line drawing symbols."""

    def __init__(self, palette: LineRenderPalette | None = None) -> None:
        """Create a renderer using the provided palette or defaults."""
        self._palette = palette or LineRenderPalette()

    def render(self, result: MazeResult, show_path: bool) -> str:
        """Return a line-art representation of the generated maze result."""
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
            [self._palette.empty for _ in range(columns)]
            for _ in range(rows)
        ]

        for position in result.grid.positions():
            canvas_y, canvas_x = _canvas_coordinates(position)
            cell = result.grid.cell_at(position)
            canvas[canvas_y][canvas_x] = (
                self._palette.pattern
                if cell.walls == ALL_WALLS
                else self._palette.empty
            )
            for wall in Wall:
                if cell.has_wall(wall):
                    wall_y, wall_x = _canvas_wall_coordinates(position, wall)
                    canvas[wall_y][wall_x] = _wall_symbol(self._palette, wall)
        self._draw_junctions(canvas)
        return canvas

    def _draw_junctions(self, canvas: list[list[str]]) -> None:
        for y in range(0, len(canvas), 2):
            for x in range(0, len(canvas[y]), 2):
                canvas[y][x] = _junction_symbol(canvas, y, x, self._palette)

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


def _wall_symbol(palette: LineRenderPalette, wall: Wall) -> str:
    if wall in (Wall.NORTH, Wall.SOUTH):
        return palette.horizontal
    return palette.vertical


def _junction_symbol(
    canvas: list[list[str]],
    y: int,
    x: int,
    palette: LineRenderPalette,
) -> str:
    up = y > 0 and canvas[y - 1][x] == palette.vertical
    down = y < len(canvas) - 1 and canvas[y + 1][x] == palette.vertical
    left = x > 0 and canvas[y][x - 1] == palette.horizontal
    right = x < len(canvas[y]) - 1 and canvas[y][x + 1] == palette.horizontal
    connections = (up, down, left, right)
    count = sum(connections)

    if count == 0:
        return palette.empty
    if count == 1:
        if up or down:
            return palette.vertical
        return palette.horizontal
    if count == 2:
        return _two_way_junction_symbol(up, down, left, right, palette)
    if count == 3:
        return _tee_junction_symbol(up, down, left, right, palette)
    return palette.cross


def _two_way_junction_symbol(
    up: bool,
    down: bool,
    left: bool,
    right: bool,
    palette: LineRenderPalette,
) -> str:
    if left and right:
        return palette.horizontal
    if up and down:
        return palette.vertical
    if down and right:
        return palette.top_left
    if down and left:
        return palette.top_right
    if up and right:
        return palette.bottom_left
    if up and left:
        return palette.bottom_right
    return palette.junction


def _tee_junction_symbol(
    up: bool,
    down: bool,
    left: bool,
    right: bool,
    palette: LineRenderPalette,
) -> str:
    if up and left and right:
        return palette.tee_up
    if down and left and right:
        return palette.tee_down
    if up and down and left:
        return palette.tee_left
    if up and down and right:
        return palette.tee_right
    return palette.junction


def _wall_for_step(step: str) -> Wall | None:
    return _PATH_STEPS.get(step)


_PATH_STEPS = {
    "N": Wall.NORTH,
    "E": Wall.EAST,
    "S": Wall.SOUTH,
    "W": Wall.WEST,
}
