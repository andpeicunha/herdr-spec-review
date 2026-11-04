import hashlib
import unittest
from pathlib import Path

from herdr_shared_ui import fill_row, initialize_colors


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
        source = (package / "__init__.py").read_bytes()
        pin = (package / "PIN").read_text(encoding="utf-8").split()

        self.assertEqual(pin[0], "1.0.0")
        self.assertEqual(pin[1], f"sha256:{hashlib.sha256(source).hexdigest()}")
        self.assertEqual((package / "VERSION").read_text(encoding="utf-8").strip(), pin[0])

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


if __name__ == "__main__":
    unittest.main()
