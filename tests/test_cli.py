from io import StringIO
from pathlib import Path
import subprocess
import sys

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
    assert "=== A-Maze-ing ===" in completed.stdout


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
    assert "=== A-Maze-ing ===" in stdout.getvalue()
    _assert_complete_frame(stdout.getvalue())
    assert "Goodbye" in stdout.getvalue()


def test_cli_interactive_toggle_path_rerenders(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO("2\n4\n"))

    assert exit_code == 0
    assert "Shortest path hidden" in stdout.getvalue()
    assert "Path: hidden" in stdout.getvalue()
    assert stdout.getvalue().count("Legend:") == 2
    assert stdout.getvalue().count("Actions:") == 2
    assert stdout.getvalue().count("=== A-Maze-ing ===") == 2


def test_cli_interactive_regenerate_rewrites_output(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)

    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO("1\n4\n"))

    assert exit_code == 0
    assert output_path.is_file()
    assert output_path.read_text(encoding="utf-8")
    assert "Status: Re-generated maze." in stdout.getvalue()
    assert stdout.getvalue().count("Legend:") == 2
    assert stdout.getvalue().count("Actions:") == 2


def test_cli_interactive_rotate_wall_style_rerenders(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO("3\n4\n"))

    assert exit_code == 0
    assert "Status: Rotated wall style." in stdout.getvalue()
    assert stdout.getvalue().count("Legend:") == 2
    assert stdout.getvalue().count("Actions:") == 2
    assert "▓" in stdout.getvalue()


def test_cli_interactive_invalid_choice_continues(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()
    stderr = StringIO()

    exit_code = main([str(config_path)], stdout, stderr, StringIO("x\n4\n"))

    assert exit_code == 0
    assert "invalid choice" in stderr.getvalue()
    assert "Status: invalid choice: use 1, 2, 3, or 4" in stdout.getvalue()
    assert stdout.getvalue().count("Legend:") == 2
    assert stdout.getvalue().count("Actions:") == 2


def test_cli_interactive_eof_quits_cleanly(tmp_path: Path) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stdout = StringIO()

    exit_code = main([str(config_path)], stdout, StringIO(), StringIO(""))

    assert exit_code == 0
    assert "Goodbye" in stdout.getvalue()


def test_input_only_exists_in_ui_cli() -> None:
    forbidden_paths = [
        Path("a_maze_ing.py"),
        *Path("mazegen").glob("**/*.py"),
        *Path("ui/renderer").glob("**/*.py"),
    ]

    for path in forbidden_paths:
        assert "input(" not in path.read_text(encoding="utf-8")


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


def _assert_complete_frame(output: str) -> None:
    assert "=== A-Maze-ing ===" in output
    assert "Legend: E = entry, S = exit, ·/. = path, 4 = 42 cell" in output
    assert "Actions:" in output
    assert "1. Re-generate a new maze" in output
    assert "2. Show / Hide the shortest path" in output
    assert "3. Rotate wall colours" in output
    assert "4. Quit" in output
    assert "Choice? " in output
