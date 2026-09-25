from io import StringIO

import pytest

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


def test_context_manager_hides_and_restores_cursor_on_normal_exit() -> None:
    stream = FakeStream()

    with TerminalScreen(stream):
        assert stream.getvalue() == HIDE_CURSOR

    assert stream.getvalue() == HIDE_CURSOR + SHOW_CURSOR


def test_context_manager_returns_same_screen_instance() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    with screen as active_screen:
        assert active_screen is screen


def test_context_manager_restores_cursor_when_exception_is_raised() -> None:
    stream = FakeStream()

    with pytest.raises(RuntimeError):
        with TerminalScreen(stream):
            raise RuntimeError("handled error")

    assert stream.getvalue() == HIDE_CURSOR + SHOW_CURSOR


def test_context_manager_flushes_stream_on_exit() -> None:
    stream = FakeStream()

    with TerminalScreen(stream):
        pass

    assert stream.flush_count == 1


def test_render_frame_first_frame_clears_moves_writes_and_flushes() -> None:
    stream = FakeStream()

    TerminalScreen(stream).render_frame("frame")

    assert stream.getvalue() == CLEAR_SCREEN + MOVE_HOME + MOVE_HOME + "frame\n"
    assert stream.flush_count == 1


def test_render_frame_second_frame_moves_home_without_full_clear() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.render_frame("first")
    screen.render_frame("second")

    assert stream.getvalue().count(CLEAR_SCREEN) == 1
    assert stream.getvalue().endswith(MOVE_HOME + "second\n")
    assert stream.flush_count == 2


def test_render_frame_pads_shorter_lines_and_clears_leftover_lines() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.render_frame("longer\nsecond")
    screen.render_frame("tiny")

    assert stream.getvalue().endswith(
        MOVE_HOME + "tiny  \n" + CLEAR_LINE + "\n",
    )


def test_render_frame_pads_by_visible_width_ignoring_colours() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.render_frame("\x1b[38;5;196mab\x1b[0m\nabcd")

    assert "\x1b[38;5;196mab\x1b[0m  \nabcd\n" in stream.getvalue()


def test_render_frame_clears_leftovers_of_wider_uncoloured_frame() -> None:
    stream = FakeStream()
    screen = TerminalScreen(stream)

    screen.render_frame("abcd")
    screen.render_frame("\x1b[38;5;196mab\x1b[0m")

    assert stream.getvalue().endswith(
        MOVE_HOME + "\x1b[38;5;196mab\x1b[0m  \n",
    )


def test_stream_injection_avoids_real_stdout() -> None:
    stream = FakeStream()

    TerminalScreen(stream).render_frame("injected")

    assert "injected" in stream.getvalue()


def test_terminal_screen_import_has_no_cli_side_effects() -> None:
    assert TerminalScreen.__module__ == "ui.terminal_screen"
