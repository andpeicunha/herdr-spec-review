import os
import subprocess
import tempfile
import unittest

from specreview.discovery import (
    candidate_repos,
    change_for_artifact,
    change_pending_count,
    list_artifacts,
    open_changes,
    parse_worktree_porcelain,
    repo_root,
)


def write(path, text="x\n"):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as out:
        out.write(text)


def git(cwd, *args):
    subprocess.run(["git", "-C", cwd, *args], check=True, capture_output=True)


class DiscoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = os.path.realpath(os.path.join(self.tmp.name, "repo"))
        os.makedirs(self.repo)
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "t@example.com")
        git(self.repo, "config", "user.name", "Test")
        changes = os.path.join(self.repo, "openspec", "changes")
        write(os.path.join(changes, "add-login", "proposal.md"))
        write(os.path.join(changes, "add-login", "tasks.md"))
        write(os.path.join(changes, "add-login", "specs", "auth", "spec.md"))
        write(os.path.join(changes, "add-login", "design.md"))
        write(os.path.join(changes, "archive", "2026-01-old", "proposal.md"))
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", "init")

    def tearDown(self):
        self.tmp.cleanup()

    def test_open_changes_skip_archive(self):
        changes = open_changes(self.repo)

        self.assertEqual([c.name for c in changes], ["add-login"])
        self.assertEqual(changes[0].worktree.branch, "main")

    def test_worktrees_are_included_and_labelled(self):
        worktree = os.path.join(self.repo, ".worktrees", "login")
        git(self.repo, "worktree", "add", "-q", "-b", "feat/login", worktree)

        changes = open_changes(self.repo)

        self.assertEqual(
            [(c.name, c.worktree.branch) for c in changes],
            [("add-login", "main"), ("add-login", "feat/login")],
        )
        self.assertEqual(repo_root(worktree), self.repo)

    def test_artifacts_follow_review_order(self):
        change = os.path.join(self.repo, "openspec", "changes", "add-login")

        self.assertEqual(
            list_artifacts(change),
            ["proposal.md", "design.md", os.path.join("specs", "auth", "spec.md"), "tasks.md"],
        )

    def test_pending_notes_are_counted_per_change(self):
        change = os.path.join(self.repo, "openspec", "changes", "add-login")
        write(
            os.path.join(change, "design.md"),
            "x\n\n---\n\n# AI Notes\n\n## NOTE-001\n\nStatus: pending\n\n## NOTE-002\n\nStatus: pending\n",
        )

        self.assertEqual(change_pending_count(change), 2)

    def test_change_for_artifact_accepts_only_open_changes(self):
        base = os.path.join(self.repo, "openspec", "changes")

        self.assertEqual(
            change_for_artifact(os.path.join(base, "add-login", "specs", "auth", "spec.md")),
            os.path.join(base, "add-login"),
        )
        self.assertIsNone(change_for_artifact(os.path.join(base, "archive", "2026-01-old", "proposal.md")))
        self.assertIsNone(change_for_artifact(os.path.join(self.repo, "README.md")))

    def test_candidate_repos_from_panes_and_roots(self):
        nested = os.path.join(self.repo, "openspec")

        self.assertEqual(candidate_repos([nested, "/nonexistent"], []), [self.repo])
        self.assertEqual(candidate_repos([], [self.tmp.name]), [self.repo])

    def test_parse_worktree_porcelain_skips_bare(self):
        text = "worktree /a\nbare\n\nworktree /b\nHEAD 123\nbranch refs/heads/x\n\nworktree /c\ndetached\n"

        self.assertEqual(
            [(w.path, w.branch) for w in parse_worktree_porcelain(text)],
            [("/b", "x"), ("/c", "(detached)")],
        )


if __name__ == "__main__":
    unittest.main()
