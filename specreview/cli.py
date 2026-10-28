"""Command line used by the Herdr action and by agents without MCP.

    python3 -m specreview.cli launch            # Herdr action: open the picker
    python3 -m specreview.cli open <artifact>   # open the reader on one artifact
"""
from __future__ import annotations

import json
import os
import sys

from .discovery import change_for_artifact
from .herdr_io import open_reader


def context_cwd() -> str:
    try:
        context = json.loads(os.environ.get("HERDR_PLUGIN_CONTEXT_JSON", "") or "{}")
    except ValueError:
        context = {}
    return context.get("focused_pane_cwd") or context.get("workspace_cwd") or ""


def open_artifact(path: str, source_pane: str | None = None) -> tuple[bool, str]:
    """Validate ``path`` and open the reader on it next to ``source_pane``."""
    source_pane = source_pane or os.environ.get("HERDR_PANE_ID", "")
    if not source_pane:
        return False, "Not running inside a Herdr pane (HERDR_PANE_ID is not set)."
    path = os.path.abspath(os.path.expanduser(path))
    if not os.path.isfile(path):
        return False, f"File not found: {path}"
    if not change_for_artifact(path):
        return False, f"Not an artifact of an open OpenSpec change: {path}"
    ok, result = open_reader(source_pane, artifact=path, cwd=os.path.dirname(path))
    return ok, (f"Opened {path} in pane {result}" if ok else result)


def main(argv: list[str]) -> int:
    command = argv[0] if argv else "launch"
    if command == "launch":
        source_pane = os.environ.get("HERDR_PANE_ID", "")
        if not source_pane:
            print("spec-review: no source pane (invoke from inside Herdr)", file=sys.stderr)
            return 1
        ok, result = open_reader(source_pane, cwd=context_cwd())
    elif command == "open" and len(argv) == 2:
        ok, result = open_artifact(argv[1])
    else:
        print(__doc__, file=sys.stderr)
        return 2
    print(result if ok else f"spec-review: {result}", file=sys.stdout if ok else sys.stderr)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
