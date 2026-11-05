from __future__ import annotations

import os
import tempfile
import unittest
from unittest.mock import patch

from specreview.ui import App, Reader


class FakeScreen:
    def timeout(self, _value):
        pass


class ReaderThemeTests(unittest.TestCase):
    def test_t_cycles_and_persists_theme_from_the_reader_loop(self):
        with tempfile.TemporaryDirectory() as config, tempfile.TemporaryDirectory() as state:
            artifact = os.path.join(config, "proposal.md")
            with open(artifact, "w", encoding="utf-8") as target:
                target.write("# Change\n\nA paragraph.\n")
            with patch.dict(os.environ, {
                "HERDR_PLUGIN_CONFIG_DIR": config,
                "HERDR_PLUGIN_STATE_DIR": state,
            }, clear=True):
                app = App("")
                reader = Reader(app, artifact)
                with patch("specreview.ui.initialize_colors", return_value={"selected": 1}), \
                     patch.object(Reader, "draw"), \
                     patch("specreview.ui.read_key", side_effect=[ord("t"), ord("q")]):
                    reader.run(FakeScreen())
                self.assertEqual(app.theme, "herdr-dark")
                with open(os.path.join(config, "config.env"), encoding="utf-8") as source:
                    self.assertIn("SPEC_REVIEW_THEME=herdr-dark", source.read())


if __name__ == "__main__":
    unittest.main()
