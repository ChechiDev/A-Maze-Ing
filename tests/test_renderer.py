from ui.renderer import RenderPalette, Renderer

from mazegen.generator import MazeResult
from mazegen.grid import Grid, Position


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
