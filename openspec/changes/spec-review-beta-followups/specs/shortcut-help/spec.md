# Delta de shortcut-help

## ADDED Requirements

### Requirement: Janela com todos os atalhos

O plugin MUST abrir uma janela com todos os atalhos da tela atual quando o
usuário pressiona `?`, no leitor e nas listas (changes, artefatos e
repositórios). A janela MUST agrupar os atalhos por assunto e MUST fechar com
`?`, `Esc`, `q` ou `Enter`.

#### Scenario: Abrir a ajuda no leitor

- **GIVEN** o leitor está aberto e o usuário não está digitando uma nota
- **WHEN** o usuário pressiona `?`
- **THEN** a janela lista os atalhos de movimento, notas, caixa de nota, visualização e os demais
- **AND** `Esc` fecha a janela e o leitor continua na mesma posição

#### Scenario: Ajuda da lista de artefatos

- **GIVEN** a lista de artefatos está aberta
- **WHEN** o usuário pressiona `?`
- **THEN** a janela lista os atalhos da lista
- **AND** não menciona a tecla de trocar de repositório, que só existe na lista de changes

#### Scenario: Pergunta digitada na nota

- **GIVEN** o usuário está digitando uma nota ou o filtro de uma lista
- **WHEN** ele digita `?`
- **THEN** o caractere entra no texto e a janela não abre

### Requirement: Janela que cabe em qualquer pane

A janela MUST rolar com `↑`/`↓` quando a lista é maior que a pane, mostrando a
faixa visível, e MUST colocar o texto de cada atalho em uma linha própria quando
as teclas não couberem ao lado dele, sem cortar nenhuma tecla.

#### Scenario: Pane baixa

- **GIVEN** a pane tem menos linhas do que a lista de atalhos
- **WHEN** o usuário abre a ajuda e pressiona `↓`
- **THEN** a janela rola e mostra a faixa visível, por exemplo `7-26 of 26`

### Requirement: Rodapé enxuto

O rodapé MUST mostrar só os atalhos essenciais e a dica `? help`, de modo que
caiba em uma pane de 80 colunas.

#### Scenario: Pane de 80 colunas

- **GIVEN** a pane tem 80 colunas
- **WHEN** o leitor desenha o rodapé
- **THEN** o rodapé inteiro aparece, incluindo `? help`

### Requirement: Enviar e fechar em teclas separadas

O leitor MUST enviar as notas pendentes ao agente com `s` (depois de pedir confirmação) e MUST fechar com `q` ou `Esc` sem enviar nada, como no comment composer. As notas pendentes MUST continuar no arquivo ao fechar.

#### Scenario: Enviar com s

- **GIVEN** o leitor tem 2 notas pendentes no arquivo
- **WHEN** o usuário pressiona `s` e confirma
- **THEN** o agente recebe a mensagem curta apontando para o arquivo e o leitor fecha

#### Scenario: Fechar com q

- **GIVEN** o leitor tem notas pendentes
- **WHEN** o usuário pressiona `q`
- **THEN** o leitor fecha sem perguntar e sem enviar, e as notas continuam no arquivo
