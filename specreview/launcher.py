"""A stable path for the MCP server.

Herdr installs every update of a plugin into a new numbered directory, so agents
cannot register ``bin/spec-review-mcp`` by its installed path. The plugin config
directory survives updates, so the plugin writes a small launcher there. The
launcher runs the newest installed copy and falls back to the plugin root that was
recorded last (this is what makes ``herdr plugin link`` work too).
"""
from __future__ import annotations

import os

LAUNCHER_NAME = "spec-review-mcp"
ROOT_FILE_NAME = "mcp-root"

LAUNCHER = """#!/bin/sh
# Written by the Spec Review plugin: runs its MCP server, whichever directory Herdr
# installed the latest version into. Register this path in your agent.
here=$(cd "$(dirname "$0")" && pwd)
plugins=$(cd "$here/../.." && pwd)
latest=$(ls -td "$plugins"/github-installations/andpeicunha.spec-review-*/*/checkout 2>/dev/null | head -n 1)
if [ -z "$latest" ] && [ -f "$here/mcp-root" ]; then
  latest=$(cat "$here/mcp-root")
fi
if [ -z "$latest" ] || [ ! -x "$latest/bin/spec-review-mcp" ]; then
  echo "spec-review plugin is not installed (run: herdr plugin install andpeicunha/herdr-spec-review)" >&2
  exit 1
fi
exec "$latest/bin/spec-review-mcp" "$@"
"""


def _write_if_changed(path: str, text: str, mode: int) -> None:
    try:
        with open(path, encoding="utf-8") as source:
            if source.read() == text and os.access(path, os.X_OK) == bool(mode & 0o100):
                return
    except OSError:
        pass
    temporary = f"{path}.tmp"
    with open(temporary, "w", encoding="utf-8") as out:
        out.write(text)
    os.chmod(temporary, mode)
    os.replace(temporary, path)


def ensure_launcher(config_dir: str, plugin_root: str = "") -> str:
    """Create or refresh the launcher in ``config_dir``; return its path."""
    os.makedirs(config_dir, exist_ok=True)
    if plugin_root:
        _write_if_changed(os.path.join(config_dir, ROOT_FILE_NAME), plugin_root + "\n", 0o644)
    path = os.path.join(config_dir, LAUNCHER_NAME)
    _write_if_changed(path, LAUNCHER, 0o755)
    return path
