import os
import tempfile
import unittest

from specreview.ainotes import add_note_to_file
from specreview.document import load_document

SPEC = """# Delta

## ADDED Requirements

### Requirement: Login

O sistema MUST validar o token
antes de carregar dados.

#### Scenario: Token inválido

- **WHEN** o token expirou
- **THEN** o sistema recusa

| Campo | Tipo |
|---|---|
| token | string |

```sh
curl /login
echo ok
```
"""


class DocumentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, "spec.md")
        with open(self.path, "w", encoding="utf-8") as out:
            out.write(SPEC)

    def tearDown(self):
        self.tmp.cleanup()

    def test_blocks_keep_real_line_ranges(self):
        doc = load_document(self.path)
        ranges = {block.text.splitlines()[0]: (block.start, block.end) for block in doc.blocks}

        self.assertEqual(ranges["### Requirement: Login"], (5, 5))
        self.assertEqual(ranges["O sistema MUST validar o token antes de carregar dados."], (7, 8))
        self.assertEqual(ranges["- **THEN** o sistema recusa"], (13, 13))
        self.assertEqual(ranges["| Campo | Tipo |"], (15, 16))  # header + separator line
        self.assertEqual(ranges["| token | string |"], (17, 17))
        self.assertEqual(ranges["echo ok"], (21, 21))
        self.assertEqual(doc.block_source(1), "## ADDED Requirements")

    def test_saved_note_maps_back_to_its_block(self):
        doc = load_document(self.path)
        index = next(i for i, b in enumerate(doc.blocks) if b.text.startswith("O sistema"))
        block = doc.blocks[index]
        add_note_to_file(self.path, block.start, block.end, doc.block_source(index), "Qual token?")

        reloaded = load_document(self.path)

        self.assertEqual(len(reloaded.blocks), len(doc.blocks))
        self.assertEqual([n.human_comment for n in reloaded.notes], ["Qual token?"])
        self.assertEqual(reloaded.note_blocks["NOTE-001"], index)
        self.assertEqual(reloaded.notes[0].selected_text, "O sistema MUST validar o token\nantes de carregar dados.")

    def test_note_follows_text_after_lines_shift(self):
        doc = load_document(self.path)
        index = next(i for i, b in enumerate(doc.blocks) if b.text.startswith("- **THEN**"))
        add_note_to_file(self.path, doc.blocks[index].start, doc.blocks[index].end, doc.block_source(index), "ok?")
        with open(self.path, encoding="utf-8") as source:
            text = source.read()
        with open(self.path, "w", encoding="utf-8") as out:
            out.write("Intro nova.\n\nOutra linha.\n\n" + text)

        reloaded = load_document(self.path)
        target = reloaded.note_blocks["NOTE-001"]

        self.assertEqual(reloaded.blocks[target].text, "- **THEN** o sistema recusa")


if __name__ == "__main__":
    unittest.main()
