"""An artifact as selectable blocks that keep their real 1-based file line ranges."""
from __future__ import annotations

import os
from dataclasses import dataclass, field

from .ainotes import Note, body_text, locate_note, pending_notes
from .markdown import split_markdown_blocks


@dataclass
class Block:
    text: str
    code: str  # Code role from split_code_fences: "", "fence", "code", "code_gap".
    start: int
    end: int


@dataclass
class Document:
    path: str
    text: str
    body_lines: list[str]
    blocks: list[Block]
    notes: list[Note]
    # Block index for each pending note; None when its text can no longer be found.
    note_blocks: dict[str, int | None] = field(default_factory=dict)
    mtime: float = 0.0

    def block_source(self, index: int) -> str:
        block = self.blocks[index]
        return "\n".join(self.body_lines[block.start - 1 : block.end])


def _matches(fragment: str, line: str) -> bool:
    if not line:
        return False
    item = fragment.lstrip("• ").strip()
    return fragment.startswith(line) or line.startswith(fragment) or bool(item and item in line)


def map_block_lines(texts: list[tuple[str, str]], body_lines: list[str]) -> list[Block]:
    """Find each block's first source line in order, then end it before the next block."""
    starts: list[int] = []
    pointer = 0
    for text, _code in texts:
        fragment = text.splitlines()[0].strip() if text.strip() else ""
        found = None
        for index in range(pointer, len(body_lines)):
            if _matches(fragment, body_lines[index].strip()):
                found = index
                break
        start = found if found is not None else min(pointer, max(0, len(body_lines) - 1))
        starts.append(start + 1)
        pointer = start + 1 if found is not None else pointer

    blocks: list[Block] = []
    for index, (text, code) in enumerate(texts):
        start = starts[index]
        limit = starts[index + 1] - 1 if index + 1 < len(starts) else len(body_lines)
        end = max(start, limit)
        while end > start and not body_lines[end - 1].strip():
            end -= 1
        if code or (index + 1 < len(starts) and starts[index + 1] == start):
            # A code line is one source line; several blocks can also share one
            # source line (e.g. "a • b • c").
            end = start
        blocks.append(Block(text, code, start, end))
    return blocks


def block_for_line(blocks: list[Block], line: int) -> int | None:
    for index, block in enumerate(blocks):
        if block.start <= line <= block.end:
            return index
    candidates = [index for index, block in enumerate(blocks) if block.start <= line]
    return candidates[-1] if candidates else None


def load_document(path: str) -> Document:
    with open(path, encoding="utf-8") as source:
        text = source.read()
    body = body_text(text)
    body_lines = body.split("\n")
    if body_lines and body_lines[-1] == "":
        body_lines.pop()
    blocks = map_block_lines(split_markdown_blocks(body), body_lines)
    notes = pending_notes(text)
    note_blocks = {}
    for note in notes:
        line = locate_note(note, body_lines)
        note_blocks[note.note_id] = block_for_line(blocks, line) if line else None
    return Document(path, text, body_lines, blocks, notes, note_blocks, os.path.getmtime(path))
