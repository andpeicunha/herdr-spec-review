"""Render a curses app in a virtual terminal (pyte) and print the screen.

Usage:
    uv run --no-project --with pyte python3 tools/render_screen.py ENTRY COLS ROWS KEYS...

ENTRY is the script to run (for example spec_review.py). The child inherits this
process environment (SPEC_REVIEW_ARTIFACT, HERDR_PLUGIN_STATE_DIR, ...). Each KEYS
argument is sent in order: "@" prints the screen, "@b" prints it with bold cells
in [ ], "@c" appends the fg/bg colors of one cell per row, "BTAB" sends Shift+Tab, and Python escapes (\\r, \\t, \\x13, \\x1b) are decoded.
"""
import os
import pty
import select
import sys
import time

import pyte

entry, cols, rows = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
pid, fd = pty.fork()
if pid == 0:
    os.environ.update(TERM="xterm-256color", LINES=str(rows), COLUMNS=str(cols))
    os.execvp("python3", ["python3", entry])


class ScrollScreen(pyte.Screen):
    """pyte lacks CSI S/T (scroll up/down), which ncurses uses."""

    def scroll_up(self, count=1, *args, **kwargs):
        saved = (self.cursor.x, self.cursor.y)
        self.cursor.y = self.margins.bottom if self.margins else self.lines - 1
        for _ in range(count or 1):
            self.index()
        self.cursor.x, self.cursor.y = saved

    def scroll_down(self, count=1, *args, **kwargs):
        saved = (self.cursor.x, self.cursor.y)
        self.cursor.y = self.margins.top if self.margins else 0
        for _ in range(count or 1):
            self.reverse_index()
        self.cursor.x, self.cursor.y = saved


class ScrollStream(pyte.ByteStream):
    csi = dict(pyte.ByteStream.csi, S="scroll_up", T="scroll_down")


screen = ScrollScreen(cols, rows)
stream = ScrollStream(screen)


def pump(t):
    end = time.time() + t
    while time.time() < end:
        r, _, _ = select.select([fd], [], [], 0.05)
        if r:
            try:
                stream.feed(os.read(fd, 65536))
            except OSError:
                return


pump(1.2)
for step, keys in enumerate(sys.argv[4:]):
    if keys in ("@", "@b", "@c"):
        print(f"--- screen {step} ---")
        for y in range(screen.lines):
            out, inside = "", False
            for x in range(screen.columns):
                char = screen.buffer[y][x]
                if keys == "@b" and char.bold != inside:
                    out += "[" if char.bold else "]"
                    inside = char.bold
                out += char.data
            line = (out + ("]" if inside else "")).rstrip()
            if keys == "@c":
                cell = screen.buffer[y][min(8, screen.columns - 1)]
                line += f"   <fg={cell.fg} bg={cell.bg}>"
            print(line)
        continue
    data = b"\x1b[Z" if keys == "BTAB" else keys.encode().decode("unicode_escape").encode()
    os.write(fd, data)
    pump(0.5)
for key in (b"\x1b", b"n", b"q", b"q"):
    os.write(fd, key)
    pump(0.2)
try:
    os.kill(pid, 9)
except OSError:
    pass
