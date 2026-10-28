"""The curses interface: picker (repo → change → artifact) and the artifact reader."""
from __future__ import annotations

import curses
import json
import os
import termios
import traceback

from .ainotes import add_note_to_file
from .discovery import (
    candidate_repos,
    change_for_artifact,
    change_pending_count,
    list_artifacts,
    open_changes,
    pending_count,
    repo_root,
)
from .document import Document, load_document
from .editor import TextBuffer, needs_discard_confirmation
from .herdr_io import build_handoff_message, copy_text_to_clipboard, pane_cwds, send_prompt
from .layout import (
    COMMENT_PREFIX,
    ZOOM_MAX,
    ZOOM_MIN,
    build_display_rows,
    clamp_zoom,
    content_rows_available,
    editor_cursor_position,
    editor_visual_rows,
    page_target,
    scroll_position_label,
    scrollbar_thumb,
    zoom_label,
    zoom_layout,
)
from .markdown import bold_segments, comment_preview, format_markdown_lines
from .settings import setting

# Open comment box: top divider, three text rows, and the frame's bottom edge.
_COMMENT_BOX_HEIGHT = 5

_EDITOR_KEYS = {
    "\n": TextBuffer.newline,
    "\r": TextBuffer.newline,
    curses.KEY_ENTER: TextBuffer.newline,
    "\b": TextBuffer.backspace,
    "\x7f": TextBuffer.backspace,
    curses.KEY_BACKSPACE: TextBuffer.backspace,
    curses.KEY_LEFT: TextBuffer.move_left,
    curses.KEY_RIGHT: TextBuffer.move_right,
    curses.KEY_UP: TextBuffer.move_up,
    curses.KEY_DOWN: TextBuffer.move_down,
}
_ENTER_KEYS = (ord("\n"), ord("\r"), curses.KEY_ENTER)


def _safe_addnstr(
    screen: curses.window, y: int, x: int, text: str, width: int, attr: int = 0
) -> None:
    if width <= 0:
        return
    try:
        screen.addnstr(y, x, text, width, attr)
    except curses.error:
        pass


def _draw_heavy_box(window: curses.window, attr: int = 0) -> None:
    height, width = window.getmaxyx()
    if height < 2 or width < 2:
        return
    horizontal = "━" * (width - 2)
    _safe_addnstr(window, 0, 0, f"┏{horizontal}┓", width, attr)
    for y in range(1, height - 1):
        _safe_addnstr(window, y, 0, "┃", 1, attr)
        _safe_addnstr(window, y, width - 1, "┃", 1, attr)
    _safe_addnstr(window, height - 1, 0, f"┗{horizontal}┛", width, attr)


def _state_dir() -> str:
    return os.environ.get("HERDR_PLUGIN_STATE_DIR") or os.path.join(
        os.environ.get("TMPDIR", "/tmp"), "spec-review"
    )


def load_last_selection(repo: str) -> dict[str, str]:
    try:
        with open(os.path.join(_state_dir(), "last.json"), encoding="utf-8") as source:
            return json.load(source).get(repo, {})
    except (OSError, ValueError, AttributeError):
        return {}


def save_last_selection(repo: str, change: str, artifact: str) -> None:
    path = os.path.join(_state_dir(), "last.json")
    try:
        with open(path, encoding="utf-8") as source:
            data = json.load(source)
    except (OSError, ValueError):
        data = {}
    data[repo] = {"change": change, "artifact": artifact}
    try:
        os.makedirs(_state_dir(), exist_ok=True)
        with open(path, "w", encoding="utf-8") as out:
            json.dump(data, out, indent=1)
    except OSError:
        pass


def load_zoom() -> int:
    """The saved zoom level (one global level for all panes)."""
    try:
        with open(os.path.join(_state_dir(), "zoom"), encoding="utf-8") as source:
            return clamp_zoom(int(source.read().strip()))
    except (OSError, ValueError):
        return 0


def save_zoom(level: int) -> None:
    try:
        os.makedirs(_state_dir(), exist_ok=True)
        with open(os.path.join(_state_dir(), "zoom"), "w", encoding="utf-8") as out:
            out.write(str(clamp_zoom(level)))
    except OSError:
        pass


