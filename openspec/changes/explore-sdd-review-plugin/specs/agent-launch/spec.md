# Delta de agent-launch

## ADDED Requirements

### Requirement: Servidor MCP como entrada padrão do agente

O plugin MUST incluir um servidor MCP via stdio, em Python sem dependências
externas, que os agentes registram uma vez e usam para abrir artefatos no leitor.

#### Scenario: Agente abre a proposal que acabou de criar

- **GIVEN** o agente está em uma pane do Herdr e acabou de escrever `openspec/changes/add-login/proposal.md`
- **AND** o usuário pede para abrir a proposal no plugin
- **WHEN** o agente chama a tool `open_artifact` com esse caminho
- **THEN** o leitor abre direto nesse artefato, ao lado da pane do agente
- **AND** sem passar pelo picker

### Requirement: Tools do MCP

O servidor MCP MUST expor as tools `list_open_changes`, `list_artifacts`,
`open_artifact` e `pending_notes`, com resultados em texto curto e legível.

#### Scenario: Listar changes em aberto

- **WHEN** o agente chama `list_open_changes` sem argumentos
- **THEN** recebe as changes em aberto do repositório do diretório atual e dos seus worktrees, com caminho e branch

#### Scenario: Ver notas pendentes

- **GIVEN** `design.md` tem 2 notas pendentes
- **WHEN** o agente chama `pending_notes` com o caminho de `design.md`
- **THEN** recebe as 2 notas com id, linhas e comentário

### Requirement: Pane de destino é a do agente que chamou

O `open_artifact` MUST abrir o leitor associado à pane do agente que chamou,
usando o `HERDR_PANE_ID` herdado pelo servidor MCP.

#### Scenario: Handoff volta para o mesmo agente

- **GIVEN** o agente da pane `w2:p1` abriu o leitor por `open_artifact`
- **WHEN** o usuário salva notas, fecha e confirma o envio
- **THEN** a mensagem vai para o agente da pane `w2:p1`

### Requirement: Erros claros fora do Herdr

O `open_artifact` MUST falhar com uma mensagem clara quando o servidor não está
dentro do Herdr ou quando o caminho não é um artefato de uma change OpenSpec em
aberto.

#### Scenario: Agente fora do Herdr

- **GIVEN** o servidor MCP não tem `HERDR_PANE_ID` no ambiente
- **WHEN** o agente chama `open_artifact`
- **THEN** a tool retorna um erro dizendo que o agente precisa rodar dentro de uma pane do Herdr

#### Scenario: Caminho inválido

- **WHEN** o agente chama `open_artifact` com um arquivo fora de `openspec/changes/<change>/`
- **THEN** a tool retorna um erro dizendo que o arquivo não é um artefato de change em aberto

### Requirement: Agente só abre quando o usuário pede

As instruções da tool `open_artifact` MUST dizer ao agente para abrir o leitor
apenas quando o usuário pedir.

#### Scenario: Agente termina uma proposal

- **GIVEN** o agente terminou de escrever uma proposal
- **WHEN** o usuário não pediu para abrir no plugin
- **THEN** o agente não chama `open_artifact`
