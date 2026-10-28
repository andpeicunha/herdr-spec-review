"""Talk to Herdr: open the reader pane, list pane cwds, and send the handoff prompt."""
from __future__ import annotations

import base64
import json
import os
import subprocess

PLUGIN_ID = "andpeicunha.spec-review"
READER_ENTRYPOINT = "reader"


def herdr_bin() -> str:
    return os.environ.get("HERDR_BIN_PATH", "herdr")


def _run(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([herdr_bin(), *args], capture_output=True, text=True, timeout=20)


def pane_cwds() -> list[str]:
    """Working directories of every Herdr pane, in every workspace."""
    try:
        result = _run(["pane", "list"])
        panes = json.loads(result.stdout)["result"]["panes"]
    except (OSError, subprocess.TimeoutExpired, ValueError, KeyError, TypeError):
        return []
    cwds = []
    for pane in panes:
        for key in ("foreground_cwd", "cwd"):
            value = pane.get(key)
            if value and value not in cwds:
                cwds.append(value)
    return cwds


def open_reader(
    source_pane: str, artifact: str = "", cwd: str = "", plugin_id: str = PLUGIN_ID
) -> tuple[bool, str]:
    """Open the reader zoomed over ``source_pane``; with ``artifact`` it skips the picker."""
    args = [
        "plugin", "pane", "open",
        "--plugin", plugin_id,
        "--entrypoint", READER_ENTRYPOINT,
        "--placement", "zoomed",
        "--target-pane", source_pane,
        "--env", f"SPEC_REVIEW_SOURCE_PANE={source_pane}",
        "--focus",
    ]
    if artifact:
        args += ["--env", f"SPEC_REVIEW_ARTIFACT={artifact}"]
    if cwd:
        args += ["--env", f"SPEC_REVIEW_CWD={cwd}", "--cwd", cwd]
    try:
        result = _run(args)
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)
    if result.returncode != 0:
        return False, (result.stderr or result.stdout or "herdr plugin pane open failed").strip()
    try:
        pane = json.loads(result.stdout)["result"]["plugin_pane"]["pane"]["pane_id"]
    except (ValueError, KeyError, TypeError):
        pane = ""
    return True, pane


def build_handoff_message(paths: list[str]) -> str:
    files = "\n".join(f"- {path}" for path in paths)
    return (
        "I left review comments as pending AI Notes in these SDD artifacts:\n\n"
        f"{files}\n\n"
        "Read the `# AI Notes` section of each file and follow its instructions. "
        "Apply every decision to the normal SDD structure (requirements, scenarios, "
        "design, tasks), delete each resolved note, and when no pending note is left "
        "remove the whole `# AI Notes` section, including the `---` above it. "
        "If a note needs my input, ask me instead of guessing.\n"
    )


def send_prompt(pane: str, prompt: str) -> tuple[bool, str]:
    """Send a prompt to the agent in ``pane``; fall back to typing it and pressing Enter."""
    try:
        result = _run(["agent", "prompt", pane, prompt])
        if result.returncode == 0:
            return True, ""
        fallback = _run(["pane", "send-text", pane, prompt])
        if fallback.returncode != 0:
            return False, (result.stderr or fallback.stderr or "Send failed").strip()
        enter = _run(["agent", "send-keys", pane, "Enter"])
        if enter.returncode != 0:
            return False, (enter.stderr or "Could not submit prompt").strip()
        return True, ""
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, str(error)


def copy_text_to_clipboard(text: str) -> None:
    """Copy through OSC 52, which works over SSH and inside Herdr panes."""
    encoded = base64.b64encode(text.encode("utf-8")).decode("ascii")
    os.write(1, f"\x1b]52;c;{encoded}\a".encode("ascii"))
