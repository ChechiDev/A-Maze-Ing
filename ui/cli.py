"""Command-line flow for generating and rendering mazes."""

import select
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace
from pathlib import Path
from random import Random
from typing import TextIO

from mazegen import MazeError
from mazegen.encoder import format_maze_output
from mazegen.generator import MazeGenerator, MazeOptions, MazeResult
from ui.config_loader import MazeConfig, load_config
from ui.frame import FrameState, TerminalFrameComposer
from ui.renderer import (
    DEFAULT_STYLE,
    LineRenderer,
    MazeStyle,
    random_maze_style,
)
from ui.terminal_screen import TerminalScreen


SUCCESS = 0
FAILURE = 1
ERROR_STATUS_SECONDS = 4.0


@dataclass(frozen=True, slots=True)
class _View:
    """What the interactive screen currently shows."""

    result: MazeResult
    show_path: bool = True
    style: MazeStyle = DEFAULT_STYLE
    status: str = ""
    status_is_error: bool = False


class _Display:
    """Draw views on the terminal screen, animating the path when enabled."""

    def __init__(
        self,
        screen: TerminalScreen,
        animate: bool,
        sleep: Callable[[float], None],
    ) -> None:
        self._screen = screen
        self._animate = animate
        self._sleep = sleep

    def show(self, view: _View, path_delay: float = 0.0) -> None:
        """Render a view; trace its path cell by cell when a delay is given.

        Args:
            view: State to draw.
            path_delay: Seconds between path cells, ``0`` to draw at once.
        """
        if self._animate and path_delay > 0 and view.show_path:
            self._animate_path(view, path_delay)
        self._screen.render_frame(_compose_view(view))

    def _animate_path(self, view: _View, path_delay: float) -> None:
        self._screen.render_frame(_compose_view(view, draw_path=False))
        renderer = LineRenderer(view.style.palette, view.style.colours)
        for row, column, symbol in renderer.path_cells(view.result):
            self._screen.draw_at(row, column, renderer.paint_path(symbol))
            self._sleep(path_delay)


