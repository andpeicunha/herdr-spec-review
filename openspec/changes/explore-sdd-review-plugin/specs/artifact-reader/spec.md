# Delta de artifact-reader

## ADDED Requirements

### Requirement: Ler o artefato em blocos

O leitor MUST mostrar o artefato em blocos selecionáveis com a mesma
renderização do comment composer: títulos, negrito, listas, tabelas alinhadas,
citações, regras e cada linha de um bloco de código como bloco próprio.

#### Scenario: Comentar uma linha de um cenário

- **GIVEN** o artefato tem um `#### Scenario:` com linhas **WHEN** e **THEN**
- **WHEN** o usuário navega até a linha **THEN**
- **THEN** apenas essa linha fica selecionada

### Requirement: Esconder a seção AI Notes na leitura

O leitor MUST esconder a seção `# AI Notes` do texto e MUST mostrar cada nota
pendente logo abaixo do bloco a que ela se refere, como no comment composer.

#### Scenario: Reabrir um artefato com notas

- **GIVEN** `design.md` tem a nota `NOTE-002` pendente nas linhas 40-42
- **WHEN** o usuário abre `design.md` no leitor
- **THEN** a nota aparece abaixo do bloco que contém a linha 40
- **AND** a seção `# AI Notes` não aparece como texto no final

### Requirement: Navegar por estrutura

O leitor MUST permitir pular entre requirements e scenarios (em specs) e entre
seções `##` (nos outros artefatos).

#### Scenario: Pular para o próximo requirement

- **GIVEN** o cursor está no primeiro requirement de um spec
- **WHEN** o usuário usa o atalho de próximo requirement
- **THEN** o cursor vai para o próximo `### Requirement:`

### Requirement: Recarregar quando o arquivo muda

O leitor MUST detectar que o arquivo mudou no disco (por exemplo, o agente
gerou uma nova versão) e MUST oferecer recarregar sem perder a posição de
leitura aproximada.

#### Scenario: Agente reescreve o design durante a leitura

- **GIVEN** o leitor está aberto em `design.md`
- **WHEN** o agente salva uma nova versão de `design.md`
- **THEN** o leitor avisa que o arquivo mudou e oferece recarregar
