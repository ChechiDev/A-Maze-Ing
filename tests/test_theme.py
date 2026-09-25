from random import Random

from mazegen.generator import MazeResult
from mazegen.grid import Grid, Position, Wall
from ui.renderer import (
    DEFAULT_STYLE,
    LINE_STYLES,
    ColourTheme,
    LineRenderer,
    MazeStyle,
    random_maze_style,
)
from ui.renderer.theme import (
    PLAIN_THEME,
    RESET,
    colourize,
    random_colour_theme,
)


def test_default_style_is_uncoloured() -> None:
    assert DEFAULT_STYLE.colours == PLAIN_THEME
    assert DEFAULT_STYLE.palette == LINE_STYLES[0]


def test_line_styles_are_all_different() -> None:
    assert len(set(LINE_STYLES)) == len(LINE_STYLES)


def test_colourize_wraps_text_in_ansi_256_colour() -> None:
    assert colourize("━", 196) == f"\x1b[38;5;196m━{RESET}"


def test_colourize_without_colour_returns_text_unchanged() -> None:
    assert colourize("━", None) == "━"


def test_colourize_skips_empty_text() -> None:
    assert colourize("", 196) == ""


def test_random_colour_theme_uses_five_distinct_colours() -> None:
    for seed in range(50):
        theme = random_colour_theme(Random(seed))
        colours = [
            theme.wall,
            theme.path,
            theme.pattern,
            theme.entry,
            theme.exit,
        ]

        assert None not in colours
        assert len(set(colours)) == 5


def test_random_maze_style_never_repeats_current_style() -> None:
    rng = Random(0)
    style = DEFAULT_STYLE

    for _ in range(200):
        new_style = random_maze_style(rng, style)
        assert new_style != style
        style = new_style


def test_random_maze_style_uses_known_line_styles() -> None:
    rng = Random(3)

    styles = [random_maze_style(rng, DEFAULT_STYLE) for _ in range(100)]

    assert {style.palette for style in styles} <= set(LINE_STYLES)
    assert len({style.palette for style in styles}) > 1


def test_random_maze_style_is_reproducible_with_same_seed() -> None:
    first = random_maze_style(Random(11), DEFAULT_STYLE)
    second = random_maze_style(Random(11), DEFAULT_STYLE)

    assert first == second


def test_line_renderer_plain_theme_emits_no_escape_codes() -> None:
    rendered = LineRenderer(colours=PLAIN_THEME).render(
        _l_shaped_result(),
        show_path=True,
    )

    assert "\x1b[" not in rendered


def test_line_renderer_colours_each_maze_element() -> None:
    theme = ColourTheme(wall=1, path=2, pattern=3, entry=4, exit=5)

    rendered = LineRenderer(colours=theme).render(
        _l_shaped_result(),
        show_path=True,
    )

    assert "\x1b[38;5;1m┏━━━┓" in rendered
    assert "\x1b[38;5;2m●" in rendered
    assert "\x1b[38;5;3m█" in rendered
    assert "\x1b[38;5;4mE" in rendered
    assert "\x1b[38;5;5mS" in rendered


def test_line_renderer_does_not_colour_empty_space() -> None:
    theme = ColourTheme(wall=1, path=2, pattern=3, entry=4, exit=5)

    rendered = LineRenderer(colours=theme).render(
        _l_shaped_result(),
        show_path=False,
    )

    assert "\x1b[38;5;1m " not in rendered
    assert f"{RESET} \x1b[" in rendered


def test_line_renderer_uses_style_palette_and_colours_together() -> None:
    style = MazeStyle(
        palette=LINE_STYLES[-1],
        colours=ColourTheme(wall=9),
    )

    rendered = LineRenderer(style.palette, style.colours).render(
        _l_shaped_result(),
        show_path=False,
    )

    assert f"\x1b[38;5;9m{style.palette.top_left}" in rendered


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
