from pathlib import Path


def test_private_documentation_is_gitignored() -> None:
    gitignore = Path(".gitignore").read_text(encoding="utf-8")

    assert "doc/" in gitignore
    assert ".doc/" in gitignore


def test_maze_analyzer_script_exists() -> None:
    assert Path("scripts/maze_analyzer.py").is_file()


def test_mandatory_project_files_exist() -> None:
    mandatory_files = (
        "a_maze_ing.py",
        "config.txt",
        "Makefile",
        "LICENSE.md",
        "README.md",
        "pyproject.toml",
    )
    for file_path in mandatory_files:
        assert Path(file_path).is_file()


def test_package_directories_exist() -> None:
    package_files = (
        "mazegen/__init__.py",
        "ui/__init__.py",
    )
    for file_path in package_files:
        assert Path(file_path).is_file()


def test_legacy_main_entrypoint_removed() -> None:
    assert not Path("main.py").exists()
