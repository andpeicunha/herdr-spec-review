import hashlib
import unittest
from pathlib import Path

from herdr_shared_ui import fill_row, initialize_colors
from herdr_shared_ui.layout import wrap_physical_line


class FakeCurses:
    class error(Exception):
        pass

    COLOR_BLACK = 0
    COLOR_BLUE = 4
    COLOR_CYAN = 6
    COLOR_GREEN = 2
    COLOR_MAGENTA = 5
    COLOR_RED = 1
    COLOR_WHITE = 7
    COLOR_YELLOW = 3

    def __init__(self, color_count):
        self.COLORS = color_count
        self.pairs = {}
        self.started = False

    def has_colors(self):
        return self.COLORS > 0

    def start_color(self):
        self.started = True

    def use_default_colors(self):
        pass

    def init_pair(self, number, foreground, background):
        self.pairs[number] = (foreground, background)

    @staticmethod
    def color_pair(number):
        return number << 8


class FakeScreen:
    def __init__(self):
        self.writes = []

    def addnstr(self, y, x, text, width, attr):
        self.writes.append((y, x, text, width, attr))


class SharedTerminalUiTests(unittest.TestCase):
    def test_bundled_source_matches_the_pinned_digest(self):
        package = Path(__file__).resolve().parents[1] / "herdr_shared_ui"
        digest = hashlib.sha256()
        for path in sorted(p for p in package.rglob("*") if p.is_file() and p.name != "PIN" and "__pycache__" not in p.parts):
            relative = path.relative_to(package).as_posix().encode()
            data = path.read_bytes()
            digest.update(len(relative).to_bytes(4, "big"))
            digest.update(relative)
            digest.update(len(data).to_bytes(8, "big"))
            digest.update(data)
        pin = (package / "PIN").read_text(encoding="utf-8").split()

        self.assertEqual(pin[0], "1.2.0")
        self.assertEqual(pin[1], f"sha256:{digest.hexdigest()}")
        self.assertEqual((package / "VERSION").read_text(encoding="utf-8").strip(), pin[0])

    def test_all_named_themes_provide_semantic_roles(self):
        from herdr_shared_ui.themes import THEME_IDS, initialize_colors
        for theme in THEME_IDS:
            styles = initialize_colors(FakeCurses(256), theme=theme)
            self.assertTrue({"selected", "heading", "code", "error"}.issubset(styles))

    def test_controls_cycle_focus_and_dispatch_plugin_actions(self):
        from herdr_shared_ui.controls import Button, ButtonBar, Modal
        bar = ButtonBar([Button("Keep", "keep"), Button("Discard", "discard")])
        self.assertIsNone(bar.handle_key("\t"))
        self.assertEqual(bar.handle_key("\n"), "discard")
        modal = Modal([Button("Keep", "keep")], {"keep": lambda: "plugin-result"})
        self.assertEqual(modal.handle_key("\n"), "plugin-result")

    def test_shared_palette_keeps_approved_256_color_roles(self):
        curses = FakeCurses(256)

        styles = initialize_colors(curses)

        self.assertTrue(curses.started)
        self.assertIn("selected", styles)
        self.assertEqual(curses.pairs[1], (250, 24))
        self.assertEqual(curses.pairs[3], (39, -1))
        self.assertEqual(curses.pairs[4], (255, 24))

    def test_basic_color_and_monochrome_fallbacks_are_available(self):
        basic = FakeCurses(8)
        basic_styles = initialize_colors(basic)
        monochrome = FakeCurses(0)

        self.assertIn("selected", basic_styles)
        self.assertEqual(basic.pairs[1], (FakeCurses.COLOR_WHITE, FakeCurses.COLOR_BLUE))
        self.assertEqual(initialize_colors(monochrome), {})

    def test_fill_row_paints_empty_cells_with_the_selection_attribute(self):
        screen = FakeScreen()

        fill_row(screen, 5, 2, 7, 19)

        self.assertEqual(screen.writes, [(5, 2, " " * 7, 7, 19)])

    def test_quote_list_wrapping_indents_continuations_under_list_text(self):
        for line in ("│ 2. " + "word " * 8, "│ - " + "word " * 8):
            prefix = line.split("word", 1)[0]
            wrapped = wrap_physical_line(line, 24)

            self.assertGreater(len(wrapped), 1)
            self.assertTrue(all(row.startswith(" " * len(prefix) + "word") for row in wrapped[1:]))


if __name__ == "__main__":
    unittest.main()
