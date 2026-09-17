"""Configuration parsing helpers for the application layer."""

from collections.abc import Iterable
from pathlib import Path
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)

from mazegen.grid import Position


class MazeConfig(BaseModel):
    """Validated maze configuration loaded from KEY=VALUE settings."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid")

    width: int = Field(alias="WIDTH", gt=0)
    height: int = Field(alias="HEIGHT", gt=0)
    entry: Position = Field(alias="ENTRY")
    exit: Position = Field(alias="EXIT")
    output_file: str = Field(alias="OUTPUT_FILE", min_length=1)
    perfect: bool = Field(alias="PERFECT")
    seed: int | None = Field(default=None, alias="SEED")

    @field_validator("entry", "exit", mode="before")
    @classmethod
    def _parse_position(cls, value: object) -> Position:
        """Parse a public x,y coordinate into a Position."""
        if isinstance(value, Position):
            return value
        if not isinstance(value, str):
            raise ValueError("coordinate must use x,y format")
        parts = [part.strip() for part in value.split(",")]
        if len(parts) != 2:
            raise ValueError("coordinate must use x,y format")
        try:
            x, y = (int(part) for part in parts)
        except ValueError as error:
            raise ValueError("coordinate must contain integer values") from error
        return Position(x, y)

    @field_validator("perfect", mode="before")
    @classmethod
    def _parse_bool(cls, value: object) -> bool:
        """Parse explicit True/False strings into booleans."""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            normalized_value = value.strip().lower()
            if normalized_value == "true":
                return True
            if normalized_value == "false":
                return False
        raise ValueError("PERFECT must be True or False")

    @field_validator("output_file")
    @classmethod
    def _validate_output_file(cls, value: str) -> str:
        """Validate and normalize the output file path value."""
        stripped_value = value.strip()
        if not stripped_value:
            raise ValueError("OUTPUT_FILE must not be empty")
        return stripped_value

    @model_validator(mode="after")
    def _validate_positions(self) -> Self:
        """Validate entry and exit against configured grid bounds."""
        if not self._in_bounds(self.entry):
            raise ValueError("ENTRY must be inside the maze bounds")
        if not self._in_bounds(self.exit):
            raise ValueError("EXIT must be inside the maze bounds")
        if self.entry == self.exit:
            raise ValueError("ENTRY and EXIT must be different")
        return self

    def _in_bounds(self, position: Position) -> bool:
        """Return whether a position is inside configured bounds."""
        return 0 <= position.x < self.width and 0 <= position.y < self.height


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


def load_config(path: str | Path) -> MazeConfig:
    """Load and validate a maze configuration file."""
    config_path = Path(path)
    try:
        entries = parse_config_lines(_read_config_lines(config_path))
        return MazeConfig.model_validate(entries)
    except ValidationError as error:
        message = _validation_error_message(error)
        raise ValueError(f"invalid configuration: {message}") from error
    except OSError as error:
        message = _file_error_message(config_path, error)
        raise ValueError(message) from error


def _read_config_lines(path: Path) -> list[str]:
    """Read configuration file lines as UTF-8 text."""
    return path.read_text(encoding="utf-8").splitlines()


def _validation_error_message(error: ValidationError) -> str:
    """Return a compact human-readable Pydantic validation message."""
    first_error = error.errors()[0]
    location = ".".join(str(part) for part in first_error["loc"])
    return f"{location}: {first_error['msg']}"


def _file_error_message(path: Path, error: OSError) -> str:
    """Return a clear message for configuration file read failures."""
    if isinstance(error, FileNotFoundError):
        return f"configuration file not found: {path}"
    return f"could not read configuration file {path}: {error}"


def _parse_config_line(line: str, line_number: int) -> tuple[str, str]:
    """Parse one non-empty, non-comment KEY=VALUE line."""
    if "=" not in line:
        raise ValueError(f"invalid config syntax on line {line_number}: missing '='")
    key, value = line.split("=", maxsplit=1)
    stripped_key = key.strip()
    if not stripped_key:
        raise ValueError(f"invalid config syntax on line {line_number}: empty key")
    return stripped_key, value.strip()
