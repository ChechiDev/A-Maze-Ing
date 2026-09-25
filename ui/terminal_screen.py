"""Terminal screen control helpers for stable frame redraws."""

import re
import sys
from types import TracebackType
from typing import Literal, Self, TextIO


CLEAR_SCREEN = "\x1b[2J"
MOVE_HOME = "\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CLEAR_BELOW = "\x1b[J"
BEGIN_SYNC = "\x1b[?2026h"
END_SYNC = "\x1b[?2026l"
_ANSI_SEQUENCE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


class TerminalScreen:
    """Write ANSI terminal control sequences to redraw full frames."""

    def __init__(self, stream: TextIO | None = None) -> None:
        """Create a screen controller using the provided output stream."""
        self._stream = stream or sys.stdout
        self._cleared = False
        self._previous_width = 0

    def __enter__(self) -> Self:
        """Hide the cursor while controlled terminal drawing is active."""
        self.hide_cursor()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> Literal[False]:
        """Restore the cursor and propagate any active exception."""
        _ = exc_type, exc, traceback
        self.show_cursor()
        self._stream.flush()
        return False

    def clear_once(self) -> None:
        """Clear the terminal screen once for this controller instance."""
        if self._cleared:
            return
        self._stream.write(CLEAR_SCREEN)
        self._stream.write(MOVE_HOME)
        self._cleared = True

    def move_home(self) -> None:
        """Move the terminal cursor to the top-left home position."""
        self._stream.write(MOVE_HOME)

    def hide_cursor(self) -> None:
        """Hide the terminal cursor."""
        self._stream.write(HIDE_CURSOR)

    def show_cursor(self) -> None:
        """Show the terminal cursor."""
        self._stream.write(SHOW_CURSOR)

    def render_frame(self, text: str) -> None:
        """Render a complete terminal frame in-place.

        The frame overwrites the previous one without clearing the screen,
        and is wrapped in a synchronized update so terminals that support it
        show it at once, without flicker. Anything left below the frame, such
        as echoed input or stray messages, is erased.
        """
        self._stream.write(BEGIN_SYNC)
        self.clear_once()
        self.move_home()
        self._stream.write(self._padded_frame(text))
        self._stream.write(CLEAR_BELOW)
        self._stream.write(END_SYNC)
        self._stream.flush()

    def draw_at(self, row: int, column: int, text: str) -> None:
        """Draw text at a zero-based screen position without a full redraw.

        Args:
            row: Zero-based screen row, counted from the top of the frame.
            column: Zero-based screen column.
            text: Text to write at that position, colour codes included.
        """
        self._stream.write(f"\x1b[{row + 1};{column + 1}H{text}")
        self._stream.flush()

    def _padded_frame(self, text: str) -> str:
        lines = text.rstrip("\n").split("\n")
        width = max((_visible_len(line) for line in lines), default=0)
        target_width = max(width, self._previous_width)
        padded_lines = [
            line + " " * (target_width - _visible_len(line)) for line in lines
        ]
        self._previous_width = width
        return "\n".join(padded_lines) + "\n"


def _visible_len(line: str) -> int:
    return len(_ANSI_SEQUENCE.sub("", line))
