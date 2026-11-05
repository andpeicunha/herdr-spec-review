from __future__ import annotations

import os
import sys
import tempfile
import unittest
from tests.ui_e2e_support import pyte
from pathlib import Path

from tests.ui_e2e_support import CursesSession, repo_root


@unittest.skipIf(pyte is None, "install pyte to run virtual-terminal E2E tests")
class SpecReviewTerminalE2ETests(unittest.TestCase):
    def test_reader_opens_mermaid_preview_from_selected_code_block(self):
        with tempfile.TemporaryDirectory() as config:
            artifact = Path(config) / "mermaid.md"
            artifact.write_text(
                "# Mermaid\n\n```mermaid\ngraph TD\n  A[Start] --> B[Done]\n```\n",
                encoding="utf-8",
            )
            env = {
                **os.environ,
                "TERM": "xterm-256color",
                "LINES": "24",
                "COLUMNS": "80",
                "HERDR_PLUGIN_CONFIG_DIR": config,
                "HERDR_PLUGIN_STATE_DIR": str(Path(config) / "state"),
                "SPEC_REVIEW_ARTIFACT": str(artifact),
            }
            env.pop("SPEC_REVIEW_THEME", None)
            with CursesSession([sys.executable, str(repo_root() / "spec_review.py")], env) as ui:
                self.assertIn("SPEC REVIEW", ui.text())
                ui.pump(0.5)
                self.assertIn("Mermaid preview", ui.text(), ui.text())
                self.assertIn("Start", ui.text(), ui.text())
                ui.send("j")
                ui.send("j")
                ui.send("m")
                ui.pump(0.5)
                self.assertIn("Mermaid preview", ui.text(), ui.text())
                ui.send("q")
                ui.send("q")

    def test_reader_cycles_theme_persists_it_and_lists_shortcut_in_help(self):
        root = repo_root()
        artifact = root / "openspec/changes/spec-review-beta-followups/proposal.md"
        self.assertTrue(artifact.is_file())
        with tempfile.TemporaryDirectory() as config:
            env = {
                **os.environ,
                "TERM": "xterm-256color",
                "LINES": "24",
                "COLUMNS": "80",
                "HERDR_PLUGIN_CONFIG_DIR": config,
                "HERDR_PLUGIN_STATE_DIR": str(Path(config) / "state"),
                "SPEC_REVIEW_ARTIFACT": str(artifact),
            }
            env.pop("SPEC_REVIEW_THEME", None)
            with CursesSession([sys.executable, str(root / "spec_review.py")], env) as ui:
                self.assertIn("SPEC REVIEW", ui.text())
                selected_row = next(
                    row for row in ui.screen.buffer.values()
                    if "Why" in "".join(cell.data for cell in row.values())
                )
                self.assertIn("005f87", {cell.bg for cell in selected_row.values()})
                for theme in ("midnight", "paper", "terminal"):
                    ui.send("t")
                    self.assertIn(f"Theme: {theme}", ui.text())
                saved = (Path(config) / "config.env").read_text(encoding="utf-8")
                self.assertIn("SPEC_REVIEW_THEME=terminal", saved)
                ui.send("?")
                ui.send("j" * 7)
                self.assertIn("cycle and save the viewer theme", ui.text(), ui.text())


if __name__ == "__main__":
    unittest.main()
