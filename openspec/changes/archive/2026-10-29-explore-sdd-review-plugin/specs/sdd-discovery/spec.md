# Delta de sdd-discovery

## ADDED Requirements

### Requirement: Listar changes OpenSpec em aberto

O plugin MUST listar todas as changes OpenSpec em aberto do repositório da pane
atual, ou seja, cada diretório em `openspec/changes/` exceto `archive/`.

#### Scenario: Repositório com changes em aberto e arquivadas

- **GIVEN** o repositório tem `openspec/changes/add-login/` e `openspec/changes/archive/2026-01-old/`
- **WHEN** o usuário abre o plugin a partir de uma pane nesse repositório
- **THEN** a lista mostra `add-login`
- **AND** a lista não mostra nada de `archive/`

#### Scenario: Repositório sem OpenSpec

- **GIVEN** o repositório não tem `openspec/changes/`
- **WHEN** o usuário abre o plugin
- **THEN** o plugin mostra uma mensagem clara de que não há changes em aberto
- **AND** não abre o leitor

### Requirement: Incluir git worktrees

O plugin MUST procurar changes em aberto no checkout principal e em todos os
git worktrees do mesmo repositório, e MUST identificar em qual worktree e
branch cada change está.

#### Scenario: Mesma change em dois worktrees

- **GIVEN** `add-login` existe no checkout principal (branch `main`) e no worktree `.worktrees/login` (branch `feat/login`)
- **WHEN** o usuário abre o plugin
- **THEN** a lista mostra duas entradas para `add-login`
- **AND** cada entrada mostra o caminho do worktree e a branch

#### Scenario: Pane aberta dentro de um worktree

- **GIVEN** a pane atual está em um worktree, não no checkout principal
- **WHEN** o usuário abre o plugin
- **THEN** a lista também inclui as changes do checkout principal e dos outros worktrees

### Requirement: Descoberta a partir do cwd da pane

O plugin MUST usar o diretório de trabalho da pane de origem (contexto do
Herdr) para achar o repositório, e não o diretório do próprio plugin.

#### Scenario: Pane fora de um repositório git

- **GIVEN** o cwd da pane de origem não está dentro de um repositório git
- **WHEN** o usuário abre o plugin
- **THEN** a descoberta não retorna repositório atual
- **AND** o picker começa pela lista de repositórios (ver artifact-picker)
