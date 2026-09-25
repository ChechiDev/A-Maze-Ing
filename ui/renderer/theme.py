"""Colour themes and random maze style selection for terminal rendering."""

from dataclasses import dataclass
from random import Random

from ui.renderer.base import LineRenderPalette


RESET = "\x1b[0m"


@dataclass(frozen=True, slots=True)
class ColourTheme:
    """ANSI 256-colour codes for each maze element.

    A ``None`` value leaves that element uncoloured.
    """

    wall: int | None = None
    path: int | None = None
    pattern: int | None = None
    entry: int | None = None
    exit: int | None = None


@dataclass(frozen=True, slots=True)
class MazeStyle:
    """Line symbols and colours used together to draw a maze."""

    palette: LineRenderPalette
    colours: ColourTheme


PLAIN_THEME = ColourTheme()

LINE_STYLES: tuple[LineRenderPalette, ...] = (
    LineRenderPalette(),
    LineRenderPalette(
        horizontal="─",
        vertical="│",
        top_left="┌",
        top_right="┐",
        bottom_left="└",
        bottom_right="┘",
        junction="┼",
        tee_up="┴",
        tee_down="┬",
        tee_left="┤",
        tee_right="├",
        cross="┼",
    ),
    LineRenderPalette(
        horizontal="─",
        vertical="│",
        top_left="╭",
        top_right="╮",
        bottom_left="╰",
        bottom_right="╯",
        junction="┼",
        tee_up="┴",
        tee_down="┬",
        tee_left="┤",
        tee_right="├",
        cross="┼",
    ),
    LineRenderPalette(
        horizontal="═",
        vertical="║",
        top_left="╔",
        top_right="╗",
        bottom_left="╚",
        bottom_right="╝",
        junction="╬",
        tee_up="╩",
        tee_down="╦",
        tee_left="╣",
        tee_right="╠",
        cross="╬",
    ),
)

DEFAULT_STYLE = MazeStyle(palette=LINE_STYLES[0], colours=PLAIN_THEME)

# Bright ANSI 256-colour codes that stay readable on dark and light terminals.
_COLOUR_CHOICES: tuple[int, ...] = (
    196,  # red
    202,  # orange
    214,  # amber
    226,  # yellow
    118,  # lime
    46,  # green
    49,  # aquamarine
    51,  # cyan
    39,  # sky blue
    27,  # blue
    93,  # purple
    129,  # violet
    201,  # magenta
    213,  # pink
)


def colourize(text: str, colour: int | None) -> str:
    """Wrap text in an ANSI 256-colour foreground sequence.

    Args:
        text: Visible text to colour.
        colour: ANSI 256-colour code, or ``None`` to leave text unchanged.

    Returns:
        The coloured text, or the original text when no colour is given.
    """
    if colour is None or not text:
        return text
    return f"\x1b[38;5;{colour}m{text}{RESET}"


def random_colour_theme(rng: Random) -> ColourTheme:
    """Return a theme with five distinct random colours.

    Args:
        rng: Random source used to pick the colours.

    Returns:
        A colour theme where every maze element has its own colour.
    """
    wall, path, pattern, entry, exit = rng.sample(_COLOUR_CHOICES, 5)
    return ColourTheme(
        wall=wall,
        path=path,
        pattern=pattern,
        entry=entry,
        exit=exit,
    )


def random_maze_style(rng: Random, current: MazeStyle) -> MazeStyle:
    """Return a random line style and colour theme different from current.

    Args:
        rng: Random source used to pick the style.
        current: Style currently on screen; the result never equals it.

    Returns:
        A new maze style with random line symbols and colours.
    """
    while True:
        style = MazeStyle(
            palette=rng.choice(LINE_STYLES),
            colours=random_colour_theme(rng),
        )
        if style != current:
            return style
