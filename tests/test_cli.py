from collections.abc import Callable
from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from random import Random
import re
import subprocess
import sys
from typing import TextIO, cast

import a_maze_ing
import ui.cli
from ui.cli import main
from ui.renderer import (
    DEFAULT_STYLE,
    LINE_STYLES,
    LineRenderPalette,
    MazeStyle,
    random_maze_style,
)


STYLE_SEED = 0
_PALETTE = LineRenderPalette()
PATH_SYMBOLS = {
    _PALETTE.path_horizontal,
    _PALETTE.path_vertical,
    _PALETTE.path_top_left,
    _PALETTE.path_top_right,
    _PALETTE.path_bottom_left,
    _PALETTE.path_bottom_right,
}


def test_cli_without_arguments_returns_error() -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main([], stdout, stderr)

    assert exit_code != 0
    assert stdout.getvalue() == ""
    assert "usage" in stderr.getvalue()


def test_cli_with_too_many_arguments_returns_error(tmp_path: Path) -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main(
        [str(tmp_path / "one.txt"), str(tmp_path / "two.txt")],
        stdout,
        stderr,
    )

    assert exit_code != 0
    assert "usage" in stderr.getvalue()


def test_cli_with_missing_config_returns_error(tmp_path: Path) -> None:
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main([str(tmp_path / "missing.txt")], stdout, stderr)

    assert exit_code != 0
    assert "configuration file not found" in stderr.getvalue()


def test_cli_with_invalid_syntax_returns_error(tmp_path: Path) -> None:
    config_path = tmp_path / "config.txt"
    config_path.write_text("WIDTH\n", encoding="utf-8")
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main([str(config_path)], stdout, stderr)

    assert exit_code != 0
    assert "invalid config syntax" in stderr.getvalue()


