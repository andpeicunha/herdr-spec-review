## ADDED Requirements

### Requirement: Shared selection in the artifact reader / Seleção compartilhada no leitor de artefatos

The Spec Review artifact reader MUST use the shared blue selected-row style for the current block, including wrapped text, table rows, and code lines. The selected style MUST cover the whole display row and MUST not hide the text or the current-block marker.

O leitor de artefatos do Spec Review DEVE usar o destaque azul compartilhado no bloco atual, inclusive texto quebrado, linhas de tabela e linhas de código. O destaque DEVE cobrir toda a linha visual sem esconder o texto nem o marcador do bloco atual.

#### Scenario: Navigate a long paragraph / Navegar por um parágrafo longo

- **WHEN** the current block wraps onto multiple display rows
- **THEN** every row of that block has the same blue selection background as Comments
- **QUANDO** o bloco atual é quebrado em várias linhas visuais
- **ENTÃO** todas as linhas do bloco têm o mesmo fundo azul de seleção do Comments

#### Scenario: Navigate code and tables / Navegar por código e tabelas

- **WHEN** the current block is a code line, code-frame line, or table row
- **THEN** the blue selection remains visible across the full display row and its content stays readable
- **QUANDO** o bloco atual é uma linha de código, moldura de código ou linha de tabela
- **ENTÃO** a seleção azul continua visível em toda a linha e seu conteúdo permanece legível
