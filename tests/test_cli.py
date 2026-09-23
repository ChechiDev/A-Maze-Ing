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

    exit_code = main([str(config_path)], stdout, stderr)

    assert exit_code == 0
    assert output_path.is_file()
    assert "E" in stdout.getvalue()
    assert "S" in stdout.getvalue()
    assert "warning:" in stderr.getvalue()


def test_cli_respects_output_path(tmp_path: Path) -> None:
    output_path = tmp_path / "custom-output.txt"
    config_path = _write_config(tmp_path, output_path)

    exit_code = main([str(config_path)], StringIO(), StringIO())

    assert exit_code == 0
    assert output_path.is_file()


def test_cli_reports_output_write_error(tmp_path: Path) -> None:
    output_path = tmp_path / "missing" / "maze.txt"
    config_path = _write_config(tmp_path, output_path)
    stderr = StringIO()

    exit_code = main([str(config_path)], StringIO(), stderr)

    assert exit_code != 0
    assert "could not write output file" in stderr.getvalue()


def test_cli_module_import_does_not_execute_cli() -> None:
    assert callable(main)


def test_cli_module_does_not_use_input() -> None:
    assert "input(" not in Path(ui.cli.__file__).read_text(encoding="utf-8")


def test_entrypoint_import_does_not_execute_cli() -> None:
    assert a_maze_ing.main is main


def test_entrypoint_script_with_valid_config_writes_output_and_renders(
    tmp_path: Path,
) -> None:
    output_path = tmp_path / "maze.txt"
    config_path = _write_config(tmp_path, output_path)

    completed = subprocess.run(
        [sys.executable, "a_maze_ing.py", str(config_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0
    assert output_path.is_file()
    assert "E" in completed.stdout
    assert "S" in completed.stdout


def test_entrypoint_script_without_arguments_returns_error() -> None:
    completed = subprocess.run(
        [sys.executable, "a_maze_ing.py"],
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode != 0
    assert "usage" in completed.stderr


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
