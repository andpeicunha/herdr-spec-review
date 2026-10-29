import inspect
import re
import unittest

from specreview.help import READER_HELP, clamp_scroll, help_layout, picker_help
from specreview.ui import Reader

# Aliases of documented keys that the reader also accepts.
ALIASES = {"=", "_"}


def key_tokens(sections):
    """Single keys named in the tables, e.g. "u d / PgUp PgDn" gives u, d, PgUp, PgDn."""
    return {
        token
        for _title, items in sections
        for keys, _text in items
        for token in re.split(r"[\s/]+", keys)
        if token
    }


class HelpTests(unittest.TestCase):
    def test_sections_are_separated_by_one_blank_row(self):
        rows, _indent = help_layout(READER_HELP, 70)
        kinds = [kind for kind, _keys, _text in rows]

        self.assertEqual(kinds.count("section"), len(READER_HELP))
        self.assertEqual(kinds.count("blank"), len(READER_HELP) - 1)
        self.assertNotEqual(kinds[-1], "blank")

    def test_keys_and_text_share_a_row_when_they_fit(self):
        rows, indent = help_layout([("Move", [("g G", "first / last block")])], 40)

        self.assertEqual(rows, [("section", "Move", ""), ("key", "g G", "first / last block")])
        self.assertEqual(indent, len("g G") + 2)

    def test_wide_keys_never_get_cut_in_a_narrow_modal(self):
        rows, indent = help_layout([("S", [("Tab / Shift+Tab", "save and go to the next block")])], 12)
        key_rows = [(keys, text) for kind, keys, text in rows if kind == "key"]

        self.assertEqual(key_rows[0], ("Tab / Shift+Tab", ""))
        self.assertEqual(indent, 2)
        self.assertEqual(" ".join(text for _keys, text in key_rows).strip(), "save and go to the next block")

    def test_every_row_fits_the_modal_width(self):
        for width in (26, 30, 40, 70):
            rows, indent = help_layout(READER_HELP, width)
            for _kind, keys, text in rows:
                self.assertLessEqual(len(keys), width, (width, keys))
                if text:
                    self.assertLessEqual(indent + len(text), width, (width, text))

    def test_scroll_offset_stays_inside_the_rows(self):
        self.assertEqual(clamp_scroll(-3, 20, 8), 0)
        self.assertEqual(clamp_scroll(99, 20, 8), 12)
        self.assertEqual(clamp_scroll(4, 5, 8), 0)

    def test_every_key_handled_by_the_reader_is_in_the_help(self):
        handled = {
            "Space" if char == " " else char
            for char in re.findall(r'ord\("(.)"\)', inspect.getsource(Reader.run))
        }

        self.assertEqual(handled - ALIASES - key_tokens(READER_HELP), set())

    def test_picker_help_lists_the_repositories_key_only_when_it_works(self):
        with_repos = key_tokens(picker_help(True))
        without = key_tokens(picker_help(False))

        self.assertIn("r", with_repos)
        self.assertNotIn("r", without)
        self.assertTrue({"Enter", "Esc", "q", "?"} <= without)
        # "/" is the filter key; it is also the separator of key_tokens, so look at the keys column.
        self.assertIn("/", [keys for _title, items in picker_help(False) for keys, _text in items])

    def test_the_help_tables_have_no_empty_section_or_text(self):
        for sections in (READER_HELP, picker_help(True)):
            for title, items in sections:
                self.assertTrue(title.strip() and items)
                for keys, text in items:
                    self.assertTrue(keys.strip() and text.strip(), (title, keys))


if __name__ == "__main__":
    unittest.main()
