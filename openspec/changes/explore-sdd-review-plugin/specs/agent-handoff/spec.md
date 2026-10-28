# Delta de agent-handoff

## ADDED Requirements

### Requirement: Confirmar antes de enviar

O plugin MUST perguntar se deve avisar o agente ao fechar o leitor, quando o
usuário salvou pelo menos uma nota nesta sessão de leitura, mostrando quantas
notas e em quais arquivos.

#### Scenario: Fechar com notas novas

- **GIVEN** o usuário salvou 3 notas em `design.md`
- **WHEN** ele fecha o leitor
- **THEN** o plugin pergunta se deve enviar as 3 notas de `design.md` ao agente

#### Scenario: Fechar sem notas novas

- **GIVEN** o usuário não salvou nenhuma nota nesta leitura
- **WHEN** ele fecha o leitor
- **THEN** o plugin fecha sem perguntar e sem enviar nada

#### Scenario: Usuário recusa o envio

- **GIVEN** a pergunta de envio está aberta
- **WHEN** o usuário responde não
- **THEN** nada é enviado
- **AND** as notas continuam no arquivo com `Status: pending`

#### Scenario: Terminar a análise depois

- **GIVEN** o usuário recusou o envio de 2 notas em `proposal.md`
- **WHEN** ele reabre `proposal.md`, salva mais 1 nota e confirma o envio ao fechar
- **THEN** as 2 notas antigas aparecem abaixo dos seus blocos durante a leitura
- **AND** a mensagem pede ao agente para processar todas as 3 notas pendentes do arquivo

### Requirement: Mensagem curta para o agente da sessão

Quando o usuário confirma, o plugin MUST enviar ao agente da pane de origem uma
mensagem curta pelo Herdr, com o caminho de cada arquivo que tem notas
pendentes, e MUST NOT repetir o conteúdo das notas, porque elas já estão no
arquivo.

#### Scenario: Envio confirmado

- **GIVEN** o usuário confirmou o envio de notas em `openspec/changes/add-login/design.md`
- **WHEN** o plugin envia a mensagem
- **THEN** o agente da pane de origem recebe um prompt pedindo para processar as AI Notes pendentes desse arquivo
- **AND** o prompt lembra que as decisões devem ir para a estrutura do SDD e que a seção `# AI Notes` deve ficar limpa no final

#### Scenario: Falha no envio

- **GIVEN** o agente da pane de origem não está disponível
- **WHEN** o plugin tenta enviar a mensagem
- **THEN** o plugin mostra o erro
- **AND** mostra o texto da mensagem para o usuário copiar
