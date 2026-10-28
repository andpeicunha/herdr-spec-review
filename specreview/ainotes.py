"""Read and write AI Notes inside Markdown files.

The format is a contract shared with the ai-notes-md VS Code extension (v0.0.17):
the same heading, agent instructions, note fields, and 1-based ``Lines``. Notes
are temporary: a resolved note is deleted, and when no pending note is left the
whole ``# AI Notes`` section goes away.
"""
from __future__ import annotations

import os
import re
import tempfile
import time
from dataclasses import dataclass

AI_NOTES_HEADING = "# AI Notes"
INSTRUCTIONS_HEADING = "## Instructions for AI Agents"
INSTRUCTIONS = "\n".join(
    [
        INSTRUCTIONS_HEADING,
        "",
        "When analyzing this document, treat every note with `Status: pending` as an active request.",
        "",
        "After resolving a note:",
        "",
        "1. Delete the note block entirely from the document — do not keep it as a historical record.",
        "2. If no `Status: pending` notes remain after deletion, also remove the entire `# AI Notes` section,",
        "   including the `---` separator above it and this `## Instructions for AI Agents` block.",
        "",
        "Unresolved notes must remain unchanged with `Status: pending`.",
    ]
)
NOT_SPECIFIED = "Not specified."
_FIELDS = ("Status", "Lines", "Selected Text", "Human Comment", "Expected AI Action", "Created At")
_NOTE_HEADING_RE = re.compile(r"^## (NOTE-\d{3,})\s*$", re.M)
_FIELD_RE = re.compile(r"^(" + "|".join(re.escape(f) for f in _FIELDS) + r"):\s*(.*)$")


@dataclass
class Note:
    note_id: str
    status: str
    start_line: int
    end_line: int
    selected_text: str
    human_comment: str
    expected_action: str = NOT_SPECIFIED
    created_at: str = ""

    @property
    def pending(self) -> bool:
        return self.status.lower() == "pending"


def split_document(text: str) -> tuple[str, str]:
    """Return (body, notes section); the ``---`` separator belongs to neither."""
    matches = list(re.finditer(rf"^{re.escape(AI_NOTES_HEADING)}\s*$", text, re.M))
    if not matches:
        return text, ""
    start = matches[-1].start()
    body = text[:start].rstrip()
    if body.endswith("---"):
        body = body[:-3].rstrip()
    return body + "\n", text[start:]


def body_text(text: str) -> str:
    """The document without its AI Notes section, as shown in the reader."""
    return split_document(text)[0]


def parse_notes(text: str) -> list[Note]:
    """Parse every ``## NOTE-XXX`` block of the document's AI Notes section."""
    section = split_document(text)[1]
    headings = list(_NOTE_HEADING_RE.finditer(section))
    notes = []
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(section)
        block = section[heading.end() : end]
        # Stop at the next level-2 heading that is not a note (e.g. instructions).
        other = re.search(r"^## ", block, re.M)
        if other:
            block = block[: other.start()]
        notes.append(_parse_note(heading.group(1), block))
    return notes


def _parse_note(note_id: str, block: str) -> Note:
    fields: dict[str, list[str]] = {}
    current = None
    for line in block.splitlines():
        match = _FIELD_RE.match(line)
        if match:
            current = match.group(1)
            fields[current] = [match.group(2)] if match.group(2).strip() else []
        elif current:
            fields[current].append(line)

    def value(name: str) -> str:
        return "\n".join(fields.get(name, [])).strip()

    start, end = 0, 0
    lines = re.match(r"(\d+)\s*-\s*(\d+)", value("Lines"))
    if lines:
        start, end = int(lines.group(1)), int(lines.group(2))
    selected = "\n".join(
        re.sub(r"^> ?", "", line) for line in value("Selected Text").splitlines()
    )
    return Note(
        note_id=note_id,
        status=value("Status").splitlines()[0].strip() if value("Status") else "",
        start_line=start,
        end_line=end,
        selected_text=selected,
        human_comment=value("Human Comment"),
        expected_action=value("Expected AI Action") or NOT_SPECIFIED,
        created_at=value("Created At"),
    )


