from pathlib import Path

import pytest

from ui.config_loader import parse_config_lines


CONFIG_PATH = Path("config.txt")
REQUIRED_KEYS = {
    "WIDTH",
    "HEIGHT",
    "ENTRY",
    "EXIT",
    "OUTPUT_FILE",
    "PERFECT",
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


def _is_xy_coordinate(value: str) -> bool:
    parts = value.split(",")
    return len(parts) == 2 and all(part.isdecimal() for part in parts)
