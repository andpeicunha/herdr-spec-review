import os
import tempfile
import unittest

from specreview.document import load_document
from specreview.markdown import group_logical_blocks

WRAPPED_LIST = """## Why

- A receita lista os ingredientes na ordem em que entram. Primeiro o
  tempero, depois o molho, sempre mexendo devagar.
- Misture com cuidado (ex.: use uma colher de
pau) para não quebrar.

1. Separe os ingredientes na bancada
   e meça cada quantidade.
2. Segundo passo.

Parágrafo depois da lista
em duas linhas."""


class MarkdownTests(unittest.TestCase):
    def test_wrapped_list_items_stay_one_block(self):
        self.assertEqual(
            group_logical_blocks(WRAPPED_LIST.splitlines()),
            [
                "## Why",
                "- A receita lista os ingredientes na ordem em que entram. Primeiro o tempero, depois o molho, sempre mexendo devagar.",
                "- Misture com cuidado (ex.: use uma colher de pau) para não quebrar.",
                "1. Separe os ingredientes na bancada e meça cada quantidade.",
                "2. Segundo passo.",
                "Parágrafo depois da lista em duas linhas.",
            ],
        )

    def test_blank_line_or_new_block_ends_the_item(self):
        lines = ["- item", "", "paragraph", "- next", "## Heading", "text"]

        self.assertEqual(
            group_logical_blocks(lines), ["- item", "paragraph", "- next", "## Heading", "text"]
        )

    def test_rule_does_not_open_a_list_item(self):
        self.assertEqual(group_logical_blocks(["---", "text"]), ["---", "text"])

    def test_wrapped_item_maps_to_all_its_file_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "proposal.md")
            with open(path, "w", encoding="utf-8") as out:
                out.write(WRAPPED_LIST + "\n")
            doc = load_document(path)

        ranges = [(block.text[:12], block.start, block.end) for block in doc.blocks]

        self.assertEqual(
            ranges,
            [
                ("## Why", 1, 1),
                ("- A receita ", 3, 4),
                ("- Misture co", 5, 6),
                ("1. Separe os", 8, 9),
                ("2. Segundo p", 10, 10),
                ("Parágrafo de", 12, 13),
            ],
        )


if __name__ == "__main__":
    unittest.main()
