import os
import tempfile
import unittest
from unittest.mock import patch

from specreview.ainotes import Note, add_note_to_file, pending_notes
from specreview.editor import TextBuffer
from specreview.ui import _EDITOR_KEYS, App, Reader

ORIGINAL = "## Why\n\nPrimeiro parágrafo.\n\nSegundo parágrafo.\n"


class ReaderNoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        patcher = patch.dict("os.environ", {"HERDR_PLUGIN_STATE_DIR": self.tmp.name})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.path = os.path.join(self.tmp.name, "design.md")
        with open(self.path, "w", encoding="utf-8") as out:
            out.write(ORIGINAL)
        self.reader = Reader(App(""), self.path)
        self.reader.cursor = 1  # "Primeiro parágrafo."

    def file(self):
        with open(self.path, encoding="utf-8") as source:
            return source.read()

    def test_new_edited_and_deleted_note_round_trip(self):
        reader = self.reader

        self.assertEqual(reader.commit_note("First", None), "NOTE-001 saved to the file")
        note = reader.notes_on_block(1)[0]
        self.assertEqual(reader.commit_note("  First, edited \n", note), "NOTE-001 updated")
        self.assertEqual([n.human_comment for n in pending_notes(self.file())], ["First, edited"])
        self.assertEqual(reader.touched_pending(), 1)

        self.assertEqual(reader.commit_note("   ", reader.notes_on_block(1)[0]), "NOTE-001 deleted")
        self.assertEqual(self.file(), ORIGINAL)
        self.assertEqual(reader.touched_pending(), 0)

    def test_pending_count_covers_every_note_in_the_file(self):
        self.assertEqual(self.reader.pending_count(), 0)
        self.reader.commit_note("First", None)
        self.reader.cursor = 2
        self.reader.commit_note("Second", None)
        self.assertEqual(self.reader.pending_count(), 2)
        # A fresh reader has touched nothing, but the notes are still pending.
        fresh = Reader(App(""), self.path)
        self.assertEqual((fresh.touched_pending(), fresh.pending_count()), (0, 2))

    def test_empty_new_note_writes_nothing(self):
        self.assertEqual(self.reader.commit_note("  ", None), "Empty comment; nothing saved")
        self.assertEqual(self.file(), ORIGINAL)

    def test_editing_a_note_that_vanished_reports_an_error(self):
        ghost = Note("NOTE-099", "pending", 3, 3, "Primeiro parágrafo.", "x")

        self.assertEqual(self.reader.commit_note("new text", ghost), "Error: NOTE-099 is no longer in the file")
        self.assertEqual(self.reader.commit_note("", ghost), "Error: NOTE-099 is no longer in the file")
        self.assertEqual(self.file(), ORIGINAL)

    def test_several_notes_on_one_block_are_edited_independently(self):
        reader = self.reader
        reader.commit_note("one", None)
        reader.commit_note("two", None)
        reader.cursor = 2
        reader.commit_note("elsewhere", None)
        reader.cursor = 1

        on_block = reader.notes_on_block(1)
        self.assertEqual([n.human_comment for n in on_block], ["one", "two"])
        self.assertEqual([n.human_comment for n in reader.notes_on_block(2)], ["elsewhere"])
        self.assertEqual(reader.notes_on_block(0), [])

        reader.commit_note("two, edited", on_block[1])
        self.assertEqual(
            [n.human_comment for n in pending_notes(self.file())], ["one", "two, edited", "elsewhere"]
        )
        reader.commit_note("", on_block[0])
        self.assertEqual([n.note_id for n in pending_notes(self.file())], ["NOTE-002", "NOTE-003"])

    def test_notes_whose_text_was_lost_sit_on_the_first_block(self):
        add_note_to_file(self.path, 3, 3, "Texto que não existe mais", "órfã")
        reader = Reader(App(""), self.path)

        self.assertEqual([n.human_comment for n in reader.notes_on_block(0)], ["órfã"])

    def test_note_created_and_deleted_in_one_reading_is_not_offered_for_sending(self):
        reader = self.reader
        reader.commit_note("temporary", None)
        reader.commit_note("", reader.notes_on_block(1)[0])

        self.assertEqual(reader.touched_pending(), 0)

    def test_notes_only_read_are_not_offered_for_sending(self):
        add_note_to_file(self.path, 3, 3, "Primeiro parágrafo.", "old note")
        reader = Reader(App(""), self.path)

        self.assertEqual(reader.touched_pending(), 0)
        reader.commit_note("old note, edited", reader.notes_on_block(1)[0])
        self.assertEqual(reader.touched_pending(), 1)


class ClearLineTests(unittest.TestCase):
    def test_clear_line_erases_only_the_current_line(self):
        buffer = TextBuffer("one\ntwo\nthree")
        buffer.row, buffer.col = 1, 2
        buffer.clear_line()

        self.assertEqual(buffer.text, "one\n\nthree")
        self.assertEqual((buffer.row, buffer.col), (1, 0))

    def test_ctrl_u_is_bound_in_the_note_box(self):
        self.assertIs(_EDITOR_KEYS["\x15"], TextBuffer.clear_line)


if __name__ == "__main__":
    unittest.main()
