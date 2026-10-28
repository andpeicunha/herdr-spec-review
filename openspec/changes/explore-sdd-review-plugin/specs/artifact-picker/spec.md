# Delta de artifact-picker

## ADDED Requirements

### Requirement: Escolher a change

O plugin MUST mostrar as changes encontradas em uma lista navegável por
teclado, com o nome da change, o worktree/branch e o número de notas
pendentes em todos os seus artefatos.

#### Scenario: Change com notas pendentes

- **GIVEN** a change `add-login` tem 2 notas `Status: pending` em `design.md`
- **WHEN** a lista de changes é exibida
- **THEN** a entrada de `add-login` mostra 2 notas pendentes

#### Scenario: Filtrar por texto

- **GIVEN** a lista tem mais changes do que cabem na tela
- **WHEN** o usuário digita parte do nome de uma change
- **THEN** a lista mostra só as changes cujo nome contém esse texto

### Requirement: Escolher o artefato

Depois de escolher a change, o plugin MUST listar os artefatos existentes
(`proposal.md`, `design.md`, `tasks.md` e cada `specs/**/spec.md`), na ordem do
fluxo SDD, com o número de notas pendentes de cada um.

#### Scenario: Change sem design

- **GIVEN** a change tem `proposal.md`, `tasks.md` e `specs/auth/spec.md`, mas não `design.md`
- **WHEN** o usuário escolhe a change
- **THEN** a lista mostra `proposal.md`, `specs/auth/spec.md` e `tasks.md`
- **AND** não mostra `design.md`

#### Scenario: Voltar para a lista de changes

- **GIVEN** a lista de artefatos está aberta
- **WHEN** o usuário pressiona `Esc`
- **THEN** o plugin volta para a lista de changes

### Requirement: Escolher outro repositório

O picker MUST abrir no repositório da pane atual e MUST permitir trocar para
outro repositório, listando os repositórios das panes abertas no Herdr e os que
têm `openspec/` dentro das raízes configuradas em `SPEC_REVIEW_ROOTS`.

#### Scenario: Revisar SDD de outro projeto

- **GIVEN** `SPEC_REVIEW_ROOTS=~/Apps:~/Projects` e `~/Projects/auth-service` tem `openspec/`
- **WHEN** o usuário abre a lista de repositórios no picker
- **THEN** `~/Projects/auth-service` aparece na lista
- **AND** ao escolher, o picker mostra as changes em aberto desse repositório

#### Scenario: Pane atual fora de um repositório

- **GIVEN** a pane atual não está em um repositório git
- **WHEN** o usuário abre o plugin
- **THEN** o picker começa pela lista de repositórios

### Requirement: Retomar a última leitura

O plugin MUST lembrar, por repositório, a última change e o último artefato
abertos, e MUST pré-selecioná-los na próxima abertura.

#### Scenario: Reabrir depois de fechar

- **GIVEN** o usuário leu `add-login/design.md` e fechou o plugin
- **WHEN** ele abre o plugin de novo no mesmo repositório
- **THEN** `add-login` e `design.md` já aparecem selecionados