def _home(path: str) -> str:
    home = os.path.expanduser("~")
    return "~" + path[len(home) :] if path.startswith(home + os.sep) or path == home else path


class App:
    def __init__(self, source_pane: str, cwd: str = "", artifact: str = ""):
        self.source_pane = source_pane
        self.cwd = cwd
        self.artifact = artifact
        self.colors: dict[str, int] = {}
        self.status = ""
        self.zoom = load_zoom()

    # ── Shared drawing ──────────────────────────────────────────────────
    def setup_colors(self) -> None:
        if not curses.has_colors():
            return
        curses.start_color()
        curses.use_default_colors()
        color_count = getattr(curses, "COLORS", 0)
        pairs = {
            "selected": (250, 235) if color_count >= 256 else (curses.COLOR_GREEN, -1),
            "accent": (curses.COLOR_MAGENTA, -1),
            "badge": (curses.COLOR_BLACK, curses.COLOR_MAGENTA),
            "comment": (curses.COLOR_YELLOW, -1),
            "muted": (curses.COLOR_BLUE, -1),
            "footer": (curses.COLOR_WHITE, curses.COLOR_BLUE),
            "success": (curses.COLOR_GREEN, -1),
            "error": (curses.COLOR_RED, -1),
            "heading": (curses.COLOR_CYAN, -1),
            "code": (curses.COLOR_GREEN, -1),
            "quote": (curses.COLOR_MAGENTA, -1),
            "rule": (curses.COLOR_BLUE, -1),
            "bullet": (curses.COLOR_WHITE, -1),
            "table": (curses.COLOR_WHITE, -1),
            "marker": (curses.COLOR_GREEN, -1),
        }
        for number, (name, colors) in enumerate(pairs.items(), 1):
            try:
                curses.init_pair(number, *colors)
                self.colors[name] = curses.color_pair(number)
            except curses.error:
                pass

    def style(self, name: str, fallback: int = 0) -> int:
        return self.colors.get(name, fallback)

    def border_attr(self) -> int:
        return self.style("accent", curses.A_BOLD) | curses.A_BOLD

    def draw_frame(self, screen: curses.window, title: str, subtitle: str) -> None:
        width = screen.getmaxyx()[1]
        _draw_heavy_box(screen, self.border_attr())
        badge = " ✎ SPEC REVIEW "
        _safe_addnstr(
            screen, 0, 2, badge, width - 4, self.style("badge", curses.A_REVERSE) | curses.A_BOLD
        )
        _safe_addnstr(
            screen, 0, 2 + len(badge), f" {title} ", width - len(badge) - 4, self.border_attr()
        )
        _safe_addnstr(screen, 1, 1, f" {subtitle} ", width - 2, self.style("muted"))
        _safe_addnstr(screen, 2, 1, "─" * (width - 2), width - 2, self.style("muted"))

    def draw_footer(self, screen: curses.window, inner_bottom: int, footer: str) -> None:
        width = screen.getmaxyx()[1]
        inner_width = width - 2
        _safe_addnstr(screen, inner_bottom - 2, 1, "─" * inner_width, inner_width, self.style("muted"))
        attr = self.style("error") if self.status.startswith("Error") else self.style("success")
        _safe_addnstr(screen, inner_bottom - 1, 2, self.status, inner_width - 1, attr)
        _safe_addnstr(
            screen, inner_bottom, 1, footer.ljust(inner_width), inner_width,
            self.style("footer", curses.A_REVERSE),
        )

    # ── Picker ──────────────────────────────────────────────────────────
    def choose(
        self,
        screen: curses.window,
        title: str,
        subtitle: str,
        items: list[tuple[str, str]],
        initial: int = 0,
        extra_keys: str = "",
    ) -> tuple[str, int]:
        """List picker. Returns ("select", index), ("back", -1), ("quit", -1), or (key, -1)."""
        cursor = max(0, min(initial, len(items) - 1))
        query = ""
        filtering = False
        screen.timeout(-1)
        while True:
            visible = [i for i, (label, detail) in enumerate(items) if query.lower() in (label + " " + detail).lower()]
            if visible and cursor not in visible:
                cursor = visible[0]
            screen.erase()
            height, width = screen.getmaxyx()
            if height < 10 or width < 40:
                _safe_addnstr(screen, 0, 0, "Pane too small", width - 1, curses.A_BOLD)
                screen.refresh()
                if screen.getch() in (ord("q"), 27):
                    return "quit", -1
                continue
            self.draw_frame(screen, title, subtitle)
            available = height - 7
            position = visible.index(cursor) if cursor in visible else 0
            top = max(0, min(position - available // 2, max(0, len(visible) - available)))
            if not items:
                _safe_addnstr(screen, 4, 3, "Nothing found here.", width - 6, self.style("muted"))
            for y, index in enumerate(visible[top : top + available], 3):
                label, detail = items[index]
                selected = index == cursor
                attr = self.style("selected", curses.A_REVERSE) if selected else 0
                marker = "▸ " if selected else "  "
                _safe_addnstr(screen, y, 2, (marker + label).ljust(width - 4), width - 4, attr | (curses.A_BOLD if selected else 0))
                detail_x = min(width - 4, 4 + max(len(items[i][0]) for i in visible) + 2) if visible else width
                if detail and detail_x < width - 6:
                    _safe_addnstr(screen, y, detail_x, detail, width - detail_x - 3, attr or self.style("muted"))
            if filtering or query:
                self.status = f"Filter: {query}" + ("▏" if filtering else "")
            repos_hint = "r repos · " if "r" in extra_keys else ""
            footer = f" ↑/↓ move · Enter open · / filter · {repos_hint}Esc back · q quit "
            self.draw_footer(screen, height - 2, footer)
            screen.refresh()
            key = screen.get_wch()
            if filtering:
                if key in ("\n", "\r", curses.KEY_ENTER):
                    filtering = False
                    if visible:
                        self.status = ""
                        return "select", cursor
                elif key == "\x1b":
                    filtering, query = False, ""
                    self.status = ""
                elif key in (curses.KEY_BACKSPACE, "\b", "\x7f"):
                    query = query[:-1]
                elif isinstance(key, str) and key.isprintable():
                    query += key
                continue
            if key in (curses.KEY_UP, "k") and visible:
                cursor = visible[max(0, visible.index(cursor) - 1)] if cursor in visible else visible[0]
            elif key in (curses.KEY_DOWN, "j") and visible:
                cursor = visible[min(len(visible) - 1, visible.index(cursor) + 1)] if cursor in visible else visible[0]
            elif key in ("\n", "\r", curses.KEY_ENTER) and visible:
                self.status = ""
                return "select", cursor
            elif key == "/":
                filtering = True
            elif key == "\x1b":
                if query:
                    query, self.status = "", ""
                else:
                    self.status = ""
                    return "back", -1
            elif key == "q":
                return "quit", -1
            elif isinstance(key, str) and key in extra_keys:
                self.status = ""
                return key, -1

    def pick_repo(self, screen: curses.window, current: str | None) -> str | None:
        roots = [r for r in setting("SPEC_REVIEW_ROOTS").split(":") if r.strip()]
        repos = candidate_repos([self.cwd] + pane_cwds(), roots)
        items = [(os.path.basename(repo), _home(repo)) for repo in repos]
        initial = repos.index(current) if current in repos else 0
        action, index = self.choose(screen, "Repositories", "Repos with openspec/changes", items, initial)
        if action == "select":
            return repos[index]
        return None if action == "quit" else current

    def picker(self, screen: curses.window) -> None:
        repo = repo_root(self.cwd)
        if not repo or not open_changes(repo):
            repo = self.pick_repo(screen, None)
        while repo:
            last = load_last_selection(repo)
            changes = open_changes(repo)
            items = []
            for change in changes:
                where = change.worktree.branch or os.path.basename(change.worktree.path)
                if change.worktree.path != repo:
                    where += f" · {_home(change.worktree.path)}"
                notes = change_pending_count(change.path)
                items.append((change.name, where + (f" · {notes} pending note(s)" if notes else "")))
            initial = next((i for i, c in enumerate(changes) if c.path == last.get("change")), 0)
            action, index = self.choose(
                screen, os.path.basename(repo), f"Open changes in {_home(repo)}", items, initial, "r"
            )
            if action == "r":
                repo = self.pick_repo(screen, repo)
                continue
            if action != "select":
                return
            change = changes[index]
            while True:
                artifacts = list_artifacts(change.path)
                art_items = []
                for rel in artifacts:
                    notes = pending_count(os.path.join(change.path, rel))
                    art_items.append((rel, f"{notes} pending note(s)" if notes else ""))
                initial = artifacts.index(last["artifact"]) if last.get("artifact") in artifacts else 0
                action, index = self.choose(
                    screen, change.name, f"Artifacts · {change.worktree.branch or _home(change.path)}", art_items, initial
                )
                if action == "quit":
                    return
                if action != "select":
                    break
                save_last_selection(repo, change.path, artifacts[index])
                last = load_last_selection(repo)
                self.read(screen, os.path.join(change.path, artifacts[index]))

    # ── Reader ──────────────────────────────────────────────────────────
    def read(self, screen: curses.window, path: str) -> None:
        reader = Reader(self, path)
        saved = reader.run(screen)
        if saved:
            self.handoff(screen, path, saved)

    def handoff(self, screen: curses.window, path: str, saved: int) -> None:
        rel = os.path.relpath(path, repo_root(os.path.dirname(path)) or os.path.dirname(path))
        lines = [f"Send {saved} new note(s) to the agent? (y/n)", rel]
        if not self.confirm(screen, "Send notes to the agent", lines):
            self.status = "Notes kept in the file; nothing sent"
            return
        message = build_handoff_message([path])
        ok, error = send_prompt(self.source_pane, message) if self.source_pane else (False, "no source pane")
        if ok:
            self.status = "Sent the notes to the agent"
        else:
            copy_text_to_clipboard(message)
            self.status = f"Error: {error[:80]} · message copied to the clipboard"

    def confirm(self, screen: curses.window, title: str, lines: list[str]) -> bool:
        height, width = screen.getmaxyx()
        modal_width = max(40, min(width - 4, max(len(line) for line in lines) + 8))
        modal_height = len(lines) + 5
        modal = curses.newwin(
            modal_height, modal_width, max(0, (height - modal_height) // 2), max(0, (width - modal_width) // 2)
        )
        modal.keypad(True)
        while True:
            modal.erase()
            _draw_heavy_box(modal, self.border_attr())
            _safe_addnstr(modal, 0, 2, f" {title} ", modal_width - 4, self.border_attr())
            for offset, line in enumerate(lines):
                attr = 0 if offset == 0 else self.style("muted")
                _safe_addnstr(modal, 2 + offset, 3, line, modal_width - 6, attr)
            _safe_addnstr(
                modal, modal_height - 2, 3, "[ y: yes ]    [ n / Esc: no ]", modal_width - 6,
                self.style("comment", curses.A_BOLD),
            )
            modal.refresh()
            key = modal.get_wch()
            if key in ("y", "Y"):
                return True
            if key in ("n", "N", "\x1b", "q"):
                return False

    def run(self, screen: curses.window) -> None:
        curses.curs_set(0)
        screen.keypad(True)
        self.setup_colors()
        if self.artifact:
            self.read(screen, self.artifact)
            if self.status:
                self.flash(screen)
            return
        self.picker(screen)

    def flash(self, screen: curses.window) -> None:
        """Show the last status briefly before exiting."""
        screen.erase()
        height, width = screen.getmaxyx()
        self.draw_frame(screen, "", "")
        self.draw_footer(screen, height - 2, " closing… ")
        screen.refresh()
        curses.napms(900)


class Reader:
    def __init__(self, app: App, path: str):
        self.app = app
        self.path = path
        self.doc: Document = load_document(path)
        self.cursor = 0
        self.editor: TextBuffer | None = None
        self.edit_top = 0
        self.saved = 0
        self.changed_on_disk = False
        self.display_rows: list[tuple[str, int, str]] = []
        self.visible_rows = 1
        self.app.status = f"{len(self.doc.notes)} pending note(s)" if self.doc.notes else ""

    def reload(self) -> None:
        anchor = self.doc.blocks[self.cursor].start if self.doc.blocks else 1
        self.doc = load_document(self.path)
        self.changed_on_disk = False
        if self.doc.blocks:
            self.cursor = min(
                range(len(self.doc.blocks)), key=lambda i: abs(self.doc.blocks[i].start - anchor)
            )

    def check_disk(self) -> None:
        try:
            if os.path.getmtime(self.path) != self.doc.mtime:
                self.changed_on_disk = True
                self.app.status = "File changed on disk · R to reload"
        except OSError:
            pass

    def set_zoom(self, level: int) -> None:
        """Change the reading zoom (simulated with the layout) and remember it."""
        clamped = clamp_zoom(level)
        if clamped == self.app.zoom:
            limit = "maximum" if level > ZOOM_MAX else "minimum" if level < ZOOM_MIN else "normal"
            self.app.status = f"Zoom is already at the {limit} level"
            return
        self.app.zoom = clamped
        save_zoom(clamped)
        self.app.status = f"Zoom {clamped:+d}" if clamped else "Zoom reset"

    def heading_blocks(self) -> list[int]:
        return [i for i, b in enumerate(self.doc.blocks) if not b.code and b.text.startswith("#")]

    def run(self, screen: curses.window) -> int:
        if not self.doc.blocks:
            self.app.status = "Error: the file is empty"
            return 0
        while True:
            self.check_disk()
            self.draw(screen)
            screen.timeout(1000)
            key = screen.getch()
            screen.timeout(-1)
            if key == -1:
                continue
            count = len(self.doc.blocks)
            if key in (ord("q"), 27):
                return self.saved
            if key in (curses.KEY_UP, ord("k")):
                self.cursor = max(0, self.cursor - 1)
            elif key in (curses.KEY_DOWN, ord("j")):
                self.cursor = min(count - 1, self.cursor + 1)
            elif key in (curses.KEY_SR, curses.KEY_SF, curses.KEY_PPAGE, curses.KEY_NPAGE, ord("u"), ord("d")):
                full = key in (curses.KEY_SR, curses.KEY_SF)
                page = max(1, self.visible_rows - 2) if full else max(1, self.visible_rows // 2)
                if key in (curses.KEY_SR, curses.KEY_PPAGE, ord("u")):
                    page = -page
                self.cursor = page_target(self.display_rows, self.cursor, page)
            elif key == ord("g"):
                self.cursor = 0
            elif key == ord("G"):
                self.cursor = count - 1
            elif key in (ord("n"), ord("N")):
                headings = self.heading_blocks()
                if key == ord("n"):
                    following = [i for i in headings if i > self.cursor]
                    self.cursor = following[0] if following else self.cursor
                else:
                    previous = [i for i in headings if i < self.cursor]
                    self.cursor = previous[-1] if previous else self.cursor
            elif key in (ord("+"), ord("=")):
                self.set_zoom(self.app.zoom + 1)
            elif key in (ord("-"), ord("_")):
                self.set_zoom(self.app.zoom - 1)
            elif key == ord("0"):
                self.set_zoom(0)
            elif key == ord("R"):
                self.reload()
                self.app.status = "Reloaded"
            elif key == ord("c"):
                if self.changed_on_disk:
                    self.reload()
                self.edit_comment(screen)

    # Drawing mirrors the comment composer's viewer.
    def draw(self, screen: curses.window) -> None:
        screen.erase()
        height, width = screen.getmaxyx()
        box_height = _COMMENT_BOX_HEIGHT if self.editor is not None else 0
        viewer_height = height - box_height
        if viewer_height < 8 or width < 30:
            _safe_addnstr(screen, 0, 0, "Pane too small", width - 1, curses.A_BOLD)
            screen.refresh()
            return
        inner_bottom = viewer_height - 1 if box_height else height - 2
        inner_width = width - 2
        app = self.app
        rel = os.path.relpath(self.path, os.path.dirname(change_for_artifact(self.path) or self.path))
        change = os.path.basename(change_for_artifact(self.path) or os.path.dirname(self.path))

        # Tables and rules use the full width; the zoom only changes the text column.
        full_width = max(1, width - 6)
        content_width, margin, spacer_policy = zoom_layout(self.app.zoom, full_width)
        texts = [block.text for block in self.doc.blocks]
        codes = [block.code for block in self.doc.blocks]
        markdown = format_markdown_lines(texts, full_width, codes)
        comments: dict[int, str] = {}
        for note in self.doc.notes:
            index = self.doc.note_blocks.get(note.note_id)
            label = f"{note.note_id} · {note.human_comment}"
            if index is None:
                index, label = 0, f"{note.note_id} (text not found) · {note.human_comment}"
            comments[index] = (comments[index] + "\n" + label) if index in comments else label
        compact_after = {
            i for i in range(len(markdown) - 1)
            if (markdown[i][1] == "bullet" and markdown[i + 1][1] == "bullet") or codes[i + 1] == "code"
        }
        if spacer_policy == "none":
            compact_after = set(range(len(markdown)))
        elif spacer_policy == "sections":
            compact_after |= {i for i in range(len(markdown) - 1) if markdown[i + 1][1] != "heading"}
        rows = build_display_rows(
            [text for text, _kind in markdown], comments, width=content_width, spacing=True,
            compact_after=compact_after, no_wrap={i for i, (_t, k) in enumerate(markdown) if k == "table"},
            no_wrap_width=full_width,
            preserve_space={i for i, (_t, k) in enumerate(markdown) if k == "code"},
        )
        selected_row = next(i for i, (kind, line, _) in enumerate(rows) if kind == "line" and line == self.cursor)
        available = content_rows_available(height, box_height)
        self.display_rows, self.visible_rows = rows, available
        top = max(0, min(selected_row - available // 2, max(0, len(rows) - available)))

        block = self.doc.blocks[self.cursor]
        position = f"lines {block.start}-{block.end}" if block.end != block.start else f"line {block.start}"
        label = scroll_position_label(len(rows), available, top)
        subtitle = f"{rel}  ·  {len(self.doc.notes)} pending note(s)  ·  {position}"
        subtitle += "".join(f" · {part}" for part in (label, zoom_label(self.app.zoom)) if part)
        app.draw_frame(screen, change, subtitle)

        thumb = scrollbar_thumb(len(rows), available, top)
        if thumb:
            for offset in range(available):
                inside = thumb[0] <= offset < thumb[0] + thumb[1]
                _safe_addnstr(screen, 3 + offset, width - 2, "┃" if inside else "│", 1,
                              app.border_attr() if inside else app.style("muted"))

        bold_at_row, bold = [], False
        for kind, _line, text in rows:
            if kind == "line":
                bold = False
            bold_at_row.append(bold)
            if kind in ("line", "continuation"):
                _segments, bold = bold_segments(text, bold)

        for y, (kind, index, text) in enumerate(rows[top : top + available], 3):
            if kind == "spacer":
                continue
            if kind in ("comment", "comment_continuation"):
                prefix = COMMENT_PREFIX if kind == "comment" else " " * len(COMMENT_PREFIX)
                _safe_addnstr(
                    screen, y, 1 + margin, prefix + text, inner_width - margin,
                    app.style("comment", curses.A_BOLD) | curses.A_BOLD,
                )
                continue
            markdown_kind = markdown[index][1]
            if index == self.cursor:
                attr = app.style("selected", curses.A_REVERSE)
            else:
                attr = app.style(markdown_kind, curses.A_BOLD if markdown_kind == "heading" else 0)
            prefix = "▸ " if index == self.cursor and kind == "line" else "  "
            # The marker sits next to the text; tables ignore the zoom margin.
            marker_x = 1 if markdown_kind == "table" else 1 + margin
            _safe_addnstr(screen, y, marker_x, prefix, 2, app.style("marker"))
            x = marker_x + 2
            segments, _bold = bold_segments(text, bold_at_row[top + y - 3])
            for segment, is_bold in segments:
                room = inner_width - (x - 1)
                if room <= 0:
                    break
                _safe_addnstr(screen, y, x, segment, room, attr | curses.A_BOLD if is_bold else attr)
                x += len(segment)

        footer = " ↑/↓ move · ⇧↑/↓ page · +/- zoom · n/N heading · c comment · R reload · q close "
        app.draw_footer(screen, inner_bottom, footer)
        if box_height:
            self.draw_comment_box(screen, viewer_height)
        screen.refresh()

    def draw_comment_box(self, screen: curses.window, top: int) -> None:
        height, width = screen.getmaxyx()
        app = self.app
        inner_height = _COMMENT_BOX_HEIGHT - 2
        inner_width = width - 4
        _safe_addnstr(screen, top, 0, "┣" + "━" * (width - 2) + "┫", width, app.border_attr())
        badge = " ✎ AI NOTE "
        _safe_addnstr(screen, top, 2, badge, width - 4, app.style("badge", curses.A_REVERSE) | curses.A_BOLD)
        block = self.doc.blocks[self.cursor]
        label = f" lines {block.start}-{block.end} · {comment_preview(block.text)} "
        _safe_addnstr(screen, top, 2 + len(badge), label, width - len(badge) - 4, app.border_attr())
        editor = self.editor or TextBuffer()
        visual_rows = editor_visual_rows(editor.lines, inner_width)
        cursor_row, cursor_col = editor_cursor_position(visual_rows, editor.row, editor.col)
        if cursor_row < self.edit_top:
            self.edit_top = cursor_row
        elif cursor_row >= self.edit_top + inner_height:
            self.edit_top = cursor_row - inner_height + 1
        for offset, (_logical, _start, text) in enumerate(visual_rows[self.edit_top : self.edit_top + inner_height], 1):
            _safe_addnstr(screen, top + offset, 2, text, inner_width)
        help_text = " Ctrl+S save to file · Enter new line · Esc cancel "
        _safe_addnstr(screen, height - 1, 2, help_text, width - 4, app.style("muted"))
        try:
            screen.move(top + 1 + cursor_row - self.edit_top, 2 + min(cursor_col, inner_width - 1))
        except curses.error:
            pass

    def edit_comment(self, screen: curses.window) -> None:
        self.editor = TextBuffer()
        self.edit_top = 0
        curses.curs_set(1)
        try:
            while True:
                self.draw(screen)
                key = screen.get_wch()
                if key == "\x13":
                    text = self.editor.text.strip()
                    if not text:
                        self.app.status = "Empty comment; nothing saved"
                        return
                    block = self.doc.blocks[self.cursor]
                    note = add_note_to_file(
                        self.path, block.start, block.end, self.doc.block_source(self.cursor), text
                    )
                    self.saved += 1
                    self.reload()
                    self.app.status = f"{note.note_id} saved to the file"
                    return
                if key == "\x1b":
                    if needs_discard_confirmation("", self.editor.text):
                        curses.curs_set(0)
                        if not self.app.confirm(screen, "Unsaved note", ["Discard this note? (y/n)"]):
                            curses.curs_set(1)
                            continue
                    self.app.status = "Note cancelled"
                    return
                action = _EDITOR_KEYS.get(key)
                if action is not None:
                    action(self.editor)
                elif isinstance(key, str) and key.isprintable():
                    self.editor.insert(key)
        finally:
            self.editor = None
            curses.curs_set(0)


def main() -> None:
    source_pane = os.environ.get("SPEC_REVIEW_SOURCE_PANE") or os.environ.get("HERDR_PANE_ID", "")
    cwd = os.environ.get("SPEC_REVIEW_CWD") or os.getcwd()
    artifact = os.environ.get("SPEC_REVIEW_ARTIFACT", "")
    original_termios = None
    if os.isatty(0):
        try:
            original_termios = termios.tcgetattr(0)
            attrs = termios.tcgetattr(0)
            attrs[0] &= ~(termios.IXON | termios.IXOFF)  # Let Ctrl+S reach the app.
            termios.tcsetattr(0, termios.TCSANOW, attrs)
        except termios.error:
            original_termios = None
    try:
        curses.set_escdelay(25)
        curses.wrapper(App(source_pane, cwd, artifact).run)
    finally:
        if original_termios is not None:
            try:
                termios.tcsetattr(0, termios.TCSANOW, original_termios)
            except termios.error:
                pass


def log_crash() -> None:
    """Append the current traceback to crash.log in the plugin state dir."""
    try:
        os.makedirs(_state_dir(), exist_ok=True)
        with open(os.path.join(_state_dir(), "crash.log"), "a", encoding="utf-8") as log:
            log.write(traceback.format_exc() + "\n")
    except OSError:
        pass
