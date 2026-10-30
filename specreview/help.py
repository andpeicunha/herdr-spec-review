"""Keyboard shortcuts of the reader and the lists, and the pure layout of the help modal."""
from __future__ import annotations

import textwrap

# (section title, [(keys, what they do)])
Section = tuple[str, list[tuple[str, str]]]

READER_HELP: list[Section] = [
    (
        "Move",
        [
            ("↑ ↓ / k j", "previous / next block"),
            ("Alt+↑ Alt+↓ / PgUp PgDn", "half a page up / down"),
            ("u d", "half a page up / down"),
            ("g G", "first / last block"),
            ("n N", "next / previous heading"),
        ],
    ),
    (
        "Notes",
        [
            ("c", "add a note on this block"),
            ("C", "edit a saved note on this block (1-9 picks one when there are several)"),
        ],
    ),
    (
        "While writing a note",
        [
            ("Ctrl+S", "save into the file (empty text on an edited note deletes it)"),
            ("Enter", "new line"),
            ("Ctrl+U", "clear the current line"),
            ("Esc", "cancel (asks first when you changed it)"),
        ],
    ),
    (
        "View",
        [
            ("+ -", "zoom in / out"),
            ("0", "reset the zoom"),
            ("R", "reload the file after it changed"),
        ],
    ),
    (
        "Other",
        [
            ("s", "send the pending notes to the agent (asks first), then close"),
            ("q Esc", "close; pending notes stay in the file"),
            ("?", "show this list"),
        ],
    ),
]


def picker_help(with_repos: bool) -> list[Section]:
    """Shortcuts of the lists (changes, artifacts, repositories)."""
    keys = [
        ("↑ ↓ / k j", "move"),
        ("Enter", "open"),
        ("/", "filter by text (type, then Enter; Esc clears)"),
    ]
    if with_repos:
        keys.append(("r", "choose another repository"))
    keys += [("Esc", "back"), ("q", "quit"), ("?", "show this list")]
    return [("Lists", keys)]


def help_layout(sections: list[Section], width: int) -> tuple[list[tuple[str, str, str]], int]:
    """Rows of the help modal and the text indent, for a modal ``width`` columns wide.

    Each row is ``(kind, keys, text)``: kind is "section", "key", or "blank". Keys and
    their text share a row when the keys fit in half of the width; otherwise the text
    goes on the rows below the keys, so no key is ever cut.
    """
    width = max(10, width)
    longest = max((len(keys) for _title, items in sections for keys, _text in items), default=0)
    stacked = longest > width // 2
    indent = 2 if stacked else longest + 2
    text_width = max(1, width - indent - (2 if stacked else 0))
    rows: list[tuple[str, str, str]] = []
    for index, (title, items) in enumerate(sections):
        if index:
            rows.append(("blank", "", ""))
        rows.append(("section", title, ""))
        for keys, text in items:
            lines = textwrap.wrap(text, text_width) or [""]
            if stacked:
                rows.append(("key", keys, ""))
                rows.extend(("key", "", line) for line in lines)
            else:
                rows.append(("key", keys, lines[0]))
                rows.extend(("key", "", line) for line in lines[1:])
    return rows, indent


def clamp_scroll(offset: int, total: int, visible: int) -> int:
    """Keep a scroll offset inside the rows that exist."""
    return max(0, min(offset, total - visible))
