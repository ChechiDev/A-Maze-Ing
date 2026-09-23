"""Terminal frame composition for interactive maze views."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FrameState:
    """Values needed to compose a complete terminal frame."""

    maze_text: str
    show_path: bool
    status: str = ""


class TerminalFrameComposer:
    """Compose deterministic full-screen terminal frames."""

    def compose(self, state: FrameState) -> str:
        """Return a complete terminal frame for the provided state."""
        sections = [
            "=== A-Maze-ing ===",
            _normalize_maze_text(state.maze_text),
            _legend_text(),
            _path_state_text(state.show_path),
            _actions_text(),
        ]
        if state.status:
            sections.append(f"Status: {state.status}")
        return "\n\n".join(sections) + "\n"


def _normalize_maze_text(maze_text: str) -> str:
    return maze_text.rstrip("\n")


def _legend_text() -> str:
    return "Legend: E = entry, S = exit, ·/. = path, 4 = 42 cell"


def _path_state_text(show_path: bool) -> str:
    return f"Path: {'shown' if show_path else 'hidden'}"


def _actions_text() -> str:
    return (
        "Actions:\n"
        "1. Re-generate a new maze\n"
        "2. Show / Hide the shortest path\n"
        "3. Rotate wall colours\n"
        "4. Quit"
    )
