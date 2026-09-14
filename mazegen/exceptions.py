"""Domain exceptions raised by the reusable maze generator package."""


class MazeError(Exception):
    """Base class for all maze generation domain errors."""


class InvalidMazeError(MazeError):
    """Raised when a maze structure violates domain invariants."""


class InvalidConfigurationError(MazeError):
    """Raised when configuration values cannot produce a valid maze."""


class UnreachableExitError(MazeError):
    """Raised when no valid path exists between entry and exit cells."""
