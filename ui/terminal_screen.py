"""Terminal screen control helpers for stable frame redraws."""

import sys
from typing import TextIO


CLEAR_SCREEN = "\x1b[2J"
MOVE_HOME = "\x1b[H"
HIDE_CURSOR = "\x1b[?25l"
SHOW_CURSOR = "\x1b[?25h"
CLEAR_LINE = "\x1b[2K"


class TerminalScreen:
    """Write ANSI terminal control sequences to redraw full frames."""

    def __init__(self, stream: TextIO | None = None) -> None:
        """Create a screen controller using the provided output stream."""
        self._stream = stream or sys.stdout
        self._cleared = False
        self._previous_line_count = 0
        self._previous_width = 0

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
        """Render a complete terminal frame in-place."""
        self.clear_once()
        self.move_home()
        frame = self._padded_frame(text)
        self._stream.write(frame)
        self._stream.flush()

    def _padded_frame(self, text: str) -> str:
        lines = text.split("\n")
        width = max((len(line) for line in lines), default=0)
        target_width = max(width, self._previous_width)
        padded_lines = [line.ljust(target_width) for line in lines]
        current_line_count = len(lines)

        if self._previous_line_count > current_line_count:
            remaining = self._previous_line_count - current_line_count
            padded_lines.extend(CLEAR_LINE for _ in range(remaining))

        self._previous_line_count = current_line_count
        self._previous_width = width
        return "\n".join(padded_lines)
