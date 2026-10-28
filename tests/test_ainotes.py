import os
import tempfile
import unittest

from specreview.ainotes import (
    INSTRUCTIONS,
    Note,
    add_note_to_file,
    append_note,
    body_text,
    delete_note_in_file,
    locate_note,
    next_note_id,
    parse_notes,
    pending_notes,
    remove_note,
    replace_comment,
    update_note_in_file,
)

DOC = "# Design\n\nThe system must validate the token.\nSecond line.\n"

# Exactly what ai-notes-md v0.0.17 writes for one note.
VSCODE_FILE = (
    DOC
    + "\n---\n\n# AI Notes\n\n"
    + INSTRUCTIONS
    + "\n\n## NOTE-003\n\nStatus: pending\n\nLines: 3-4\n\nSelected Text:\n\n"
    + "> The system must validate the token.\n> Second line.\n\n"
    + "Human Comment:\n\nAlso support B2B tenants.\nAnd SSO.\n\n"
    + "Expected AI Action:\n\nNot specified.\n\nCreated At:\n\n2026-05-13 10:30\n"
)


def note(note_id="NOTE-001", start=3, text="The system must validate the token.", comment="Why?"):
    return Note(note_id, "pending", start, start, text, comment, "Not specified.", "2026-10-28 10:00")


class AiNotesTests(unittest.TestCase):
    def test_parses_a_note_written_by_vscode_extension(self):
        notes = parse_notes(VSCODE_FILE)

        self.assertEqual(len(notes), 1)
        parsed = notes[0]
        self.assertEqual(parsed.note_id, "NOTE-003")
        self.assertTrue(parsed.pending)
        self.assertEqual((parsed.start_line, parsed.end_line), (3, 4))
        self.assertEqual(parsed.selected_text, "The system must validate the token.\nSecond line.")
        self.assertEqual(parsed.human_comment, "Also support B2B tenants.\nAnd SSO.")
        self.assertEqual(parsed.expected_action, "Not specified.")
        self.assertEqual(parsed.created_at, "2026-05-13 10:30")

    def test_body_hides_section_and_separator(self):
        self.assertEqual(body_text(VSCODE_FILE), DOC)
        self.assertEqual(body_text(DOC), DOC)

    def test_first_note_creates_section_like_the_extension(self):
        text = append_note(DOC, note())

        self.assertTrue(text.startswith(DOC + "\n---\n\n# AI Notes\n\n" + INSTRUCTIONS + "\n\n## NOTE-001\n"))
        self.assertEqual(parse_notes(text)[0].human_comment, "Why?")

    def test_next_id_continues_after_vscode_notes(self):
        self.assertEqual(next_note_id(VSCODE_FILE), "NOTE-004")
        self.assertEqual(next_note_id(DOC), "NOTE-001")

    def test_appending_to_existing_section_round_trips(self):
        text = append_note(VSCODE_FILE, note("NOTE-004", comment="Second note"))

        self.assertEqual([n.note_id for n in parse_notes(text)], ["NOTE-003", "NOTE-004"])
        lines = text.splitlines()
        self.assertEqual(lines.count("# AI Notes"), 1)
        self.assertEqual(lines.count(INSTRUCTIONS_HEADING_TEXT), 1)

    def test_removing_last_pending_note_cleans_everything(self):
        self.assertEqual(remove_note(VSCODE_FILE, "NOTE-003"), DOC)

    def test_removing_one_of_two_notes_keeps_section(self):
        text = append_note(VSCODE_FILE, note("NOTE-004"))
        cleaned = remove_note(text, "NOTE-003")

        self.assertEqual([n.note_id for n in pending_notes(cleaned)], ["NOTE-004"])
        self.assertIn("\n---\n\n# AI Notes", cleaned)

    def test_add_note_to_file_writes_atomically_and_keeps_body(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "design.md")
            with open(path, "w", encoding="utf-8") as out:
                out.write(DOC)
            first = add_note_to_file(path, 3, 3, "The system must validate the token.", "  Q1  ")
            second = add_note_to_file(path, 4, 4, "Second line.", "Q2")
            with open(path, encoding="utf-8") as source:
                text = source.read()

            self.assertEqual((first.note_id, second.note_id), ("NOTE-001", "NOTE-002"))
            self.assertEqual(body_text(text), DOC)
            self.assertEqual([n.human_comment for n in pending_notes(text)], ["Q1", "Q2"])
            self.assertEqual(os.listdir(folder), ["design.md"])

    def test_replace_comment_changes_only_the_human_comment(self):
        updated = replace_comment(VSCODE_FILE, "NOTE-003", "New text.\nSecond line.")
        before, after = parse_notes(VSCODE_FILE)[0], parse_notes(updated)[0]

        self.assertEqual(after.human_comment, "New text.\nSecond line.")
        self.assertEqual(
            (after.note_id, after.status, after.start_line, after.end_line, after.selected_text,
             after.expected_action, after.created_at),
            (before.note_id, before.status, before.start_line, before.end_line, before.selected_text,
             before.expected_action, before.created_at),
        )
        self.assertEqual(body_text(updated), DOC)
        self.assertEqual(updated.count("Human Comment:"), 1)

    def test_replace_comment_touches_only_the_target_note(self):
        text = append_note(VSCODE_FILE, note("NOTE-004", comment="Keep me"))
        updated = replace_comment(text, "NOTE-004", "Changed")

        self.assertEqual(
            [n.human_comment for n in parse_notes(updated)],
            ["Also support B2B tenants.\nAnd SSO.", "Changed"],
        )

    def test_replace_comment_refuses_missing_resolved_or_body_headings(self):
        self.assertIsNone(replace_comment(VSCODE_FILE, "NOTE-009", "x"))
        self.assertIsNone(replace_comment(DOC, "NOTE-001", "x"))
        resolved = VSCODE_FILE.replace("Status: pending", "Status: resolved")
        self.assertIsNone(replace_comment(resolved, "NOTE-003", "x"))
        fake = DOC + "\n## NOTE-003\n\nStatus: pending\n\nHuman Comment:\n\nin body\n"
        self.assertIsNone(replace_comment(fake, "NOTE-003", "x"))

    def test_update_and_delete_note_in_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "design.md")
            with open(path, "w", encoding="utf-8") as out:
                out.write(DOC)
            first = add_note_to_file(path, 3, 3, "The system must validate the token.", "Q1")
            second = add_note_to_file(path, 4, 4, "Second line.", "Q2")

            self.assertTrue(update_note_in_file(path, first.note_id, "Q1 edited"))
            self.assertFalse(update_note_in_file(path, "NOTE-099", "x"))
            with open(path, encoding="utf-8") as source:
                self.assertEqual([n.human_comment for n in pending_notes(source.read())], ["Q1 edited", "Q2"])

            self.assertTrue(delete_note_in_file(path, first.note_id))
            self.assertFalse(delete_note_in_file(path, first.note_id))
            self.assertTrue(delete_note_in_file(path, second.note_id))
            with open(path, encoding="utf-8") as source:
                self.assertEqual(source.read(), DOC)
            self.assertEqual(os.listdir(folder), ["design.md"])

    def test_locate_note_reanchors_after_lines_move(self):
        lines = ["# Design", "", "new", "new", "The system must validate the token.", "Second line."]

        self.assertEqual(locate_note(note(start=3), lines), 5)
        self.assertEqual(locate_note(note(start=5), lines), 5)
        self.assertIsNone(locate_note(note(text="Gone text"), lines))


INSTRUCTIONS_HEADING_TEXT = "## Instructions for AI Agents"

if __name__ == "__main__":
    unittest.main()
