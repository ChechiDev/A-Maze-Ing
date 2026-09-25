from ui.frame import FrameState, TerminalFrameComposer


def test_terminal_frame_includes_title() -> None:
    frame = TerminalFrameComposer().compose(_state())

    assert "=== A-Maze-ing ===" in frame


def test_terminal_frame_preserves_rendered_maze_text() -> None:
    maze_text = "┌─┐\n│S│\n└─┘\n"

    frame = TerminalFrameComposer().compose(_state(maze_text=maze_text))

    assert "┌─┐\n│S│\n└─┘" in frame


def test_terminal_frame_includes_legend() -> None:
    frame = TerminalFrameComposer().compose(_state())

    assert "Legend: E = entry, S = exit, ·/. = path, 4 = 42 cell" in frame


def test_terminal_frame_includes_menu_actions() -> None:
    frame = TerminalFrameComposer().compose(_state())

    assert "Actions:" in frame
    assert "1. Re-generate a new maze" in frame
    assert "2. Show / Hide the shortest path" in frame
    assert "3. Rotate wall colours" in frame
    assert "4. Quit" in frame
    assert "Choice? " in frame


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
        "=== A-Maze-ing ===\n"
        "\n"
        "┌───┐\n"
        "│E S│\n"
        "└───┘\n"
        "\n"
        "Legend: E = entry, S = exit, ·/. = path, 4 = 42 cell\n"
        "\n"
        "Path: hidden\n"
        "\n"
        "Actions:\n"
        "1. Re-generate a new maze\n"
        "2. Show / Hide the shortest path\n"
        "3. Rotate wall colours\n"
        "4. Quit\n"
        "Choice? \n"
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
