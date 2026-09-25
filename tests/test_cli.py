from collections.abc import Callable
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
    assert "━" in completed.stdout
    assert "┃" in completed.stdout
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
    assert "━" in stdout.getvalue()


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
    assert "●" not in _maze_of(frames[2])


def test_cli_menu_action_toggle_path_hides_and_restores_path(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "2\n2\n4\n")

    assert "●" in _maze_of(frames[0])
    assert "●" not in _maze_of(frames[1])
    assert _maze_of(frames[2]) == _maze_of(frames[0])
    assert "Path: shown" in frames[2]


def test_cli_menu_action_toggle_path_keeps_the_same_maze(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "2\n4\n")

    assert _maze_of(frames[1]) == _maze_of(frames[0]).replace("●", " ")


def test_cli_menu_action_rotate_changes_appearance_every_time(
    tmp_path: Path,
) -> None:
    frames = _run_menu(tmp_path, "3\n3\n3\n4\n")

    mazes = [_maze_of(frame) for frame in frames[:4]]

    assert all(before != after for before, after in zip(mazes, mazes[1:]))


def test_cli_menu_action_rotate_uses_ansi_colours(tmp_path: Path) -> None:
    frames = _run_menu(tmp_path, "3\n4\n")

    assert "\x1b[38;5;" not in frames[0]
    assert "\x1b[38;5;" in _maze_of(frames[1])


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
    assert "●" not in _maze_of(frames[2])


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
            )
        ),
        encoding="utf-8",
    )
    return config_path


def _run_menu(
    tmp_path: Path,
    choices: str,
    style_rng: Random | None = None,
) -> list[str]:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main(
        [str(config_path)],
        stdout,
        StringIO(),
        StringIO(choices),
        style_rng=style_rng,
    )

    assert exit_code == 0
    return _frames(stdout.getvalue())


def _frames(output: str) -> list[str]:
    for code in ("\x1b[?25l", "\x1b[?25h", "\x1b[2J", "\x1b[2K"):
        output = output.replace(code, "")
    return [
        "\n".join(line.rstrip() for line in chunk.splitlines()).strip("\n")
        for chunk in output.split("\x1b[H")
        if chunk.strip()
    ]


def _maze_of(frame: str) -> str:
    return frame.split("\n\nPath:", maxsplit=1)[0]


def _layout_of(maze: str) -> str:
    plain = re.sub(r"\x1b\[[0-9;]*m", "", maze)
    return "".join(
        symbol if symbol in " \nES●█" else "#" for symbol in plain
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
