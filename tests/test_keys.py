import curses
import unittest

from specreview.keys import ALT_DOWN, ALT_UP, decode_escape


class KeyDecodingTests(unittest.TestCase):
    def test_alt_arrows_in_every_form(self):
        self.assertEqual(decode_escape([curses.KEY_UP]), ALT_UP)
        self.assertEqual(decode_escape([curses.KEY_DOWN]), ALT_DOWN)
        self.assertEqual(decode_escape([ord(c) for c in "[1;3A"]), ALT_UP)
        self.assertEqual(decode_escape([ord(c) for c in "[1;3B"]), ALT_DOWN)

    def test_unknown_sequences_are_a_plain_escape(self):
        self.assertEqual(decode_escape([]), 27)
        self.assertEqual(decode_escape([ord("x")]), 27)
