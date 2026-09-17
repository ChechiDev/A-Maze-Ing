from pathlib import Path

import pytest
from pydantic import ValidationError

from mazegen.grid import Position
from ui.config_loader import MazeConfig, parse_config_lines


CONFIG_PATH = Path("config.txt")
REQUIRED_KEYS = {
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
}


def _valid_config_entries() -> dict[str, str]:
    return {
        "WIDTH": "10",
        "HEIGHT": "10",
        "ENTRY": "0,0",
        "EXIT": "9,9",
        "OUTPUT_FILE": "maze.txt",
        "PERFECT": "False",
        "SEED": "42",
    }


def _config_lines() -> list[str]:
    return CONFIG_PATH.read_text(encoding="utf-8").splitlines()


def _config_entries() -> dict[str, str]:
    return parse_config_lines(_config_lines())


def test_default_config_file_exists() -> None:
    assert CONFIG_PATH.is_file()


def test_default_config_contains_required_keys() -> None:
    assert REQUIRED_KEYS <= _config_entries().keys()


def test_default_config_contains_optional_seed() -> None:
    assert "SEED" in _config_entries()


def test_default_config_uses_playable_mode_by_default() -> None:
    assert _config_entries()["PERFECT"] == "False"


def test_default_config_documents_seed_as_optional() -> None:
    comments = [line for line in _config_lines() if line.strip().startswith("#")]

    assert any("Optional" in line and "SEED" in line for line in comments)


def test_default_config_entries_use_key_value_format() -> None:
    for line in _config_lines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        assert "=" in stripped_line
        key, value = stripped_line.split("=", maxsplit=1)
        assert key
        assert value


def test_default_config_entries_do_not_use_inline_comments() -> None:
    for line in _config_lines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        assert "#" not in stripped_line


def test_default_config_entry_and_exit_use_public_xy_format() -> None:
    entries = _config_entries()

    assert _is_xy_coordinate(entries["ENTRY"])
    assert _is_xy_coordinate(entries["EXIT"])


def test_parse_config_lines_ignores_comments() -> None:
    assert parse_config_lines(("# ignored", "WIDTH=10")) == {"WIDTH": "10"}


def test_parse_config_lines_ignores_empty_lines() -> None:
    assert parse_config_lines(("", "   ", "HEIGHT=10")) == {"HEIGHT": "10"}


def test_parse_config_lines_trims_keys_and_values() -> None:
    assert parse_config_lines((" WIDTH = 10 ",)) == {"WIDTH": "10"}


def test_parse_config_lines_preserves_values_as_strings() -> None:
    entries = parse_config_lines(("ENTRY=0,0", "PERFECT=False"))

    assert entries["ENTRY"] == "0,0"
    assert entries["PERFECT"] == "False"


def test_parse_config_lines_rejects_line_without_separator() -> None:
    with pytest.raises(ValueError, match="missing '='"):
        parse_config_lines(("WIDTH",))


def test_parse_config_lines_rejects_empty_key() -> None:
    with pytest.raises(ValueError, match="empty key"):
        parse_config_lines(("=10",))


def test_parse_config_lines_rejects_duplicate_keys() -> None:
    with pytest.raises(ValueError, match="duplicate key 'WIDTH'"):
        parse_config_lines(("WIDTH=10", "WIDTH=20"))


def test_parse_config_lines_rejects_duplicate_keys_after_trim() -> None:
    with pytest.raises(ValueError, match="duplicate key 'WIDTH'"):
        parse_config_lines((" WIDTH = 10", "WIDTH=20"))


def test_parse_config_lines_preserves_empty_values() -> None:
    assert parse_config_lines(("OUTPUT_FILE=",)) == {"OUTPUT_FILE": ""}


def test_parse_config_lines_preserves_inline_comment_text() -> None:
    entries = parse_config_lines(("OUTPUT_FILE=maze.txt # comment",))

    assert entries["OUTPUT_FILE"] == "maze.txt # comment"