def main(
    argv: Sequence[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    input_stream: TextIO | None = None,
    interactive: bool = True,
    style_rng: Random | None = None,
    animate: bool | None = None,
    sleep: Callable[[float], None] = time.sleep,
    input_ready: Callable[[float], bool] | None = None,
) -> int:
    """Run the CLI flow and return a process-style exit code.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.
        stdout: Stream for the maze screen; defaults to ``sys.stdout``.
        stderr: Stream for errors and warnings; defaults to ``sys.stderr``.
        input_stream: Stream for menu choices; defaults to standard input.
        interactive: Whether to run the menu after the first render.
        style_rng: Random source for option 3; defaults to an unseeded one.
        animate: Whether to animate the path; defaults to whether ``stdout``
            is a terminal.
        sleep: Function used to wait between path animation steps.
        input_ready: Function that waits up to a timeout for a menu choice
            and returns whether one is available; defaults to waiting on
            standard input when no ``input_stream`` is given.

    Returns:
        ``SUCCESS`` or ``FAILURE``.
    """
    args = list(sys.argv[1:] if argv is None else argv)
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr

    if len(args) != 1:
        _write_error(
            error_stream,
            "usage: python3 a_maze_ing.py <config.txt>",
        )
        return FAILURE

    try:
        config = load_config(args[0])
        result = _generate(config, regeneration_count=0)
        _write_output_file(config.output_file, result)
        if result.warning is not None:
            error_stream.write(f"warning: {result.warning}\n")
        if interactive:
            with TerminalScreen(output_stream) as screen:
                display = _Display(
                    screen,
                    output_stream.isatty() if animate is None else animate,
                    sleep,
                )
                rng = style_rng or Random()
                view = _View(
                    result,
                    style=random_maze_style(rng, DEFAULT_STYLE),
                )
                display.show(view, config.path_delay)
                _run_interactions(
                    args[0],
                    config,
                    view,
                    display,
                    error_stream,
                    input_stream,
                    rng,
                    input_ready or _default_input_ready(input_stream),
                )
        else:
            output_stream.write(_compose_view(_View(result)))
    except (ValueError, MazeError, OSError) as error:
        _write_error(error_stream, str(error))
        return FAILURE
    return SUCCESS


def _options_from_config(config: MazeConfig) -> MazeOptions:
    return _options_with_seed(config, config.seed)


def _options_with_seed(config: MazeConfig, seed: int | None) -> MazeOptions:
    return MazeOptions(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.perfect,
        seed=seed,
    )


def _generate(config: MazeConfig, regeneration_count: int) -> MazeResult:
    seed = _regeneration_seed(config.seed, regeneration_count)
    return MazeGenerator().generate(_options_with_seed(config, seed))


def _regeneration_seed(seed: int | None, regeneration_count: int) -> int | None:
    if regeneration_count == 0:
        return seed
    if seed is None:
        return regeneration_count
    return seed + regeneration_count


def _run_interactions(
    config_path: str,
    config: MazeConfig,
    view: _View,
    display: _Display,
    stderr: TextIO,
    input_stream: TextIO | None,
    style_rng: Random,
    input_ready: Callable[[float], bool],
) -> None:
    regeneration_count = 0
    while True:
        if view.status_is_error and not input_ready(ERROR_STATUS_SECONDS):
            view = replace(view, status="", status_is_error=False)
            display.show(view)
        choice = _read_choice(input_stream)
        if choice == "1":
            try:
                new_config = load_config(config_path)
                config_changed = new_config != config
                new_count = 0 if config_changed else regeneration_count + 1
                new_result = _generate(new_config, new_count)
                _write_output_file(new_config.output_file, new_result)
            except (ValueError, MazeError, OSError) as error:
                status = f"error: {error} (kept previous maze)"
                stderr.write(f"{status}\n")
                view = replace(view, status=status, status_is_error=True)
                display.show(view)
                continue
            config = new_config
            regeneration_count = new_count
            status = (
                "Reloaded config and re-generated maze."
                if config_changed
                else "Re-generated maze."
            )
            if new_result.warning is not None:
                status = f"{status} Warning: {new_result.warning}"
            view = replace(
                view,
                result=new_result,
                status=status,
                status_is_error=False,
            )
            display.show(view, config.path_delay)
            continue
        if choice == "2":
            show_path = not view.show_path
            view = replace(
                view,
                show_path=show_path,
                status=f"Shortest path {'shown' if show_path else 'hidden'}.",
                status_is_error=False,
            )
            display.show(view, config.path_delay)
            continue
        if choice == "3":
            view = replace(
                view,
                style=random_maze_style(style_rng, view.style),
                status="Changed maze colours and style.",
                status_is_error=False,
            )
            display.show(view)
            continue
        if choice == "4":
            display.show(
                replace(view, status="Goodbye.", status_is_error=False),
            )
            return
        status = "invalid choice: use 1, 2, 3, or 4"
        stderr.write(f"{status}\n")
        view = replace(view, status=status, status_is_error=True)
        display.show(view)


def _render(result: MazeResult, show_path: bool, style: MazeStyle) -> str:
    return LineRenderer(style.palette, style.colours).render(
        result,
        show_path=show_path,
    )


def _compose_view(view: _View, draw_path: bool = True) -> str:
    rendered = _render(view.result, view.show_path and draw_path, view.style)
    return TerminalFrameComposer().compose(
        FrameState(
            maze_text=rendered,
            show_path=view.show_path,
            status=view.status,
        ),
    )


def _read_choice(input_stream: TextIO | None) -> str:
    if input_stream is None:
        try:
            return input().strip()
        except EOFError:
            return "4"
    line = input_stream.readline()
    if line == "":
        return "4"
    return line.strip()


def _default_input_ready(
    input_stream: TextIO | None,
) -> Callable[[float], bool]:
    if input_stream is None and sys.stdin.isatty():
        return _stdin_ready
    return _always_ready


def _stdin_ready(timeout: float) -> bool:
    try:
        ready, _, _ = select.select([sys.stdin], [], [], timeout)
    except (OSError, ValueError):
        return True
    return bool(ready)


def _always_ready(timeout: float) -> bool:
    _ = timeout
    return True


def _write_output_file(path: str, result: MazeResult) -> None:
    output = format_maze_output(
        result.grid,
        result.entry,
        result.exit,
        result.shortest_path,
    )
    try:
        Path(path).write_text(output, encoding="utf-8")
    except OSError as error:
        raise OSError(f"could not write output file {path}: {error}") from error


def _write_error(stderr: TextIO, message: str) -> None:
    stderr.write(f"error: {message}\n")


if __name__ == "__main__":
    raise SystemExit(main())
