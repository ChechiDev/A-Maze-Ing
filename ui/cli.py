"""Command-line flow for generating and rendering mazes."""

import sys
from collections.abc import Sequence
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


def main(
    argv: Sequence[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    input_stream: TextIO | None = None,
    interactive: bool = True,
    style_rng: Random | None = None,
) -> int:
    """Run the CLI flow and return a process-style exit code."""
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
                screen.render_frame(
                    _compose_frame(result, show_path=True, style=DEFAULT_STYLE),
                )
                _run_interactions(
                    args[0],
                    config,
                    result,
                    screen,
                    error_stream,
                    input_stream,
                    style_rng or Random(),
                )
        else:
            output_stream.write(
                _compose_frame(result, show_path=True, style=DEFAULT_STYLE),
            )
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
    result: MazeResult,
    screen: TerminalScreen,
    stderr: TextIO,
    input_stream: TextIO | None,
    style_rng: Random,
) -> None:
    show_path = True
    style = DEFAULT_STYLE
    regeneration_count = 0
    current_result = result
    while True:
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
            else:
                config = new_config
                regeneration_count = new_count
                current_result = new_result
                status = (
                    "Reloaded config and re-generated maze."
                    if config_changed
                    else "Re-generated maze."
                )
                if new_result.warning is not None:
                    status = f"{status} Warning: {new_result.warning}"
            screen.render_frame(
                _compose_frame(
                    current_result,
                    show_path,
                    style,
                    status=status,
                ),
            )
            continue
        if choice == "2":
            show_path = not show_path
            screen.render_frame(
                _compose_frame(
                    current_result,
                    show_path,
                    style,
                    status=f"Shortest path {'shown' if show_path else 'hidden'}.",
                ),
            )
            continue
        if choice == "3":
            style = random_maze_style(style_rng, style)
            screen.render_frame(
                _compose_frame(
                    current_result,
                    show_path,
                    style,
                    status="Changed maze colours and style.",
                ),
            )
            continue
        if choice == "4":
            screen.render_frame(
                _compose_frame(
                    current_result,
                    show_path,
                    style,
                    status="Goodbye.",
                ),
            )
            return
        status = "invalid choice: use 1, 2, 3, or 4"
        stderr.write(f"{status}\n")
        screen.render_frame(
            _compose_frame(
                current_result,
                show_path,
                style,
                status=status,
            ),
        )


def _render(result: MazeResult, show_path: bool, style: MazeStyle) -> str:
    return LineRenderer(style.palette, style.colours).render(
        result,
        show_path=show_path,
    )


def _compose_frame(
    result: MazeResult,
    show_path: bool,
    style: MazeStyle,
    status: str = "",
) -> str:
    rendered = _render(result, show_path, style)
    return TerminalFrameComposer().compose(
        FrameState(
            maze_text=rendered,
            show_path=show_path,
            status=status,
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
