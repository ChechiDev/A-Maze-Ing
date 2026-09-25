from ui.renderer import (
    AsciiRenderer,
    ColourTheme,
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

    assert palette.wall == "█"
    assert palette.path == "◆"
    assert palette.entry == "E"
    assert palette.exit == "S"
    assert palette.pattern == "█"
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

    assert palette.horizontal == "━"
    assert palette.vertical == "┃"
    assert palette.top_left == "┏"
    assert palette.top_right == "┓"
    assert palette.bottom_left == "┗"
    assert palette.bottom_right == "┛"
    assert palette.junction == "╋"
    assert palette.tee_up == "┻"
    assert palette.tee_down == "┳"
    assert palette.tee_left == "┫"
    assert palette.tee_right == "┣"
    assert palette.cross == "╋"
    assert palette.entry == "E"
    assert palette.exit == "S"
    assert palette.path_horizontal == "─"
    assert palette.path_vertical == "│"
    assert palette.path_top_left == "╭"
    assert palette.path_top_right == "╮"
    assert palette.path_bottom_left == "╰"
    assert palette.path_bottom_right == "╯"
    assert palette.pattern == "█"
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
        path_horizontal="*",
        path_vertical="~",
        path_top_left="1",
        path_top_right="2",
        path_bottom_left="3",
        path_bottom_right="4",
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
    assert palette.path_horizontal == "*"
    assert palette.path_vertical == "~"
    assert palette.path_top_left == "1"
    assert palette.path_top_right == "2"
    assert palette.path_bottom_left == "3"
    assert palette.path_bottom_right == "4"
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
    assert RenderPalette().path in with_path


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

    assert "━" in rendered
    assert "┃" in rendered
    assert "#" not in rendered


def test_line_renderer_show_path_changes_output() -> None:
    renderer = LineRenderer()
    result = _path_result()

    without_path = renderer.render(result, show_path=False)
    with_path = renderer.render(result, show_path=True)

    assert with_path != without_path
    assert LineRenderPalette().path_horizontal in with_path


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
        path_horizontal="*",
        path_vertical="~",
        path_top_left="1",
        path_top_right="2",
        path_bottom_left="3",
        path_bottom_right="4",
        pattern="X",
        empty="_",
    )

    junction_rendered = LineRenderer(palette).render(
        _fully_closed_two_by_two_result(),
        show_path=True,
    )
    path_rendered = LineRenderer(palette).render(
        _l_shaped_result(),
        show_path=True,
    )
    empty_rendered = LineRenderer(palette).render(
        _l_shaped_result(),
        show_path=False,
    )
    rendered = junction_rendered + path_rendered + empty_rendered

    assert "=" in rendered
    assert "!" in rendered
    assert "a" in rendered
    assert "b" in rendered
    assert "c" in rendered
    assert "d" in rendered
    assert "u" in rendered
    assert "n" in rendered
    assert "l" in rendered
    assert "r" in rendered
    assert "x" in rendered
    assert "I" in rendered
    assert "O" in rendered
    assert "*" in rendered
    assert "~" in rendered
    assert "2" in rendered
    assert "X" in rendered
    assert "_" in rendered


def test_line_renderer_distinguishes_fully_closed_cells() -> None:
    palette = LineRenderPalette(pattern="X")

    rendered = LineRenderer(palette).render(_pattern_like_result(), False)

    assert "X" in rendered


def test_line_renderer_horizontal_corridor_snapshot() -> None:
    rendered = LineRenderer().render(_horizontal_result(), show_path=False)

    assert rendered == "┏━━━┓\n┃E S┃\n┗━━━┛\n"


def test_line_renderer_single_fully_closed_cell_snapshot() -> None:
    rendered = LineRenderer().render(_minimal_result(), show_path=False)

    assert rendered == "┏━┓\n┃S┃\n┗━┛\n"


def test_line_renderer_vertical_corridor_snapshot() -> None:
    rendered = LineRenderer().render(_vertical_result(), show_path=False)

    assert rendered == "┏━┓\n┃E┃\n┃ ┃\n┃S┃\n┗━┛\n"


def test_line_renderer_l_shaped_path_snapshot() -> None:
    rendered = LineRenderer().render(_l_shaped_result(), show_path=True)

    assert rendered == "┏━━━┓\n┃E─╮┃\n┣━┓│┃\n┃█┃S┃\n┗━┻━┛\n"


def test_line_renderer_path_does_not_overwrite_entry_or_exit() -> None:
    rendered = LineRenderer().render(_l_shaped_result(), show_path=True)

    assert rendered.count("E") == 1
    assert rendered.count("S") == 1


def test_line_renderer_path_is_one_joined_line_through_open_walls() -> None:
    rendered = LineRenderer().render(_path_result(), show_path=True)

    assert rendered == "┏━━━━━┓\n┃E───S┃\n┗━━━━━┛\n"


def test_line_renderer_vertical_path_snapshot() -> None:
    rendered = LineRenderer().render(_vertical_path_result(), show_path=True)

    assert rendered == "┏━┓\n┃E┃\n┃│┃\n┃│┃\n┃│┃\n┃S┃\n┗━┛\n"


def test_line_renderer_draws_every_path_corner() -> None:
    rendered = LineRenderer().render(_zigzag_result(), show_path=True)

    assert rendered == (
        "┏━━━┳━┓\n"
        "┃E─╮┃█┃\n"
        "┣━━│┣━┫\n"
        "┃╭─╯┃S┃\n"
        "┃│━━┛│┃\n"
        "┃╰───╯┃\n"
        "┗━━━━━┛\n"
    )


def test_line_renderer_path_cells_follow_walking_order() -> None:
    cells = LineRenderer().path_cells(_l_shaped_result())

    assert cells == [(1, 2, "─"), (1, 3, "╮"), (2, 3, "│")]


def test_line_renderer_paint_path_uses_path_colour() -> None:
    renderer = LineRenderer(colours=ColourTheme(path=42))

    assert renderer.paint_path("─") == "\x1b[38;5;42m─\x1b[0m"


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


def _vertical_path_result() -> MazeResult:
    grid = Grid(1, 3)
    grid.open_wall(Position(0, 0), Wall.SOUTH)
    grid.open_wall(Position(0, 1), Wall.SOUTH)
    return MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(0, 2),
        shortest_path="SS",
    )


def _zigzag_result() -> MazeResult:
    grid = Grid(3, 3)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    grid.open_wall(Position(1, 1), Wall.WEST)
    grid.open_wall(Position(0, 1), Wall.SOUTH)
    grid.open_wall(Position(0, 2), Wall.EAST)
    grid.open_wall(Position(1, 2), Wall.EAST)
    grid.open_wall(Position(2, 2), Wall.NORTH)
    return MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(2, 1),
        shortest_path="ESWSEEN",
    )


def _l_shaped_result() -> MazeResult:
    grid = Grid(2, 2)
    grid.open_wall(Position(0, 0), Wall.EAST)
    grid.open_wall(Position(1, 0), Wall.SOUTH)
    return MazeResult(
        grid=grid,
        entry=Position(0, 0),
        exit=Position(1, 1),
        shortest_path="ES",
    )


def _fully_closed_two_by_two_result() -> MazeResult:
    return MazeResult(
        grid=Grid(2, 2),
        entry=Position(0, 0),
        exit=Position(1, 1),
        shortest_path="",
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
