from io import StringIO

from ui.terminal_screen import (
    CLEAR_LINE,
    CLEAR_SCREEN,
    HIDE_CURSOR,
    MOVE_HOME,
    SHOW_CURSOR,
    TerminalScreen,
)


class FakeStream(StringIO):
    """String stream that records flush calls."""

    def __init__(self) -> None:
        super().__init__()
        self.flush_count = 0

    def flush(self) -> None:
        self.flush_count += 1


def test_clear_once_emits_clear_screen_and_move_home() -> None:
    stream = FakeStream()

    TerminalScreen(stream).clear_once()

    assert stream.getvalue() == CLEAR_SCREEN + MOVE_HOME


def test_clear_once_does_not_emit_duplicate_clear_screen() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.clear_once()
    screen.clear_once()

    assert stream.getvalue() == CLEAR_SCREEN + MOVE_HOME


def test_move_home_emits_move_home_sequence() -> None:
    stream = FakeStream()

    TerminalScreen(stream).move_home()

    assert stream.getvalue() == MOVE_HOME


def test_cursor_visibility_sequences_are_emitted() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.hide_cursor()
    screen.show_cursor()

    assert stream.getvalue() == HIDE_CURSOR + SHOW_CURSOR


def test_render_frame_first_frame_clears_moves_writes_and_flushes() -> None:
    stream = FakeStream()

    TerminalScreen(stream).render_frame("frame")

    assert stream.getvalue() == CLEAR_SCREEN + MOVE_HOME + MOVE_HOME + "frame"
    assert stream.flush_count == 1


def test_render_frame_second_frame_moves_home_without_full_clear() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.render_frame("first")
    screen.render_frame("second")

    assert stream.getvalue().count(CLEAR_SCREEN) == 1
    assert stream.getvalue().endswith(MOVE_HOME + "second")
    assert stream.flush_count == 2


def test_render_frame_pads_shorter_lines_and_clears_leftover_lines() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.render_frame("longer\nsecond")
    screen.render_frame("tiny")

    assert stream.getvalue().endswith(MOVE_HOME + "tiny  \n" + CLEAR_LINE)


def test_stream_injection_avoids_real_stdout() -> None:
    stream = FakeStream()

    TerminalScreen(stream).render_frame("injected")

    assert "injected" in stream.getvalue()


def test_terminal_screen_import_has_no_cli_side_effects() -> None:
    assert TerminalScreen.__module__ == "ui.terminal_screen"
