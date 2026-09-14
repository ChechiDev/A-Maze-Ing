import pytest

from mazegen.exceptions import (
    InvalidConfigurationError,
    InvalidMazeError,
    MazeError,
    UnreachableExitError,
)


@pytest.mark.parametrize(
    "exception_type",
    (
        MazeError,
        InvalidMazeError,
        InvalidConfigurationError,
        UnreachableExitError,
    ),
)
def test_domain_exceptions_inherit_from_exception(
    exception_type: type[Exception],
) -> None:
    assert issubclass(exception_type, Exception)


def test_specific_exceptions_inherit_from_maze_error() -> None:
    specific_exceptions = (
        InvalidMazeError,
        InvalidConfigurationError,
        UnreachableExitError,
    )

    for exception_type in specific_exceptions:
        assert issubclass(exception_type, MazeError)


@pytest.mark.parametrize(
    "exception_type",
    (
        MazeError,
        InvalidMazeError,
        InvalidConfigurationError,
        UnreachableExitError,
    ),
)
def test_domain_exceptions_preserve_messages(
    exception_type: type[Exception],
) -> None:
    message = "domain error message"

    assert str(exception_type(message)) == message
