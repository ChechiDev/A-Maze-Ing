from ui.frame import FrameState, TerminalFrameComposer


ACTIONS_BLOCK = (
    "Actions:\n"
    "1. Re-generate a new maze\n"
    "2. Show / Hide the shortest path\n"
    "3. Rotate wall colours\n"
    "4. Quit\n"
    "Choice?"
)


def test_terminal_frame_preserves_rendered_maze_text() -> None:
    maze_text = "┌─┐\n│S│\n└─┘\n"

    frame = TerminalFrameComposer().compose(_state(maze_text=maze_text))

    assert "┌─┐\n│S│\n└─┘" in frame


def test_terminal_frame_includes_menu_actions_in_order() -> None:
    frame = TerminalFrameComposer().compose(_state())

    assert ACTIONS_BLOCK in frame


def test_terminal_frame_places_actions_after_maze_and_path_state() -> None:
    frame = TerminalFrameComposer().compose(_state(maze_text="MAZE\n"))

    assert frame.index("MAZE") < frame.index("Path:")
    assert frame.index("Path:") < frame.index("Actions:")


def test_terminal_frame_places_status_after_actions() -> None:
    frame = TerminalFrameComposer().compose(_state(status="Hello."))

    assert frame.index("Choice?") < frame.index("Status: Hello.")
    assert frame.endswith("Status: Hello.\n")


def test_terminal_frame_actions_do_not_change_with_state() -> None:
    composer = TerminalFrameComposer()

    shown = composer.compose(_state(show_path=True, status="a"))
    hidden = composer.compose(_state(show_path=False, status="b"))

    assert ACTIONS_BLOCK in shown
    assert ACTIONS_BLOCK in hidden


def test_terminal_frame_reflects_shown_path_state() -> None:
    frame = TerminalFrameComposer().compose(_state(show_path=True))

    assert "Path: shown" in frame


def test_terminal_frame_reflects_hidden_path_state() -> None:
    frame = TerminalFrameComposer().compose(_state(show_path=False))

    assert "Path: hidden" in frame


def test_terminal_frame_includes_status_when_provided() -> None:
    frame = TerminalFrameComposer().compose(_state(status="Re-generated maze."))

    assert "Status: Re-generated maze." in frame


def test_terminal_frame_omits_status_when_empty() -> None:
    frame = TerminalFrameComposer().compose(_state(status=""))

    assert "Status:" not in frame


def test_terminal_frame_composer_import_has_no_cli_side_effects() -> None:
    assert TerminalFrameComposer.__module__ == "ui.frame"
    assert FrameState.__module__ == "ui.frame"


def test_terminal_frame_snapshot() -> None:
    frame = TerminalFrameComposer().compose(
        FrameState(
            maze_text="┌───┐\n│E S│\n└───┘\n",
            show_path=False,
            status="Invalid choice.",
        )
    )

    assert frame == (
        "┌───┐\n"
        "│E S│\n"
        "└───┘\n"
        "\n"
        "Path: hidden\n"
        "\n"
        "Actions:\n"
        "1. Re-generate a new maze\n"
        "2. Show / Hide the shortest path\n"
        "3. Rotate wall colours\n"
        "4. Quit\n"
        "Choice?\n"
        "\n"
        "Status: Invalid choice.\n"
    )


def _state(
    maze_text: str = "maze\n",
    show_path: bool = True,
    status: str = "",
) -> FrameState:
    return FrameState(
        maze_text=maze_text,
        show_path=show_path,
        status=status,
    )
