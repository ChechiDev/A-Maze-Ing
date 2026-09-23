from ui.renderer import (
    AsciiRenderer,
    LineRenderPalette,
    LineRenderer,
    RenderPalette,
    Renderer,
)

from mazegen.generator import MazeResult
from mazegen.grid import Grid, Position, Wall


def test_fake_renderer_satisfies_renderer_contract() -> None:
    renderer: Renderer = FakeRenderer()
    result = _minimal_result()

    rendered = renderer.render(result, show_path=False)

    assert rendered == "no-path"


def test_renderer_contract_allows_show_path_argument() -> None:
    renderer: Renderer = FakeRenderer()
    result = _minimal_result()

    assert renderer.render(result, show_path=True) == "path"
    assert renderer.render(result, show_path=False) == "no-path"


def test_renderer_module_imports_without_cli_side_effects() -> None:
    assert Renderer.__module__ == "ui.renderer.base"
    assert RenderPalette.__module__ == "ui.renderer.base"


def test_render_palette_uses_default_symbols() -> None:
    palette = RenderPalette()

    assert palette.wall == "#"
    assert palette.path == "."
    assert palette.entry == "E"
    assert palette.exit == "S"
    assert palette.pattern == "4"
    assert palette.empty == " "


def test_render_palette_accepts_custom_symbols() -> None:
    palette = RenderPalette(
        wall="W",
        path="P",
        entry="A",
        exit="B",
        pattern="X",
        empty="_",
    )

    assert palette.wall == "W"
    assert palette.path == "P"
    assert palette.entry == "A"
    assert palette.exit == "B"
    assert palette.pattern == "X"
    assert palette.empty == "_"


def test_line_render_palette_uses_default_line_symbols() -> None:
    palette = LineRenderPalette()

    assert palette.horizontal == "─"
    assert palette.vertical == "│"
    assert palette.top_left == "┌"
    assert palette.top_right == "┐"
    assert palette.bottom_left == "└"
    assert palette.bottom_right == "┘"
    assert palette.junction == "┼"
    assert palette.tee_up == "┴"
    assert palette.tee_down == "┬"
    assert palette.tee_left == "┤"
    assert palette.tee_right == "├"
    assert palette.cross == "┼"
    assert palette.entry == "E"
    assert palette.exit == "S"
    assert palette.path == "·"
    assert palette.pattern == "4"
    assert palette.empty == " "
    assert palette.horizontal != "#"
    assert palette.vertical != "#"


def test_line_render_palette_accepts_custom_symbols() -> None:
    palette = LineRenderPalette(
        horizontal="=",
        vertical="!",
        top_left="a",
        top_right="b",
        bottom_left="c",
        bottom_right="d",
        junction="+",
        tee_up="u",
        tee_down="n",
        tee_left="l",
        tee_right="r",
        cross="x",
        entry="I",
        exit="O",
        path="*",
        pattern="X",
        empty="_",
    )

    assert palette.horizontal == "="
    assert palette.vertical == "!"
    assert palette.top_left == "a"
    assert palette.top_right == "b"
    assert palette.bottom_left == "c"
    assert palette.bottom_right == "d"
    assert palette.junction == "+"
    assert palette.tee_up == "u"
    assert palette.tee_down == "n"
    assert palette.tee_left == "l"
    assert palette.tee_right == "r"
    assert palette.cross == "x"
    assert palette.entry == "I"
    assert palette.exit == "O"
    assert palette.path == "*"
    assert palette.pattern == "X"
    assert palette.empty == "_"


def test_line_render_palette_imports_without_cli_side_effects() -> None:
    assert LineRenderPalette.__module__ == "ui.renderer.base"


def test_ascii_renderer_satisfies_renderer_contract() -> None:
    renderer: Renderer = AsciiRenderer()

    rendered = renderer.render(_path_result(), show_path=False)

    assert isinstance(rendered, str)


def test_ascii_renderer_contains_entry_and_exit() -> None:
    rendered = AsciiRenderer().render(_path_result(), show_path=False)

    assert "E" in rendered
    assert "S" in rendered


def test_ascii_renderer_show_path_changes_output() -> None:
    renderer = AsciiRenderer()
    result = _path_result()

    without_path = renderer.render(result, show_path=False)
    with_path = renderer.render(result, show_path=True)

    assert with_path != without_path
    assert "." in with_path


def test_ascii_renderer_does_not_modify_grid() -> None:
    result = _path_result()
    before = _wall_signature(result.grid)

    AsciiRenderer().render(result, show_path=True)

    assert _wall_signature(result.grid) == before


