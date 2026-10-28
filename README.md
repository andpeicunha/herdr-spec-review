# spec-review

A [Herdr](https://herdr.io) plugin for reviewing spec-driven development (SDD)
artifacts. It finds open [OpenSpec](https://github.com/Fission-AI/OpenSpec)
changes in a repository and all of its git worktrees, opens an artifact in a
terminal reader, and lets you leave **AI Notes** that the agent turns into
changes to the spec.

## Flow

1. Open the plugin (Herdr action) or ask your agent to open an artifact (MCP).
2. Pick the repository, the change, and the artifact (`proposal.md`,
   `design.md`, `specs/**/spec.md`, `tasks.md`).
3. Read it block by block and press `c` on any block to write a note.
   `Ctrl+S` saves the note **into the Markdown file**.
4. Close with `q`. If you saved notes, confirm and the agent in your session
   gets a short message pointing to the file.
5. The agent applies each note to the SDD structure and deletes it. When no
   note is pending, the `# AI Notes` section is removed: the final artifact is
   always clean.

Notes use the same format as the
[`ai-notes-md`](https://github.com/andpeicunha) VS Code extension, so notes
written in one tool show up in the other.

## Requirements

- [Herdr](https://herdr.io) 0.9.5 or newer.
- Python 3 with `curses` support, and `git`.

## Install

Local development:

```sh
herdr plugin link .
```

Bind the action in your Herdr configuration:

```toml
[[keys.command]]
key = "prefix+r"
type = "plugin_action"
command = "andpeicunha.spec-review.open"
description = "spec-review: open"
```

### MCP server for agents

Register the stdio server once per agent:

```sh
# Claude Code
claude mcp add --scope user spec-review -- /path/to/herdr-spec-review/bin/spec-review-mcp
```

```toml
# Codex: ~/.codex/config.toml
[mcp_servers.spec-review]
command = "/path/to/herdr-spec-review/bin/spec-review-mcp"
```

Tools: `list_open_changes`, `list_artifacts`, `open_artifact`,
`pending_notes`. The agent must run inside a Herdr pane: `open_artifact`
opens the reader next to it, and the handoff goes back to it. Agents are told
to open the reader only when you ask.

## Keys

Picker: `↑`/`↓` move · `Enter` open · `/` filter · `r` other repositories ·
`Esc` back · `q` quit.

Reader:

| Key | Action |
| --- | --- |
| `↑` / `↓` | Previous / next block |
| `Shift+↑` / `Shift+↓` | Page up / down |
| `+` / `-` | Zoom in / out (see below) |
| `0` | Reset the zoom |
| `n` / `N` | Next / previous heading |
| `c` | Write an AI Note on the current block |
| `Ctrl+S` | Save the note into the file |
| `R` | Reload after the file changed on disk |
| `q` / `Esc` | Close (asks before sending new notes to the agent) |

## Zoom

A terminal program cannot change the font size, so the zoom is simulated with the
layout. It only affects the text inside the reader pane, and the level is saved
(one level for all panes).

- **Zoom in** (`+`, up to `+3`): a narrower, centered reading column, so there are
  fewer words per line.
- **Zoom out** (`-`, down to `-2`): the full width and fewer blank rows, so more
  content fits on the screen.
- **Tables** always use the full pane width, at every level. A table that is
  still too wide has its widest cells cut with `…`.

## Settings

Put settings in `config.env` in the plugin config directory
(`herdr plugin config-dir andpeicunha.spec-review`):

| Setting | Default | Effect |
| --- | --- | --- |
| `SPEC_REVIEW_ROOTS` | unset | `:`-separated folders whose child repos appear under `r` |

## Development

```sh
python3 -m unittest discover -s tests -v
```

The design and specs live in `openspec/changes/explore-sdd-review-plugin/`.
