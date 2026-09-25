"""Line-art renderer for generated maze results."""

from mazegen.generator import MazeResult
from mazegen.grid import ALL_WALLS, Position, Wall
from ui.renderer.base import LineRenderPalette
from ui.renderer.theme import PLAIN_THEME, ColourTheme, colourize


CanvasColours = dict[tuple[int, int], int | None]


class LineRenderer:
    """Render maze results using terminal line drawing symbols."""

    def __init__(
        self,
        palette: LineRenderPalette | None = None,
        colours: ColourTheme | None = None,
    ) -> None:
        """Create a renderer using the provided palette and colours.

        Args:
            palette: Symbols for walls and cells; defaults to heavy lines.
            colours: ANSI colours per maze element; defaults to no colour.
        """
        self._palette = palette or LineRenderPalette()
        self._colours = colours or PLAIN_THEME

    def render(self, result: MazeResult, show_path: bool) -> str:
        """Return a line-art representation of the generated maze result."""
        canvas = self._build_canvas(result)
        colours = self._pattern_colours(result)
        if show_path:
            self._draw_path(canvas, result, colours)
        self._mark_position(
            canvas,
            colours,
            result.entry,
            self._palette.entry,
            self._colours.entry,
        )
        self._mark_position(
            canvas,
            colours,
            result.exit,
            self._palette.exit,
            self._colours.exit,
        )
        return self._join(canvas, colours)

    def _pattern_colours(self, result: MazeResult) -> CanvasColours:
        return {
            _canvas_coordinates(position): self._colours.pattern
            for position in result.grid.positions()
            if result.grid.cell_at(position).walls == ALL_WALLS
        }

    def _join(self, canvas: list[list[str]], colours: CanvasColours) -> str:
        lines = []
        for y, row in enumerate(canvas):
            runs: list[tuple[int | None, str]] = []
            for x, symbol in enumerate(row):
                colour = colours.get((y, x), self._wall_colour(symbol))
                if runs and runs[-1][0] == colour:
                    runs[-1] = (colour, runs[-1][1] + symbol)
                else:
                    runs.append((colour, symbol))
            lines.append("".join(colourize(text, colour) for colour, text in runs))
        return "\n".join(lines) + "\n"

    def _wall_colour(self, symbol: str) -> int | None:
        if symbol == self._palette.empty:
            return None
        return self._colours.wall

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

    def path_cells(self, result: MazeResult) -> list[tuple[int, int, str]]:
        """Return the canvas cells of the shortest path in walking order.

        The path is drawn as one continuous line: every cell it crosses and
        every opened wall between two consecutive cells gets a line symbol,
        with corners where the path turns.

        Args:
            result: Maze result whose shortest path is traced from the entry.

        Returns:
            ``(row, column, symbol)`` for each path canvas cell, excluding the
            entry and exit cells.
        """
        positions = [result.entry]
        for step in result.shortest_path:
            wall = _wall_for_step(step)
            if wall is not None:
                positions.append(positions[-1].move(wall))

        cells = []
        for index, position in enumerate(positions):
            if index > 0:
                cells.append(self._path_gap(positions[index - 1], position))
            if position in {result.entry, result.exit}:
                continue
            directions = {
                _direction(position, positions[neighbour])
                for neighbour in (index - 1, index + 1)
                if 0 <= neighbour < len(positions)
            }
            canvas_y, canvas_x = _canvas_coordinates(position)
            cells.append((canvas_y, canvas_x, self._path_symbol(directions)))
        return cells

    def paint_path(self, symbol: str) -> str:
        """Return a path symbol as it is drawn, colour included."""
        return colourize(symbol, self._colours.path)

    def _path_gap(
        self,
        start: Position,
        end: Position,
    ) -> tuple[int, int, str]:
        start_y, start_x = _canvas_coordinates(start)
        end_y, end_x = _canvas_coordinates(end)
        symbol = (
            self._palette.path_horizontal
            if start_y == end_y
            else self._palette.path_vertical
        )
        return (start_y + end_y) // 2, (start_x + end_x) // 2, symbol

    def _path_symbol(self, directions: set[Wall]) -> str:
        palette = self._palette
        if directions <= {Wall.EAST, Wall.WEST}:
            return palette.path_horizontal
        if directions <= {Wall.NORTH, Wall.SOUTH}:
            return palette.path_vertical
        if directions == {Wall.SOUTH, Wall.EAST}:
            return palette.path_top_left
        if directions == {Wall.SOUTH, Wall.WEST}:
            return palette.path_top_right
        if directions == {Wall.NORTH, Wall.EAST}:
            return palette.path_bottom_left
        return palette.path_bottom_right

    def _draw_path(
        self,
        canvas: list[list[str]],
        result: MazeResult,
        colours: CanvasColours,
    ) -> None:
        for canvas_y, canvas_x, symbol in self.path_cells(result):
            canvas[canvas_y][canvas_x] = symbol
            colours[(canvas_y, canvas_x)] = self._colours.path

    def _mark_position(
        self,
        canvas: list[list[str]],
        colours: CanvasColours,
        position: Position,
        symbol: str,
        colour: int | None,
    ) -> None:
        canvas_y, canvas_x = _canvas_coordinates(position)
        canvas[canvas_y][canvas_x] = symbol
        colours[(canvas_y, canvas_x)] = colour


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


def _direction(start: Position, end: Position) -> Wall:
    if end.x > start.x:
        return Wall.EAST
    if end.x < start.x:
        return Wall.WEST
    if end.y > start.y:
        return Wall.SOUTH
    return Wall.NORTH


def _wall_for_step(step: str) -> Wall | None:
    return _PATH_STEPS.get(step)


_PATH_STEPS = {
    "N": Wall.NORTH,
    "E": Wall.EAST,
    "S": Wall.SOUTH,
    "W": Wall.WEST,
}
