"""Find open OpenSpec changes in a repository and all of its git worktrees."""
from __future__ import annotations

import glob
import os
import subprocess
from dataclasses import dataclass

from .ainotes import pending_notes

# Review order of the spec-driven flow; specs/**/spec.md go between design and tasks.
_ARTIFACT_ORDER = ("proposal.md", "design.md")
_ARTIFACT_LAST = ("tasks.md",)


@dataclass
class Worktree:
    path: str
    branch: str


@dataclass
class Change:
    name: str
    path: str
    worktree: Worktree


def _git(cwd: str, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", "-C", cwd, *args], capture_output=True, text=True, timeout=10
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return result.stdout if result.returncode == 0 else None


def repo_root(cwd: str) -> str | None:
    """Top level of the main checkout for ``cwd`` (also when ``cwd`` is in a worktree)."""
    if not cwd or not os.path.isdir(cwd):
        return None
    common = _git(cwd, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if common:
        common = common.strip()
        if os.path.basename(common) == ".git":
            return os.path.dirname(common)
    top = _git(cwd, "rev-parse", "--show-toplevel")
    return top.strip() if top else None


def parse_worktree_porcelain(text: str) -> list[Worktree]:
    worktrees: list[Worktree] = []
    path, branch, bare = "", "", False
    for line in text.splitlines() + [""]:
        if line.startswith("worktree "):
            path, branch, bare = line[len("worktree ") :], "", False
        elif line.startswith("branch "):
            branch = line[len("branch ") :].removeprefix("refs/heads/")
        elif line == "detached":
            branch = "(detached)"
        elif line == "bare":
            bare = True
        elif not line and path:
            if not bare:
                worktrees.append(Worktree(path, branch))
            path, branch, bare = "", "", False
    return worktrees


def worktrees(root: str) -> list[Worktree]:
    output = _git(root, "worktree", "list", "--porcelain")
    found = [w for w in parse_worktree_porcelain(output or "") if os.path.isdir(w.path)]
    return found or [Worktree(root, "")]


def open_changes(root: str) -> list[Change]:
    """Open changes (``openspec/changes/*`` except ``archive``) in every worktree."""
    changes: list[Change] = []
    for worktree in worktrees(root):
        changes_dir = os.path.join(worktree.path, "openspec", "changes")
        try:
            names = sorted(os.listdir(changes_dir))
        except OSError:
            continue
        for name in names:
            path = os.path.join(changes_dir, name)
            if name != "archive" and not name.startswith(".") and os.path.isdir(path):
                changes.append(Change(name, path, worktree))
    return changes


def list_artifacts(change_path: str) -> list[str]:
    """Artifact paths relative to the change, in review order."""
    found = [name for name in _ARTIFACT_ORDER if os.path.isfile(os.path.join(change_path, name))]
    specs = sorted(
        os.path.relpath(path, change_path)
        for path in glob.glob(os.path.join(change_path, "specs", "**", "spec.md"), recursive=True)
    )
    found += specs
    found += [name for name in _ARTIFACT_LAST if os.path.isfile(os.path.join(change_path, name))]
    return found


def pending_count(path: str) -> int:
    try:
        with open(path, encoding="utf-8") as source:
            return len(pending_notes(source.read()))
    except OSError:
        return 0


def change_pending_count(change_path: str) -> int:
    return sum(pending_count(os.path.join(change_path, rel)) for rel in list_artifacts(change_path))


def change_for_artifact(path: str) -> str | None:
    """Return the change directory when ``path`` is a Markdown artifact of an open change."""
    path = os.path.abspath(path)
    if not path.endswith(".md") or not os.path.isfile(path):
        return None
    parts = path.split(os.sep)
    for index in range(len(parts) - 3):
        if parts[index] == "openspec" and parts[index + 1] == "changes":
            name = parts[index + 2]
            if name == "archive" or index + 3 >= len(parts):
                return None
            return os.sep.join(parts[: index + 3])
    return None


def candidate_repos(pane_cwds: list[str], roots: list[str]) -> list[str]:
    """Repos with ``openspec/changes`` from open panes and one level under ``roots``."""
    seen: list[str] = []

    def add(root: str | None) -> None:
        if root and root not in seen and os.path.isdir(os.path.join(root, "openspec", "changes")):
            seen.append(root)

    for cwd in pane_cwds:
        add(repo_root(cwd))
    for base in roots:
        base = os.path.expanduser(base)
        try:
            children = sorted(os.listdir(base))
        except OSError:
            continue
        for child in children:
            add(repo_root(os.path.join(base, child)) if os.path.isdir(os.path.join(base, child, "openspec")) else None)
    return seen
