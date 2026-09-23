"""Command-line flow for generating and rendering mazes."""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from mazegen import MazeError
from mazegen.encoder import format_maze_output
from mazegen.generator import MazeGenerator, MazeOptions, MazeResult
from ui.config_loader import MazeConfig, load_config
from ui.frame import FrameState, TerminalFrameComposer
from ui.renderer import AsciiRenderer, RenderPalette


SUCCESS = 0
FAILURE = 1
_WALL_STYLES = ("#", "▓", "█")


def main(
    argv: Sequence[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
    input_stream: TextIO | None = None,
    interactive: bool = True,
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
        output_stream.write(
            _compose_frame(result, show_path=True, wall_style_index=0),
        )
        if result.warning is not None:
            error_stream.write(f"warning: {result.warning}\n")
        if interactive:
            _run_interactions(config, result, output_stream, error_stream, input_stream)
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
    config: MazeConfig,
    result: MazeResult,
    stdout: TextIO,
    stderr: TextIO,
    input_stream: TextIO | None,
) -> None:
    show_path = True
    wall_style_index = 0
    regeneration_count = 0
    current_result = result
    while True:
        choice = _read_choice(input_stream)
        if choice == "1":
            regeneration_count += 1
            current_result = _generate(config, regeneration_count)
            _write_output_file(config.output_file, current_result)
            stdout.write(
                _compose_frame(
                    current_result,
                    show_path,
                    wall_style_index,
                    status="Re-generated maze.",
                ),
            )
            continue
        if choice == "2":
            show_path = not show_path
            stdout.write(
                _compose_frame(
                    current_result,
                    show_path,
                    wall_style_index,
                    status=f"Shortest path {'shown' if show_path else 'hidden'}.",
                ),
            )
            continue
        if choice == "3":
            wall_style_index = (wall_style_index + 1) % len(_WALL_STYLES)
            stdout.write(
                _compose_frame(
                    current_result,
                    show_path,
                    wall_style_index,
                    status="Rotated wall style.",
                ),
            )
            continue
        if choice == "4":
            stdout.write("Goodbye.\n")
            return
        status = "invalid choice: use 1, 2, 3, or 4"
        stderr.write(f"{status}\n")
        stdout.write(
            _compose_frame(
                current_result,
                show_path,
                wall_style_index,
                status=status,
            ),
        )


def _render(result: MazeResult, show_path: bool, wall_style_index: int) -> str:
    palette = RenderPalette(wall=_WALL_STYLES[wall_style_index])
    return AsciiRenderer(palette).render(result, show_path=show_path)


def _compose_frame(
    result: MazeResult,
    show_path: bool,
    wall_style_index: int,
    status: str = "",
) -> str:
    rendered = _render(result, show_path, wall_style_index)
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