def test_cli_with_invalid_configuration_returns_error(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(
        tmp_path,
        output_path,
        entry="0,0",
        exit="0,0",
    )
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main([str(config_path)], stdout, stderr)

    assert exit_code != 0
    assert "invalid configuration" in stderr.getvalue()


def test_cli_with_valid_config_writes_output_and_renders_maze(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main([str(config_path)], stdout, stderr, interactive=False)

    assert exit_code == 0
    assert output_path.is_file()
    _assert_complete_frame(stdout.getvalue())
    assert "Path: shown" in stdout.getvalue()
    assert "E" in stdout.getvalue()
    assert "S" in stdout.getvalue()
    assert "━" in stdout.getvalue()
    assert "┃" in stdout.getvalue()
    assert "#" not in stdout.getvalue()
    _assert_hex_output_file(output_path)
    assert "warning:" in stderr.getvalue()


def test_cli_respects_output_path(tmp_path: Path) -> None:
    output_path = tmp_path / "custom-output.txt"
    config_path = _write_config(tmp_path, output_path)

    exit_code = main([str(config_path)], StringIO(), StringIO(), interactive=False)

    assert exit_code == 0
    assert output_path.is_file()


def test_cli_reports_output_write_error(tmp_path: Path) -> None:
    output_path = tmp_path / "missing" / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stderr = StringIO()

    exit_code = main([str(config_path)], StringIO(), stderr, interactive=False)

    assert exit_code != 0
    assert "could not write output file" in stderr.getvalue()


def test_cli_module_import_does_not_execute_cli() -> None:
    assert callable(main)


def test_cli_module_contains_the_only_allowed_input_call() -> None:
    assert "input(" in Path(ui.cli.__file__).read_text(encoding="utf-8")


def test_entrypoint_import_does_not_execute_cli() -> None:
    assert a_maze_ing.main is main


def test_entrypoint_script_with_valid_config_writes_output_and_renders(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)

    completed = subprocess.run(
        [sys.executable, "a_maze_ing.py", str(config_path)],
        input="4\n",
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert output_path.is_file()
    assert "E" in completed.stdout
    assert "S" in completed.stdout
    assert any(
        style.horizontal in completed.stdout for style in LINE_STYLES
    )
    assert "Actions:" in completed.stdout
    assert "┏" not in output_path.read_text(encoding="utf-8")
    assert "━" not in output_path.read_text(encoding="utf-8")


def test_entrypoint_script_without_arguments_returns_error() -> None:
    completed = subprocess.run(
        [sys.executable, "a_maze_ing.py"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "usage" in completed.stderr


def test_cli_interactive_quit_returns_success(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO("4\n"))

    assert exit_code == 0
    assert output_path.is_file()
    _assert_complete_frame(stdout.getvalue())
    assert "Status: Goodbye." in stdout.getvalue()
    assert "\x1b[2J" in stdout.getvalue()
    assert "\x1b[H" in stdout.getvalue()
    assert "\x1b[?25l" in stdout.getvalue()
    assert stdout.getvalue().endswith("\x1b[?25h")


def test_cli_interactive_toggle_path_rerenders(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO("2\n4\n"))

    assert exit_code == 0
    assert "Shortest path hidden" in stdout.getvalue()
    assert "Path: hidden" in stdout.getvalue()
    assert stdout.getvalue().count("Actions:") == 3
    assert stdout.getvalue().count("\x1b[2J") == 1


def test_cli_interactive_regenerate_rewrites_output(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)

    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO("1\n4\n"))

    assert exit_code == 0
    assert output_path.is_file()
    assert output_path.read_text(encoding="utf-8")
    _assert_hex_output_file(output_path)
    assert "Status: Re-generated maze." in stdout.getvalue()
    assert stdout.getvalue().count("Actions:") == 3
    assert any(style.horizontal in stdout.getvalue() for style in LINE_STYLES)


def test_cli_interactive_regenerate_reloads_edited_config(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()
    input_stream = _EditingInput(
        ["1\n", "4\n"],
        lambda: _write_config(tmp_path, output_path, exit="2,3"),
    )

    exit_code = main(
        [str(config_path)],
        stdout,
        StringIO(),
        cast(TextIO, input_stream),
    )

    assert exit_code == 0
    assert "Status: Reloaded config and re-generated maze." in stdout.getvalue()
    assert output_path.read_text(encoding="utf-8").splitlines()[-2] == "2,3"


def test_cli_interactive_regenerate_with_invalid_config_keeps_running(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    previous_output = ""
    stdout = StringIO()
    stderr = StringIO()

    def break_config() -> None:
        nonlocal previous_output
        previous_output = output_path.read_text(encoding="utf-8")
        _write_config(tmp_path, output_path, exit="9,9")

    input_stream = _EditingInput(["1\n", "4\n"], break_config)

    exit_code = main(
        [str(config_path)],
        stdout,
        stderr,
        cast(TextIO, input_stream),
    )

    assert exit_code == 0
    assert "kept previous maze" in stderr.getvalue()
    assert "Status: error: invalid configuration" in stdout.getvalue()
    assert "Status: Goodbye." in stdout.getvalue()
    assert output_path.read_text(encoding="utf-8") == previous_output


def test_cli_interactive_rotate_wall_style_rerenders(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO("3\n4\n"))

    assert exit_code == 0
    assert "Status: Changed maze colours and style." in stdout.getvalue()
    assert stdout.getvalue().count("Actions:") == 3
    assert "\x1b[38;5;" in stdout.getvalue()


def test_cli_interactive_toggle_path_does_not_rewrite_output(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)

    first_exit_code = main(
        [str(config_path)],
        StringIO(),
        StringIO(),
        interactive=False,
    )
    before = output_path.read_text(encoding="utf-8")
    second_exit_code = main(
        [str(config_path)],
        StringIO(),
        StringIO(),
        StringIO("2\n4\n"),
    )

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert output_path.read_text(encoding="utf-8") == before


def test_cli_interactive_rotate_style_does_not_rewrite_output(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)

    first_exit_code = main(
        [str(config_path)],
        StringIO(),
        StringIO(),
        interactive=False,
    )
    before = output_path.read_text(encoding="utf-8")
    second_exit_code = main(
        [str(config_path)],
        StringIO(),
        StringIO(),
        StringIO("3\n4\n"),
    )

    assert first_exit_code == 0
    assert second_exit_code == 0
    assert output_path.read_text(encoding="utf-8") == before


def test_cli_interactive_invalid_choice_continues(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main([str(config_path)], stdout, stderr, StringIO("x\n4\n"))

    assert exit_code == 0
    assert "invalid choice" in stderr.getvalue()
    assert "Status: invalid choice: use 1, 2, 3, or 4" in stdout.getvalue()
    assert stdout.getvalue().count("Actions:") == 3
    assert stdout.getvalue().endswith("\x1b[?25h")


def test_cli_interactive_eof_quits_cleanly(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO(""))

    assert exit_code == 0
    assert "Status: Goodbye." in stdout.getvalue()
    assert stdout.getvalue().endswith("\x1b[?25h")


def test_cli_menu_action_regenerate_changes_the_maze(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "1\n1\n4\n")

    mazes = [_maze_of(frame) for frame in frames[:3]]

    assert len(set(mazes)) == 3


def test_cli_menu_action_regenerate_keeps_hidden_path(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "2\n1\n4\n")

    assert "Path: hidden" in frames[2]
    assert not _has_path(_maze_of(frames[2]), _styles(1)[0])


def test_cli_menu_action_toggle_path_hides_and_restores_path(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "2\n2\n4\n")

    style = _styles(1)[0]
    assert _has_path(_maze_of(frames[0]), style)
    assert not _has_path(_maze_of(frames[1]), style)
    assert _maze_of(frames[2]) == _maze_of(frames[0])
    assert "Path: shown" in frames[2]


def test_cli_menu_action_toggle_path_keeps_the_same_maze(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "2\n4\n")

    shown = _plain(_maze_of(frames[0])).splitlines()
    hidden = _plain(_maze_of(frames[1])).splitlines()

    assert len(shown) == len(hidden)
    for shown_line, hidden_line in zip(shown, hidden):
        assert len(shown_line) == len(hidden_line)
        for shown_symbol, hidden_symbol in zip(shown_line, hidden_line):
            if shown_symbol != hidden_symbol:
                assert shown_symbol in PATH_SYMBOLS
                assert hidden_symbol == " "


def test_cli_menu_action_rotate_changes_appearance_every_time(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "3\n3\n3\n4\n")

    mazes = [_maze_of(frame) for frame in frames[:4]]

    assert all(before != after for before, after in zip(mazes, mazes[1:]))


def test_cli_menu_action_rotate_uses_ansi_colours(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "3\n4\n")

    assert "\x1b[38;5;" in _maze_of(frames[1])


def test_cli_starts_with_random_colours_and_style(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "4\n")

    assert "\x1b[38;5;" in _maze_of(frames[0])


def test_cli_start_style_is_reproducible_with_seeded_rng(
    tmp_path: Path,
) -> None:
    first = _run_menu(tmp_path, "4\n", style_rng=Random(5))
    second = _run_menu(tmp_path, "4\n", style_rng=Random(5))

    assert first == second


def test_cli_start_style_changes_between_runs(tmp_path: Path) -> None:
    starts = {
        _maze_of(_run_menu(tmp_path, "4\n", style_rng=Random(seed))[0])
        for seed in range(10)
    }

    assert len(starts) > 1


def test_cli_non_interactive_output_stays_uncoloured(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    main([str(config_path)], stdout, StringIO(), interactive=False)

    assert "\x1b[" not in stdout.getvalue()
    assert DEFAULT_STYLE.palette.horizontal in stdout.getvalue()


def test_cli_menu_action_rotate_keeps_the_same_maze_layout(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "3\n3\n4\n")

    layouts = {_layout_of(_maze_of(frame)) for frame in frames[:3]}

    assert len(layouts) == 1


def test_cli_menu_action_rotate_is_reproducible_with_seeded_rng(
    tmp_path: Path,
) -> None:
    first = _run_menu(tmp_path, "3\n3\n4\n", style_rng=Random(7))
    second = _run_menu(tmp_path, "3\n3\n4\n", style_rng=Random(7))

    assert first == second


def test_cli_menu_action_rotate_keeps_path_visibility(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "2\n3\n4\n")

    assert "Path: hidden" in frames[2]
    assert not _has_path(_maze_of(frames[2]), _styles(2)[1])


def test_cli_menu_action_quit_renders_goodbye_and_stops(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "4\n1\n")

    assert len(frames) == 2
    assert frames[-1].endswith("Status: Goodbye.")


def test_cli_menu_accepts_choice_with_surrounding_spaces(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "  2  \n4\n")

    assert "Status: Shortest path hidden." in frames[1]


def test_cli_menu_invalid_choice_keeps_the_same_maze(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "9\n\n4\n")

    assert _maze_of(frames[1]) == _maze_of(frames[0])
    assert _maze_of(frames[2]) == _maze_of(frames[0])
    assert "Status: invalid choice: use 1, 2, 3, or 4" in frames[2]


def test_cli_menu_every_frame_shows_the_actions(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "1\n2\n3\nx\n4\n")

    assert len(frames) == 6
    for frame in frames:
        _assert_complete_frame(frame)


def test_cli_animates_path_cell_by_cell_with_configured_delay(
    tmp_path: Path,
) -> None:
    run = _run_animated(tmp_path, "4\n", path_delay="0.05")

    assert run.sleeps
    assert set(run.sleeps) == {0.05}
    assert len(run.draws) == len(run.sleeps)
    assert all(symbol in PATH_SYMBOLS for _, _, symbol in run.draws)


def test_cli_path_animation_draws_cells_in_path_order(tmp_path: Path) -> None:
    run = _run_animated(tmp_path, "4\n")

    rows_and_columns = [(row, column) for row, column, _ in run.draws]
    final_maze = _plain(_maze_of(_frames(run.output)[-1])).splitlines()

    assert len(set(rows_and_columns)) == len(rows_and_columns)
    for row, column, symbol in run.draws:
        assert final_maze[row - 1][column - 1] == symbol


def test_cli_path_animation_starts_from_maze_without_path(
    tmp_path: Path,
) -> None:
    run = _run_animated(tmp_path, "4\n")

    first_frame = _frames(run.output)[0]

    assert not _has_path(_maze_of(first_frame), _styles(1)[0])
    assert "Path: shown" in first_frame


def test_cli_path_animation_never_clears_the_screen_again(
    tmp_path: Path,
) -> None:
    run = _run_animated(tmp_path, "1\n2\n2\n4\n")

    assert run.output.count("\x1b[2J") == 1


def test_cli_path_animation_runs_on_regenerate_and_show_only(
    tmp_path: Path,
) -> None:
    start = len(_run_animated(tmp_path, "4\n").sleeps)

    assert len(_run_animated(tmp_path, "1\n4\n").sleeps) > start
    assert len(_run_animated(tmp_path, "2\n4\n").sleeps) == start
    assert len(_run_animated(tmp_path, "2\n2\n4\n").sleeps) > start
    assert len(_run_animated(tmp_path, "3\nx\n4\n").sleeps) == start


def test_cli_path_animation_is_disabled_with_zero_delay(
    tmp_path: Path,
) -> None:
    run = _run_animated(tmp_path, "1\n4\n", path_delay="0")

    assert run.sleeps == []
    assert run.draws == []


def test_cli_does_not_animate_when_output_is_not_a_terminal(
    tmp_path: Path,
) -> None:
    sleeps: list[float] = []
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)

    main(
        [str(config_path)],
        StringIO(),
        StringIO(),
        StringIO("1\n4\n"),
        sleep=sleeps.append,
    )

    assert sleeps == []


def test_cli_error_status_clears_when_no_input_arrives_in_time(
    tmp_path: Path,
) -> None:
    waits: list[float] = []

    def no_input(timeout: float) -> bool:
        waits.append(timeout)
        return False

    frames = _run_menu(tmp_path, "x\n4\n", input_ready=no_input)

    assert "Status: invalid choice" in frames[1]
    assert "Status:" not in frames[2]
    assert _maze_of(frames[2]) == _maze_of(frames[1])
    assert waits == [ui.cli.ERROR_STATUS_SECONDS]


def test_cli_error_status_timeout_is_between_three_and_five_seconds() -> None:
    assert 3 <= ui.cli.ERROR_STATUS_SECONDS <= 5


def test_cli_config_error_status_clears_after_timeout(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()
    input_stream = _EditingInput(
        ["1\n", "4\n"],
        lambda: _write_config(tmp_path, output_path, exit="9,9"),
    )

    main(
        [str(config_path)],
        stdout,
        StringIO(),
        cast(TextIO, input_stream),
        input_ready=lambda timeout: False,
    )
    frames = _frames(stdout.getvalue())

    assert "EXIT must be inside the maze bounds" in frames[1]
    assert "Status:" not in frames[2]


def test_cli_error_status_stays_when_user_answers_in_time(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "x\n4\n", input_ready=lambda timeout: True)

    assert len(frames) == 3
    assert "Status: Goodbye." in frames[2]


def test_cli_only_waits_with_timeout_after_errors(tmp_path: Path) -> None:
    waits: list[float] = []

    def ready(timeout: float) -> bool:
        waits.append(timeout)
        return True

    _run_menu(tmp_path, "1\n2\n3\n4\n", input_ready=ready)

    assert waits == []


def test_input_only_exists_in_ui_cli() -> None:
    forbidden_paths = [
        Path("a_maze_ing.py"),
        *Path("mazegen").glob("**/*.py"),
        *Path("ui/renderer").glob("**/*.py"),
    ]

    for path in forbidden_paths:
        assert "input(" not in path.read_text(encoding="utf-8")


class _EditingInput:
    """Input stream that runs an edit callback before the first line."""

    def __init__(self, lines: list[str], edit: Callable[[], object]) -> None:
        self._lines = StringIO("".join(lines))
        self._edit: Callable[[], object] | None = edit

    def readline(self) -> str:
        if self._edit is not None:
            self._edit()
            self._edit = None
        return self._lines.readline()


def _write_config(
    tmp_path: Path,
    output_path: Path,
    *,
    entry: str = "0,0",
    exit: str = "3,3",
    extra: tuple[str, ...] = (),
) -> Path:
    config_path = tmp_path / "config.txt"
    config_path.write_text(
        "\n".join(
            (
                "WIDTH=4",
                "HEIGHT=4",
                f"ENTRY={entry}",
                f"EXIT={exit}",
                f"OUTPUT_FILE={output_path}",
                "PERFECT=True",
                "SEED=42",
                *extra,
            )
        ),
        encoding="utf-8",
    )
    return config_path


class _TerminalOutput(StringIO):
    """Output stream that reports being an interactive terminal."""

    def isatty(self) -> bool:
        return True


@dataclass
class _AnimatedRun:
    output: str
    sleeps: list[float]
    draws: list[tuple[int, int, str]]


def _run_animated(
    tmp_path: Path,
    choices: str,
    path_delay: str = "0.01",
) -> _AnimatedRun:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(
        tmp_path,
        output_path,
        extra=(f"PATH_DELAY={path_delay}",),
    )
    stdout = _TerminalOutput()
    sleeps: list[float] = []

    exit_code = main(
        [str(config_path)],
        stdout,
        StringIO(),
        StringIO(choices),
        style_rng=Random(STYLE_SEED),
        sleep=sleeps.append,
    )

    assert exit_code == 0
    output = stdout.getvalue()
    draws = [
        (int(row), int(column), symbol)
        for row, column, symbol in re.findall(
            r"\x1b\[(\d+);(\d+)H(?:\x1b\[[0-9;]*m)?(.)",
            output,
        )
    ]
    return _AnimatedRun(output=output, sleeps=sleeps, draws=draws)


def _run_menu(
    tmp_path: Path,
    choices: str,
    style_rng: Random | None = None,
    input_ready: Callable[[float], bool] | None = None,
) -> list[str]:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main(
        [str(config_path)],
        stdout,
        StringIO(),
        StringIO(choices),
        style_rng=style_rng or Random(STYLE_SEED),
        input_ready=input_ready,
    )

    assert exit_code == 0
    return _frames(stdout.getvalue())


def _frames(output: str) -> list[str]:
    for code in (
        "\x1b[?25l",
        "\x1b[?25h",
        "\x1b[2J",
        "\x1b[J",
        "\x1b[?2026h",
        "\x1b[?2026l",
    ):
        output = output.replace(code, "")
    output = re.sub(
        r"\x1b\[\d+;\d+H(?:\x1b\[[0-9;]*m)?[^\x1b](?:\x1b\[0m)?",
        "",
        output,
    )
    return [
        "\n".join(line.rstrip() for line in chunk.splitlines()).strip("\n")
        for chunk in output.split("\x1b[H")
        if chunk.strip()
    ]


def _maze_of(frame: str) -> str:
    return frame.split("\n\nPath:", maxsplit=1)[0]


def _styles(count: int) -> list[MazeStyle]:
    """Return the styles the CLI shows when seeded with STYLE_SEED."""
    rng = Random(STYLE_SEED)
    styles = []
    style = DEFAULT_STYLE
    for _ in range(count):
        style = random_maze_style(rng, style)
        styles.append(style)
    return styles


def _has_path(maze: str, style: MazeStyle) -> bool:
    return f"\x1b[38;5;{style.colours.path}m" in maze


def _plain(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _layout_of(maze: str) -> str:
    return "".join(
        symbol if symbol in " \nES█" else "#" for symbol in _plain(maze)
    )


def _assert_complete_frame(output: str) -> None:
    assert "Actions:" in output
    assert "1. Re-generate a new maze" in output
    assert "2. Show / Hide the shortest path" in output
    assert "3. Rotate wall colours" in output
    assert "4. Quit" in output
    assert "Choice?" in output


def _assert_hex_output_file(output_path: Path) -> None:
    output = output_path.read_text(encoding="utf-8")
    grid_text, footer_text = output.split("\n\n", maxsplit=1)
    grid_lines = grid_text.splitlines()
    footer_lines = footer_text.splitlines()

    assert grid_lines
    assert all(line for line in grid_lines)
    assert all(set(line) <= set("0123456789abcdef") for line in grid_lines)
    assert len(footer_lines) >= 2
    assert _is_coordinate(footer_lines[0])
    assert _is_coordinate(footer_lines[1])
    for symbol in "┌─│┏━┃●█":
        assert symbol not in output


def _is_coordinate(value: str) -> bool:
    parts = value.split(",")
    return len(parts) == 2 and all(part.isdigit() for part in parts)
