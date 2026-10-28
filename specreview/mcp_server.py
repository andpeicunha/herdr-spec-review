"""Minimal MCP server over stdio (newline-delimited JSON-RPC 2.0), no dependencies.

The agent starts this process, so it inherits the agent's ``HERDR_PANE_ID`` and cwd:
``open_artifact`` opens the reader next to that agent, and the handoff goes back to it.
"""
from __future__ import annotations

import json
import os
import sys

from . import __version__
from .ainotes import pending_notes
from .cli import open_artifact
from .discovery import list_artifacts, open_changes, pending_count, repo_root, change_pending_count

SERVER_NAME = "spec-review"
DEFAULT_PROTOCOL = "2025-06-18"
INSTRUCTIONS = (
    "Spec Review opens OpenSpec SDD artifacts (proposal, design, specs, tasks) in a Herdr "
    "reader where the user leaves AI Notes. Only call open_artifact when the user asks to "
    "open, read, or review an artifact in Spec Review. When the user later sends notes, "
    "process the pending AI Notes in the file as its `# AI Notes` section instructs."
)

TOOLS = [
    {
        "name": "list_open_changes",
        "description": "List open OpenSpec changes (not archived) in a repository and all of its git worktrees, with branch and pending AI Notes count.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "repo": {"type": "string", "description": "Any path inside the repository. Defaults to the current directory."}
            },
        },
    },
    {
        "name": "list_artifacts",
        "description": "List the artifacts of one OpenSpec change in review order, with pending AI Notes per file.",
        "inputSchema": {
            "type": "object",
            "properties": {"change_path": {"type": "string", "description": "Path to openspec/changes/<change>."}},
            "required": ["change_path"],
        },
    },
    {
        "name": "open_artifact",
        "description": "Open an OpenSpec artifact in the Spec Review reader pane, next to this agent's Herdr pane. Only call this when the user asks to open or review the artifact.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to proposal.md, design.md, tasks.md, or specs/**/spec.md of an open change."}},
            "required": ["path"],
        },
    },
    {
        "name": "pending_notes",
        "description": "List the pending AI Notes of an artifact: id, lines, selected text, and the human comment.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "Path to the Markdown artifact."}},
            "required": ["path"],
        },
    },
]


class ToolError(Exception):
    pass


def _path(arguments: dict, key: str) -> str:
    value = arguments.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ToolError(f"Missing required argument: {key}")
    return os.path.abspath(os.path.expanduser(value))


def tool_list_open_changes(arguments: dict) -> str:
    start = os.path.abspath(os.path.expanduser(arguments.get("repo") or os.getcwd()))
    root = repo_root(start)
    if not root:
        raise ToolError(f"Not inside a git repository: {start}")
    changes = open_changes(root)
    if not changes:
        return f"No open OpenSpec changes in {root}."
    lines = [f"Open changes in {root}:"]
    for change in changes:
        notes = change_pending_count(change.path)
        branch = change.worktree.branch or "(no branch)"
        lines.append(f"- {change.name} [{branch}] {change.path}" + (f" ({notes} pending note(s))" if notes else ""))
    return "\n".join(lines)


def tool_list_artifacts(arguments: dict) -> str:
    change_path = _path(arguments, "change_path")
    if not os.path.isdir(change_path):
        raise ToolError(f"Change directory not found: {change_path}")
    artifacts = list_artifacts(change_path)
    if not artifacts:
        return f"No artifacts in {change_path}."
    lines = [f"Artifacts of {os.path.basename(change_path)}:"]
    for rel in artifacts:
        notes = pending_count(os.path.join(change_path, rel))
        lines.append(f"- {os.path.join(change_path, rel)}" + (f" ({notes} pending note(s))" if notes else ""))
    return "\n".join(lines)


def tool_open_artifact(arguments: dict) -> str:
    ok, message = open_artifact(_path(arguments, "path"))
    if not ok:
        raise ToolError(message)
    return message


def tool_pending_notes(arguments: dict) -> str:
    path = _path(arguments, "path")
    try:
        with open(path, encoding="utf-8") as source:
            notes = pending_notes(source.read())
    except OSError as error:
        raise ToolError(f"Cannot read {path}: {error.strerror}") from error
    if not notes:
        return f"No pending AI Notes in {path}."
    lines = [f"{len(notes)} pending AI Note(s) in {path}:"]
    for note in notes:
        quoted = note.selected_text.replace("\n", " ")[:120]
        lines.append(f"- {note.note_id} (lines {note.start_line}-{note.end_line}) on \"{quoted}\": {note.human_comment}")
    return "\n".join(lines)


HANDLERS = {
    "list_open_changes": tool_list_open_changes,
    "list_artifacts": tool_list_artifacts,
    "open_artifact": tool_open_artifact,
    "pending_notes": tool_pending_notes,
}


def handle(message: dict) -> dict | None:
    """Answer one JSON-RPC message; notifications (no id) get no response."""
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}
    if message_id is None:
        return None
    if method == "initialize":
        result = {
            "protocolVersion": params.get("protocolVersion") or DEFAULT_PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": __version__},
            "instructions": INSTRUCTIONS,
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        handler = HANDLERS.get(params.get("name"))
        if handler is None:
            return _error(message_id, -32602, f"Unknown tool: {params.get('name')}")
        try:
            text, is_error = handler(params.get("arguments") or {}), False
        except ToolError as error:
            text, is_error = str(error), True
        result = {"content": [{"type": "text", "text": text}], "isError": is_error}
    else:
        return _error(message_id, -32601, f"Method not found: {method}")
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def _error(message_id, code: int, text: str) -> dict:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": text}}


def serve(stdin=sys.stdin, stdout=sys.stdout) -> None:
    for line in stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
        except ValueError:
            response = _error(None, -32700, "Parse error")
        else:
            response = handle(message) if isinstance(message, dict) else _error(None, -32600, "Invalid request")
        if response is not None:
            stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            stdout.flush()


if __name__ == "__main__":
    serve()
