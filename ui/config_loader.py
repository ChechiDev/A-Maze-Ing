"""Configuration parsing helpers for the application layer."""

from collections.abc import Iterable


def parse_config_lines(lines: Iterable[str]) -> dict[str, str]:
    """Parse KEY=VALUE configuration lines into a string dictionary."""
    entries: dict[str, str] = {}
    for line_number, line in enumerate(lines, start=1):
        stripped_line = line.strip()
        if not stripped_line or stripped_line.startswith("#"):
            continue
        key, value = _parse_config_line(stripped_line, line_number)
        if key in entries:
            raise ValueError(
                f"invalid config syntax on line {line_number}: "
                f"duplicate key '{key}'"
            )
        entries[key] = value
    return entries


def _parse_config_line(line: str, line_number: int) -> tuple[str, str]:
    """Parse one non-empty, non-comment KEY=VALUE line."""
    if "=" not in line:
        raise ValueError(f"invalid config syntax on line {line_number}: missing '='")
    key, value = line.split("=", maxsplit=1)
    stripped_key = key.strip()
    if not stripped_key:
        raise ValueError(f"invalid config syntax on line {line_number}: empty key")
    return stripped_key, value.strip()