def test_parse_config_lines_parses_default_config() -> None:
    entries = parse_config_lines(_config_lines())

    assert REQUIRED_KEYS <= entries.keys()
    assert entries["PERFECT"] == "False"
    assert entries["ENTRY"] == "0,0"
    assert entries["EXIT"] == "9,9"


def test_maze_config_accepts_uppercase_config_keys() -> None:
    config = MazeConfig.model_validate(_valid_config_entries())

    assert config.width == 10
    assert config.height == 10
    assert config.entry == Position(0, 0)
    assert config.exit == Position(9, 9)
    assert config.output_file == "maze.txt"
    assert config.perfect is False
    assert config.seed == 42


def test_maze_config_accepts_missing_seed() -> None:
    entries = _valid_config_entries()
    del entries["SEED"]

    assert MazeConfig.model_validate(entries).seed is None


@pytest.mark.parametrize(
    "missing_key",
    ("WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"),
)
def test_maze_config_rejects_missing_required_keys(missing_key: str) -> None:
    entries = _valid_config_entries()
    del entries[missing_key]

    with pytest.raises(ValidationError):
        MazeConfig.model_validate(entries)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("WIDTH", "0"),
        ("HEIGHT", "0"),
        ("WIDTH", "abc"),
    ),
)
def test_maze_config_rejects_invalid_dimensions(key: str, value: str) -> None:
    entries = _valid_config_entries()
    entries[key] = value

    with pytest.raises(ValidationError):
        MazeConfig.model_validate(entries)


@pytest.mark.parametrize(
    ("key", "value"),
    (
        ("ENTRY", "10,0"),
        ("EXIT", "0,10"),
    ),
)
def test_maze_config_rejects_coordinates_outside_bounds(
    key: str,
    value: str,
) -> None:
    entries = _valid_config_entries()
    entries[key] = value

    with pytest.raises(ValidationError, match="inside the maze bounds"):
        MazeConfig.model_validate(entries)


def test_maze_config_rejects_equal_entry_and_exit() -> None:
    entries = _valid_config_entries()
    entries["EXIT"] = "0,0"

    with pytest.raises(ValidationError, match="must be different"):
        MazeConfig.model_validate(entries)


def test_maze_config_rejects_empty_output_file() -> None:
    entries = _valid_config_entries()
    entries["OUTPUT_FILE"] = ""

    with pytest.raises(ValidationError):
        MazeConfig.model_validate(entries)


def test_maze_config_rejects_blank_output_file() -> None:
    entries = _valid_config_entries()
    entries["OUTPUT_FILE"] = "   "

    with pytest.raises(ValidationError, match="OUTPUT_FILE must not be empty"):
        MazeConfig.model_validate(entries)


@pytest.mark.parametrize("value", ("True", "False", "true", "false"))
def test_maze_config_accepts_explicit_boolean_values(value: str) -> None:
    entries = _valid_config_entries()
    entries["PERFECT"] = value

    assert isinstance(MazeConfig.model_validate(entries).perfect, bool)


@pytest.mark.parametrize("value", ("maybe", "False # comment"))
def test_maze_config_rejects_invalid_boolean_values(value: str) -> None:
    entries = _valid_config_entries()
    entries["PERFECT"] = value

    with pytest.raises(ValidationError, match="PERFECT must be True or False"):
        MazeConfig.model_validate(entries)


def test_maze_config_rejects_invalid_seed() -> None:
    entries = _valid_config_entries()
    entries["SEED"] = "abc"

    with pytest.raises(ValidationError):
        MazeConfig.model_validate(entries)


@pytest.mark.parametrize("value", ("1", "1,2,3", "a,b"))
def test_maze_config_rejects_invalid_entry_format(value: str) -> None:
    entries = _valid_config_entries()
    entries["ENTRY"] = value

    with pytest.raises(ValidationError):
        MazeConfig.model_validate(entries)


def test_maze_config_rejects_unknown_keys() -> None:
    entries = _valid_config_entries()
    entries["UNKNOWN"] = "value"

    with pytest.raises(ValidationError):
        MazeConfig.model_validate(entries)


def _is_xy_coordinate(value: str) -> bool:
    parts = value.split(",")
    return len(parts) == 2 and all(part.isdecimal() for part in parts)
