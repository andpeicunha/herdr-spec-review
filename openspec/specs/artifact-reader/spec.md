# artifact-reader Specification

## Purpose
Ler um artefato em blocos (texto, tabelas, código), com navegação, zoom simulado e recarga quando o arquivo muda.

## Requirements
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

### Requirement: Cada linha de tabela é um bloco

O leitor MUST tratar cada linha de uma tabela como um bloco selecionável e
comentável, e o cabeçalho (com a linha separadora) como um bloco. Uma tabela que
cabe na pane MUST aparecer com colunas alinhadas. Uma tabela que não cabe sem
cortar células MUST aparecer como um registro por linha, com linhas `Nome: valor`
de texto completo e uma linha de cabeçalho `Columns:`. Copiar um intervalo de
linhas MUST gerar Markdown válido.

#### Scenario: Comentar uma linha de tabela

- **GIVEN** o artefato tem uma tabela com três linhas de dados
- **WHEN** o usuário move o cursor para a segunda linha e salva uma nota
- **THEN** a nota registra as linhas reais do arquivo dessa linha e cita só essa linha
- **AND** a nota aparece abaixo dessa linha

#### Scenario: Tabela larga vira registros

- **GIVEN** a soma das larguras naturais das colunas é maior que a largura da pane
- **WHEN** o leitor desenha a tabela
- **THEN** cada linha aparece como um registro com todos os campos por extenso
- **AND** nenhuma célula é cortada com `…`

### Requirement: Zoom simulado pelo layout

O leitor MUST permitir aumentar e reduzir o texto com `+` e `-` (e `0` para
voltar ao normal), afetando só o texto da pane, e MUST lembrar o nível entre
aberturas, com um único nível para todas as panes. Como o terminal não permite
mudar a fonte, o zoom MUST ser simulado pelo layout: aumentar estreita e
centraliza a coluna de leitura, e reduzir usa a largura toda com menos linhas em
branco.

#### Scenario: Aumentar o texto

- **GIVEN** o leitor está no nível normal em uma pane larga
- **WHEN** o usuário pressiona `+`
- **THEN** a coluna de texto fica mais estreita e centralizada
- **AND** o cabeçalho mostra o nível, por exemplo `zoom +1`

#### Scenario: Tabelas com zoom

- **GIVEN** o artefato tem uma tabela e o nível de zoom é `+3`
- **WHEN** o leitor desenha a tabela
- **THEN** a tabela usa a largura toda da pane, sem a margem da coluna
- **AND** se a tabela não couber, cada linha vira um registro com o texto completo, sem células cortadas

#### Scenario: Limites do zoom

- **GIVEN** o nível de zoom está no máximo (`+3`) ou no mínimo (`-2`)
- **WHEN** o usuário pressiona `+` ou `-` de novo
- **THEN** o nível não muda
- **AND** a linha de status avisa que o limite foi atingido

### Requirement: Recarregar quando o arquivo muda

O leitor MUST detectar que o arquivo mudou no disco (por exemplo, o agente
gerou uma nova versão) e MUST oferecer recarregar sem perder a posição de
leitura aproximada.

#### Scenario: Agente reescreve o design durante a leitura

- **GIVEN** o leitor está aberto em `design.md`
- **WHEN** o agente salva uma nova versão de `design.md`
- **THEN** o leitor avisa que o arquivo mudou e oferece recarregar

