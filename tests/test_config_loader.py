from pathlib import Path


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
    entries: dict[str, str] = {}
    for line in _config_lines():
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        key, value = stripped_line.split("=", maxsplit=1)
        entries[key] = value
    return entries


def test_default_config_file_exists() -> None:
    assert CONFIG_PATH.is_file()


def test_default_config_contains_required_keys() -> None:
    assert REQUIRED_KEYS <= _config_entries().keys()


def test_default_config_contains_optional_seed() -> None:
    assert "SEED" in _config_entries()


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


def _is_xy_coordinate(value: str) -> bool:
    parts = value.split(",")
    return len(parts) == 2 and all(part.isdecimal() for part in parts)
