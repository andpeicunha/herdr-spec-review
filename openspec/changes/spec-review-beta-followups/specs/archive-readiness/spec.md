# Delta de archive-readiness

## ADDED Requirements

### Requirement: Checar se a change está pronta para arquivar

O plugin MUST oferecer uma checagem que, dada uma change OpenSpec, lista as
notas pendentes e as seções `# AI Notes` restantes de cada artefato, e MUST
indicar no resultado (código de saída diferente de zero) quando há sobras.

#### Scenario: Change com notas pendentes

- **GIVEN** `design.md` tem 2 notas `Status: pending` e `tasks.md` tem uma seção `# AI Notes` sem notas
- **WHEN** o usuário roda a checagem dessa change
- **THEN** o resultado lista as 2 notas de `design.md` e a seção restante de `tasks.md`
- **AND** o código de saída indica que a change não está pronta para arquivar

#### Scenario: Change limpa

- **GIVEN** nenhum artefato da change tem notas pendentes nem seção `# AI Notes`
- **WHEN** o usuário roda a checagem
- **THEN** o resultado diz que a change está pronta para arquivar
- **AND** o código de saída indica sucesso

### Requirement: Lembrar a checagem no handoff

A mensagem enviada ao agente MUST lembrar de rodar a checagem antes de
arquivar uma change.

#### Scenario: Handoff com notas

- **GIVEN** o usuário confirmou o envio de notas de uma change
- **WHEN** o plugin monta a mensagem para o agente
- **THEN** a mensagem pede para rodar a checagem de arquivamento antes de `openspec archive`
