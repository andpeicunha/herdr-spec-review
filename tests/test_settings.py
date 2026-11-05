from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from specreview.settings import next_theme, save_theme, selected_theme


class ThemeSettingsTests(unittest.TestCase):
    def test_default_and_invalid_themes_use_terminal(self):
        with patch.dict(os.environ, {}, clear=True), tempfile.TemporaryDirectory() as config:
            with patch.dict(os.environ, {"HERDR_PLUGIN_CONFIG_DIR": config}, clear=True):
                self.assertEqual(selected_theme(), "terminal")
                (Path(config) / "config.env").write_text("SPEC_REVIEW_THEME=unknown\n", encoding="utf-8")
                self.assertEqual(selected_theme(), "terminal")

    def test_environment_setting_precedes_config(self):
        with tempfile.TemporaryDirectory() as config:
            with open(os.path.join(config, "config.env"), "w", encoding="utf-8") as target:
                target.write("SPEC_REVIEW_THEME=paper\n")
            with patch.dict(os.environ, {"HERDR_PLUGIN_CONFIG_DIR": config, "SPEC_REVIEW_THEME": "midnight"}, clear=True):
                self.assertEqual(selected_theme(), "midnight")

    def test_cycle_persists_and_preserves_other_config(self):
        with tempfile.TemporaryDirectory() as config:
            path = os.path.join(config, "config.env")
            with open(path, "w", encoding="utf-8") as target:
                target.write("KEEP=value\nSPEC_REVIEW_THEME=terminal\nOTHER=unchanged\n")
            with patch.dict(os.environ, {"HERDR_PLUGIN_CONFIG_DIR": config}, clear=True):
                theme = next_theme(selected_theme())
                self.assertTrue(save_theme(theme))
                with open(path, encoding="utf-8") as source:
                    contents = source.read()
                self.assertIn("KEEP=value", contents)
                self.assertIn("OTHER=unchanged", contents)
                self.assertIn("SPEC_REVIEW_THEME=herdr-dark", contents)
                self.assertEqual(selected_theme(), "herdr-dark")


if __name__ == "__main__":
    unittest.main()
