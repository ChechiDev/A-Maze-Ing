"""Command-line flow for generating and rendering mazes."""

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from mazegen import MazeError
from mazegen.encoder import format_maze_output
from mazegen.generator import MazeGenerator, MazeOptions, MazeResult
from ui.config_loader import MazeConfig, load_config
from ui.renderer import AsciiRenderer


SUCCESS = 0
FAILURE = 1


def main(
    argv: Sequence[str] | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
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
        result = MazeGenerator().generate(_options_from_config(config))
        _write_output_file(config.output_file, result)
        output_stream.write(AsciiRenderer().render(result, show_path=True))
        if result.warning is not None:
            error_stream.write(f"warning: {result.warning}\n")
    except (ValueError, MazeError, OSError) as error:
        _write_error(error_stream, str(error))
        return FAILURE
    return SUCCESS


def _options_from_config(config: MazeConfig) -> MazeOptions:
    return MazeOptions(
        width=config.width,
        height=config.height,
        entry=config.entry,
        exit=config.exit,
        perfect=config.perfect,
        seed=config.seed,
    )


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