def test_ascii_renderer_uses_custom_palette_symbols() -> None:
    palette = RenderPalette(
        wall="W",
        path="P",
        entry="A",
        exit="B",
        pattern="X",
        empty="_",
    )

    rendered = AsciiRenderer(palette).render(_path_result(), show_path=True)

    assert "W" in rendered
    assert "P" in rendered
    assert "A" in rendered
    assert "B" in rendered
    assert "_" in rendered


def test_ascii_renderer_distinguishes_fully_closed_cells() -> None:
    palette = RenderPalette(pattern="X")

    rendered = AsciiRenderer(palette).render(_pattern_like_result(), False)

    assert "X" in rendered


def test_ascii_renderer_import_has_no_cli_side_effects() -> None:
    assert AsciiRenderer.__module__ == "ui.renderer.ascii_renderer"


def test_line_renderer_satisfies_renderer_contract() -> None:
    renderer: Renderer = LineRenderer()

    rendered = renderer.render(_horizontal_result(), show_path=False)

    assert isinstance(rendered, str)
    assert rendered.endswith("\n")


def test_line_renderer_contains_entry_and_exit() -> None:
    rendered = LineRenderer().render(_horizontal_result(), show_path=False)

    assert "E" in rendered
    assert "S" in rendered


def test_line_renderer_uses_line_symbols_not_hash_walls() -> None:
    rendered = LineRenderer().render(_horizontal_result(), show_path=False)

    assert "─" in rendered
    assert "│" in rendered
    assert "#" not in rendered


def test_line_renderer_show_path_changes_output() -> None:
    renderer = LineRenderer()
    result = _path_result()

    without_path = renderer.render(result, show_path=False)
    with_path = renderer.render(result, show_path=True)

    assert with_path != without_path
    assert "·" in with_path


def test_line_renderer_does_not_modify_grid() -> None:
    result = _horizontal_result()
    before = _wall_signature(result.grid)

    LineRenderer().render(result, show_path=True)

    assert _wall_signature(result.grid) == before


def test_line_renderer_uses_custom_palette_symbols() -> None:
    palette = LineRenderPalette(
        horizontal="=",
        vertical="!",
        top_left="a",
        top_right="b",
        bottom_left="c",
        bottom_right="d",
        junction="+",
        tee_up="u",
        tee_down="n",
        tee_left="l",
        tee_right="r",
        cross="x",
        entry="I",
        exit="O",
        path="*",
        pattern="X",
        empty="_",
    )

    rendered = LineRenderer(palette).render(_path_result(), show_path=True)

    assert "=" in rendered
    assert "!" in rendered
    assert "I" in rendered
    assert "O" in rendered
    assert "*" in rendered
    assert "_" in rendered


def test_line_renderer_distinguishes_fully_closed_cells() -> None:
    palette = LineRenderPalette(pattern="X")

    rendered = LineRenderer(palette).render(_pattern_like_result(), False)

    assert "X" in rendered


def test_line_renderer_horizontal_corridor_snapshot() -> None:
    rendered = LineRenderer().render(_horizontal_result(), show_path=False)

    assert rendered == "┌───┐\n│E S│\n└───┘\n"


def test_line_renderer_vertical_corridor_snapshot() -> None:
    rendered = LineRenderer().render(_vertical_result(), show_path=False)

    assert rendered == "┌─┐\n│E│\n│ │\n│S│\n└─┘\n"


def test_line_renderer_import_has_no_cli_side_effects() -> None:
    assert LineRenderer.__module__ == "ui.renderer.line_renderer"


class FakeRenderer:
    """Minimal renderer used to verify the protocol contract."""

    def render(self, result: MazeResult, show_path: bool) -> str:
        _ = result
        return "path" if show_path else "no-path"


def _minimal_result() -> MazeResult:
    return MazeResult(
        grid=Grid(1, 1),
        entry=Position(0, 0),
        exit=Position(0, 0),
        shortest_path="",
    )


def _path_result() -> MazeResult:
    grid = Grid(3, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.EAST)
    return MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(2, 0),
        shortest_path="EE",
    )


def _horizontal_result() -> MazeResult:
    grid = Grid(2, 1)
    grid.open_wall(Position(0, 0), Wall.EAST)
    return MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(1, 0),
        shortest_path="E",
    )


def _vertical_result() -> MazeResult:
    grid = Grid(1, 2)
    grid.open_wall(Position(0, 0), Wall.SOUTH)
    return MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(0, 1),
        shortest_path="S",
    )


def _pattern_like_result() -> MazeResult:
    grid = Grid(2, 1)
    return MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(0, 0),
        shortest_path="",
    )


def _wall_signature(grid: Grid) -> tuple[int, ...]:
    return tuple(int(grid.cell_at(position).walls) for position in grid.positions())