def pending_notes(text: str) -> list[Note]:
    return [note for note in parse_notes(text) if note.pending]


def next_note_id(text: str) -> str:
    numbers = [int(match) for match in re.findall(r"## NOTE-(\d{3,})\b", text)]
    return f"NOTE-{(max(numbers) + 1 if numbers else 1):03d}"


def format_note(note: Note) -> str:
    quoted = "\n".join(f"> {line}" for line in note.selected_text.splitlines() or [""])
    return "\n".join(
        [
            f"## {note.note_id}",
            "",
            f"Status: {note.status}",
            "",
            f"Lines: {note.start_line}-{note.end_line}",
            "",
            "Selected Text:",
            "",
            quoted,
            "",
            "Human Comment:",
            "",
            note.human_comment,
            "",
            "Expected AI Action:",
            "",
            note.expected_action or NOT_SPECIFIED,
            "",
            "Created At:",
            "",
            note.created_at,
        ]
    )


def append_note(text: str, note: Note) -> str:
    """Append a note the same way ai-notes-md does (creating the section if needed)."""
    prefix = "" if text.endswith("\n") else "\n"
    has_section = re.search(rf"^{re.escape(AI_NOTES_HEADING)}\s*$", text, re.M)
    has_instructions = re.search(rf"^{re.escape(INSTRUCTIONS_HEADING)}\s*$", text, re.M)
    if has_section:
        if not has_instructions:
            return f"{text}{prefix}\n{INSTRUCTIONS}\n\n{format_note(note)}\n"
        return f"{text}{prefix}\n{format_note(note)}\n"
    return f"{text}{prefix}\n---\n\n{AI_NOTES_HEADING}\n\n{INSTRUCTIONS}\n\n{format_note(note)}\n"


def remove_note(text: str, note_id: str) -> str:
    """Delete one note; drop the whole section when no pending note is left."""
    body, section = split_document(text)
    if not section:
        return text
    pattern = re.compile(
        rf"^## {re.escape(note_id)}\s*$.*?(?=^## |\Z)", re.M | re.S
    )
    section = pattern.sub("", section).rstrip() + "\n"
    if not any(note.pending for note in parse_notes(body + "\n" + section)):
        return body
    return f"{body}\n---\n\n{section}"


def now_stamp(moment: float | None = None) -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.localtime(moment))


def write_atomic(path: str, text: str) -> None:
    """Write via a temp file in the same directory, then rename over the target."""
    directory = os.path.dirname(os.path.abspath(path))
    handle, temp_path = tempfile.mkstemp(prefix=".spec-review-", dir=directory)
    try:
        with os.fdopen(handle, "w", encoding="utf-8") as out:
            out.write(text)
        if os.path.exists(path):
            os.chmod(temp_path, os.stat(path).st_mode & 0o777)
        os.replace(temp_path, path)
    except BaseException:
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise


def add_note_to_file(
    path: str,
    start_line: int,
    end_line: int,
    selected_text: str,
    human_comment: str,
    expected_action: str = NOT_SPECIFIED,
) -> Note:
    """Re-read the file, append a pending note, and write it atomically."""
    with open(path, encoding="utf-8") as source:
        text = source.read()
    note = Note(
        note_id=next_note_id(text),
        status="pending",
        start_line=start_line,
        end_line=end_line,
        selected_text=selected_text,
        human_comment=human_comment.strip(),
        expected_action=expected_action,
        created_at=now_stamp(),
    )
    write_atomic(path, append_note(text, note))
    return note


def locate_note(note: Note, body_lines: list[str]) -> int | None:
    """Return the 1-based line the note refers to, re-anchoring by its selected text."""
    first = next((line.strip() for line in note.selected_text.splitlines() if line.strip()), "")
    if not first:
        return note.start_line or None
    if 0 < note.start_line <= len(body_lines) and first in body_lines[note.start_line - 1]:
        return note.start_line
    matches = [index + 1 for index, line in enumerate(body_lines) if first in line]
    if not matches:
        return None
    return min(matches, key=lambda line: abs(line - note.start_line))
