import os
import tempfile
import unittest
from unittest.mock import patch

from specreview.layout import ZOOM_MAX, ZOOM_MIN, build_display_rows, clamp_zoom, zoom_label, zoom_layout
from specreview.markdown import format_markdown_lines
from specreview.ui import App, Reader, load_zoom, save_zoom


class ZoomLayoutTests(unittest.TestCase):
    def test_normal_and_zoom_out_keep_full_width(self):
        self.assertEqual(zoom_layout(0, 100), (100, 0, "all"))
        self.assertEqual(zoom_layout(-1, 100), (100, 0, "sections"))
        self.assertEqual(zoom_layout(-2, 100), (100, 0, "none"))

    def test_zoom_in_narrows_and_centers_the_column(self):
        self.assertEqual(zoom_layout(1, 100), (85, 7, "all"))
        self.assertEqual(zoom_layout(2, 100), (70, 15, "all"))
        self.assertEqual(zoom_layout(3, 100), (55, 22, "all"))

    def test_zoom_in_never_goes_below_a_readable_column_or_above_the_pane(self):
        self.assertEqual(zoom_layout(3, 30), (24, 3, "all"))
        self.assertEqual(zoom_layout(3, 20), (20, 0, "all"))
        self.assertEqual(zoom_layout(3, 1), (1, 0, "all"))
        for available in range(1, 200):
            for level in range(ZOOM_MIN, ZOOM_MAX + 1):
                column, margin, _policy = zoom_layout(level, available)
                self.assertGreaterEqual(column, 1)
                self.assertLessEqual(column + margin, available)

    def test_levels_are_clamped(self):
        self.assertEqual(clamp_zoom(99), ZOOM_MAX)
        self.assertEqual(clamp_zoom(-99), ZOOM_MIN)
        self.assertEqual(zoom_layout(99, 100), zoom_layout(ZOOM_MAX, 100))

    def test_label_shows_only_when_zoomed(self):
        self.assertEqual(zoom_label(0), "")
        self.assertEqual(zoom_label(2), "zoom +2")
        self.assertEqual(zoom_label(-1), "zoom -1")


class ZoomTableTests(unittest.TestCase):
    def test_tables_are_cut_at_the_full_width_not_the_column(self):
        table = "| Campo | Descrição |\n|---|---|\n| token | valor muito longo aqui |"
        full, column = 40, 22
        markdown = format_markdown_lines([table], full)

        rows = build_display_rows(
            [markdown[0][0]], {}, width=column, no_wrap={0}, no_wrap_width=full
        )

        self.assertTrue(any(len(text) > column for _kind, _index, text in rows))
        self.assertTrue(all(len(text) <= full for _kind, _index, text in rows))
        self.assertEqual(rows[0][2], "Campo │ Descrição")

    def test_wide_table_still_truncates_with_ellipsis_at_full_width(self):
        table = "| Key | Description |\n| a | " + "x" * 80 + " |"
        markdown = format_markdown_lines([table], 30)
        rows = build_display_rows([markdown[0][0]], {}, width=20, no_wrap={0}, no_wrap_width=30)

        self.assertTrue(all(len(text) <= 30 for _kind, _index, text in rows))
        self.assertTrue(any(text.endswith("…") for _kind, _index, text in rows))

    def test_text_wraps_at_the_column_width(self):
        rows = build_display_rows(["word " * 20], {}, width=24, no_wrap_width=80)

        self.assertTrue(all(len(text) <= 24 for _kind, _index, text in rows))
        self.assertGreater(len(rows), 3)


class ZoomStateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        patcher = patch.dict("os.environ", {"HERDR_PLUGIN_STATE_DIR": self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.addCleanup(self.tmp.cleanup)

    def test_zoom_is_saved_and_loaded_globally(self):
        self.assertEqual(load_zoom(), 0)
        save_zoom(2)

        self.assertEqual(load_zoom(), 2)
        self.assertEqual(App("").zoom, 2)

    def test_bad_or_out_of_range_saved_values_are_safe(self):
        path = os.path.join(self.tmp.name, "zoom")
        for text, expected in (("abc", 0), ("", 0), ("99", ZOOM_MAX), ("-99", ZOOM_MIN)):
            with open(path, "w", encoding="utf-8") as out:
                out.write(text)
            self.assertEqual(load_zoom(), expected)

    def test_reader_keys_change_level_stop_at_limits_and_persist(self):
        doc = os.path.join(self.tmp.name, "proposal.md")
        with open(doc, "w", encoding="utf-8") as out:
            out.write("## Why\n\nText.\n")
        app = App("")
        reader = Reader(app, doc)

        reader.set_zoom(app.zoom + 1)
        self.assertEqual((app.zoom, app.status, load_zoom()), (1, "Zoom +1", 1))
        for _ in range(10):
            reader.set_zoom(app.zoom + 1)
        self.assertEqual(app.zoom, ZOOM_MAX)
        self.assertIn("maximum", app.status)
        for _ in range(10):
            reader.set_zoom(app.zoom - 1)
        self.assertEqual(app.zoom, ZOOM_MIN)
        self.assertIn("minimum", app.status)
        reader.set_zoom(0)
        self.assertEqual((app.zoom, app.status, load_zoom()), (0, "Zoom reset", 0))


if __name__ == "__main__":
    unittest.main()
