import os
import tempfile
import unittest

from specreview.document import load_document
from specreview.layout import build_display_rows
from specreview.markdown import (
    BOLD_OFF,
    BOLD_ON,
    format_markdown_lines,
    group_logical_blocks,
    mark_inline_markup,
)

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

    def test_bold_can_contain_code_spans(self):
        text = "**Passo 3 — Use o campo `userId`, não o nome.** A lista já tem o `userId`."

        self.assertEqual(
            mark_inline_markup(text),
            f"{BOLD_ON}Passo 3 — Use o campo userId, não o nome.{BOLD_OFF} A lista já tem o userId.",
        )

    def test_bold_pairs_across_code_spans_without_leaking_to_later_bold(self):
        text = (
            "**Passo 4 — Serviço próprio: `example-service`.** (Neste exemplo) "
            "É um serviço **corporativo**, pensado para `a` e `b`."
        )

        self.assertEqual(
            mark_inline_markup(text),
            f"{BOLD_ON}Passo 4 — Serviço próprio: example-service.{BOLD_OFF} (Neste exemplo) "
            f"É um serviço {BOLD_ON}corporativo{BOLD_OFF}, pensado para a e b.",
        )
        self.assertEqual(
            mark_inline_markup("O nível é o **mesmo de `x-y`**, mas **no início**"),
            f"O nível é o {BOLD_ON}mesmo de x-y{BOLD_OFF}, mas {BOLD_ON}no início{BOLD_OFF}",
        )

    def test_unpaired_markers_and_markers_inside_code_stay_literal(self):
        self.assertEqual(mark_inline_markup("a ** b"), "a ** b")
        self.assertEqual(mark_inline_markup("2 ** 3 e 4**5"), "2 ** 3 e 4**5")
        self.assertEqual(mark_inline_markup("só `**x**` aqui"), "só **x** aqui")

    def test_list_items_keep_indentation_but_other_blocks_do_not(self):
        self.assertEqual(
            group_logical_blocks(["- a", "  - b", "    - c", "  ## Title", "  > quote"]),
            ["- a", "  - b", "    - c", "## Title", "> quote"],
        )

    def test_nested_bullets_use_an_inner_marker_per_level(self):
        blocks = ["- a", "  - b", "    - c", "  - d", "- e"]

        self.assertEqual(
            [text for text, _kind in format_markdown_lines(blocks)],
            ["  • a", "    ◦ b", "      ◦ c", "    ◦ d", "  • e"],
        )

    def test_nesting_works_with_four_space_steps_numbers_and_resets(self):
        self.assertEqual(
            [text for text, _kind in format_markdown_lines(["- a", "    - b"])],
            ["  • a", "    ◦ b"],
        )
        self.assertEqual(
            [text for text, _kind in format_markdown_lines(["1. a", "   - b", "2. c"])],
            ["  1. a", "    ◦ b", "  2. c"],
        )
        self.assertEqual(
            [text for text, _kind in format_markdown_lines(["- a", "  - b", "Text", "  - c"])],
            ["  • a", "    ◦ b", "Text", "  • c"],
        )

    def test_wrapped_list_items_get_a_hanging_indent(self):
        rows = build_display_rows(["    ◦ " + "palavra " * 8], {}, width=24)
        continuation = [text for kind, _index, text in rows if kind == "continuation"]

        self.assertTrue(rows[0][2].startswith("    ◦ palavra"))
        self.assertGreater(len(continuation), 1)
        self.assertTrue(all(t.startswith(" " * 6 + "palavra") for t in continuation))

    def test_wrapped_paragraphs_have_no_stray_leading_space(self):
        rows = build_display_rows(["uma frase que quebra em varias linhas curtas"], {}, width=12)

        self.assertGreater(len(rows), 2)
        self.assertFalse(any(text.startswith(" ") for _kind, _index, text in rows))

    def test_code_blocks_keep_their_whitespace(self):
        rows = build_display_rows(
            ["    indented code line that is long"], {}, width=14, preserve_space={0}
        )

        self.assertTrue(rows[0][2].startswith("    indented"))

    def test_nested_items_map_to_their_own_file_lines(self):
        with tempfile.TemporaryDirectory() as folder:
            path = os.path.join(folder, "design.md")
            with open(path, "w", encoding="utf-8") as out:
                out.write("- Passo 5\n  - Entrada: token\n    continua aqui\n  - Saída\n- Passo 6\n")
            doc = load_document(path)

        self.assertEqual(
            [(block.text.strip()[:14], block.start, block.end) for block in doc.blocks],
            [("- Passo 5", 1, 1), ("- Entrada: tok", 2, 3), ("- Saída", 4, 4), ("- Passo 6", 5, 5)],
        )

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
