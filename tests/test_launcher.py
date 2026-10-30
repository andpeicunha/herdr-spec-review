import os
import subprocess
import tempfile
import unittest

from specreview.launcher import LAUNCHER_NAME, ROOT_FILE_NAME, ensure_launcher


def fake_install(root: str, name: str, marker: str) -> str:
    """A plugin copy whose bin/spec-review-mcp just prints ``marker``."""
    checkout = os.path.join(root, name, "checkout")
    os.makedirs(os.path.join(checkout, "bin"))
    script = os.path.join(checkout, "bin", "spec-review-mcp")
    with open(script, "w", encoding="utf-8") as out:
        out.write(f"#!/bin/sh\necho {marker} \"$@\"\n")
    os.chmod(script, 0o755)
    return checkout


class LauncherTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        # Same layout as ~/.config/herdr/plugins: config/<id> and github-installations/<id>-<hash>/<n>/checkout.
        self.plugins = tmp.name
        self.config_dir = os.path.join(self.plugins, "config", "andpeicunha.spec-review")
        self.installs = os.path.join(self.plugins, "github-installations", "andpeicunha.spec-review-abc")

    def run_launcher(self, *args):
        path = os.path.join(self.config_dir, LAUNCHER_NAME)
        return subprocess.run([path, *args], capture_output=True, text=True)

    def test_creates_an_executable_launcher_and_is_idempotent(self):
        path = ensure_launcher(self.config_dir)
        self.assertEqual(path, os.path.join(self.config_dir, LAUNCHER_NAME))
        self.assertTrue(os.access(path, os.X_OK))
        before = os.stat(path).st_mtime_ns
        ensure_launcher(self.config_dir)
        self.assertEqual(os.stat(path).st_mtime_ns, before)

    def test_runs_the_newest_installed_copy_and_keeps_arguments(self):
        ensure_launcher(self.config_dir)
        fake_install(self.installs, "100-0", "old")
        newest = fake_install(self.installs, "200-0", "new")
        os.utime(newest, (2_000_000_000, 2_000_000_000))
        result = self.run_launcher("--flag")
        self.assertEqual(result.stdout.strip(), "new --flag")

    def test_falls_back_to_the_recorded_root_for_a_linked_plugin(self):
        root = fake_install(os.path.join(self.plugins, "dev"), "src", "linked")
        ensure_launcher(self.config_dir, root)
        with open(os.path.join(self.config_dir, ROOT_FILE_NAME), encoding="utf-8") as source:
            self.assertEqual(source.read().strip(), root)
        self.assertEqual(self.run_launcher().stdout.strip(), "linked")

    def test_says_how_to_install_when_nothing_is_found(self):
        ensure_launcher(self.config_dir)
        result = self.run_launcher()
        self.assertEqual(result.returncode, 1)
        self.assertIn("herdr plugin install", result.stderr)
        self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
