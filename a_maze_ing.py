"""Command-line entrypoint for A-Maze-ing.

The full CLI is implemented later in `ui.cli`. This placeholder keeps the
mandatory executable file present during project setup.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence


def main(argv: Sequence[str] | None = None) -> int:
    """Validate the mandatory entrypoint shape until the CLI is implemented.

    Args:
        argv: Optional command-line arguments excluding the program name.

    Returns:
        A process exit code.
    """
    args = tuple(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python3 a_maze_ing.py config.txt")
        return 2
    print("A-Maze-ing setup placeholder: CLI implementation pending.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
