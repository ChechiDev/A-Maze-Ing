import sys

from ui.renderer import AsciiRenderer, RenderPalette, Renderer

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
    assert "ui.cli" not in sys.modules
    assert "a_maze_ing" not in sys.modules


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
