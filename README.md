# spec-review

A [Herdr](https://herdr.io) plugin for reviewing spec-driven development (SDD)
artifacts. It finds open [OpenSpec](https://github.com/Fission-AI/OpenSpec)
changes in a repository and all of its git worktrees, opens an artifact in a
terminal reader, and lets you leave **AI Notes** that the agent turns into
changes to the spec.

> **Beta (`0.1.0-beta.4`).** It works end to end with Claude Code in Herdr, but the
> behavior and the notes format may still change. See [Known limits](#known-limits-beta).

## Flow

1. Open the plugin (Herdr action) or ask your agent to open an artifact (MCP).
2. Pick the repository, the change, and the artifact (`proposal.md`,
   `design.md`, `specs/**/spec.md`, `tasks.md`).
3. Read it block by block and press `c` on any block (a paragraph, a list item, a
   single table row, a line of code) to write a note. Press `C` to edit a saved
   note; erase its text and save to delete it.
   `Ctrl+S` saves the note **into the Markdown file**.
4. Close with `q`. If you saved notes, confirm and the agent in your session
   gets a short message pointing to the file.
5. The agent applies each note to the SDD structure and deletes it. When no
   note is pending, the `# AI Notes` section is removed: the final artifact is
   always clean.

Notes use the same format as the
[`ai-notes-md`](https://github.com/andpeicunha/ai-notes-md) VS Code extension, so notes
written in one tool show up in the other.

## Requirements

- [Herdr](https://herdr.io) 0.9.5 or newer.
- Python 3 with `curses` support, and `git`.

## Install

```sh
herdr plugin install andpeicunha/herdr-spec-review
```

For local development, link a checkout instead: `herdr plugin link .`

Bind the action in your Herdr configuration (pick a key that is free in your setup):

```toml
[[keys.command]]
key = "prefix+shift+s"
type = "plugin_action"
command = "andpeicunha.spec-review.open"
description = "spec-review: open"
```

### MCP server for agents

Register the stdio server once per agent. Use a **clone of this repository** at a
fixed path (`git clone https://github.com/andpeicunha/herdr-spec-review`): Herdr
installs every update of a plugin into a new directory, so a path inside the
installed plugin would stop working after an update.

```sh
# Claude Code
claude mcp add --scope user spec-review -- /path/to/herdr-spec-review/bin/spec-review-mcp
```

```toml
# Codex: ~/.codex/config.toml
[mcp_servers.spec-review]
command = "/path/to/herdr-spec-review/bin/spec-review-mcp"
# Codex only passes the variables you list; open_artifact needs the agent's Herdr pane.
env_vars = ["HERDR_PANE_ID", "HERDR_WORKSPACE_ID", "HERDR_TAB_ID", "HERDR_BIN_PATH", "HERDR_SOCKET_PATH", "HERDR_ENV"]
```

Tools: `list_open_changes`, `list_artifacts`, `open_artifact`,
`pending_notes`. The agent must run inside a Herdr pane: `open_artifact`
opens the reader next to it, and the handoff goes back to it. Agents are told
to open the reader only when you ask.

## Keys

Picker: `↑`/`↓` move · `Enter` open · `/` filter · `r` other repositories ·
`Esc` back · `q` quit · `?` all shortcuts.

Reader:

| Key | Action |
| --- | --- |
| `↑` / `↓` | Previous / next block |
| `Alt+↑` / `Alt+↓` | Half a page up / down (also `u` / `d`, `Page Up` / `Page Down`) |
| `+` / `-` | Zoom in / out (see below) |
| `0` | Reset the zoom |
| `n` / `N` | Next / previous heading |
| `c` | Add a new AI Note on the current block |
| `C` | Edit a saved note on the current block (press `1`-`9` to choose when there are several) |
| `Ctrl+S` | Save the note into the file (on an edited note, empty text deletes it) |
| `Ctrl+U` | Clear the current line in the note box |
| `R` | Reload after the file changed on disk |
| `?` | Show all the shortcuts in a window (`Esc`, `?` or `q` closes it) |
| `q` / `Esc` | Close (asks before sending new notes to the agent) |

## Zoom

A terminal program cannot change the font size, so the zoom is simulated with the
layout. It only affects the text inside the reader pane, and the level is saved
(one level for all panes).

- **Zoom in** (`+`, up to `+3`): a narrower, centered reading column, so there are
  fewer words per line.
- **Zoom out** (`-`, down to `-2`): the full width and fewer blank rows, so more
  content fits on the screen.
- **Tables** always use the full pane width, at every level. Every table row is its
  own block. A table that does not fit shows as one record per row (`Name: value`
  lines with the full text, no cut cells) instead of an aligned table.

## Settings

Put settings in `config.env` in the plugin config directory
(`herdr plugin config-dir andpeicunha.spec-review`):

| Setting | Default | Effect |
| --- | --- | --- |
| `SPEC_REVIEW_ROOTS` | unset | `:`-separated folders whose child repos appear under `r` |

## Known limits (beta)

- **No "ready to archive" check yet.** `openspec archive` copies a leftover
  `# AI Notes` section into the main specs without a warning. Resolve or delete all
  notes before archiving.
- **Tested mostly with Claude Code.** The Codex setup above works by configuration,
  but it has had less testing.
- **The MCP server needs a fixed path** (see above), so it can run a different
  version than the plugin installed by Herdr until you `git pull` the clone.
- OpenSpec changes only; other SDD layouts are not supported.

## Development

```sh
python3 -m unittest discover -s tests -v
```

To check the curses UI without a real terminal, run it in a virtual terminal:

```sh
SPEC_REVIEW_ARTIFACT=path/to/proposal.md SPEC_REVIEW_SOURCE_PANE=fake \
  uv run --no-project --with pyte python3 tools/render_screen.py spec_review.py 90 24 j c 'a note' '\x13' @
```

The specs live in `openspec/specs/`. The design history of the MVP is in
`openspec/changes/archive/2026-10-29-explore-sdd-review-plugin/`, and the open
follow-ups are in `openspec/changes/spec-review-beta-followups/`.
