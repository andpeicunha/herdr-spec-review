# Delta de ai-notes-annotations

## ADDED Requirements

### Requirement: Formato compatível com ai-notes-md

O plugin MUST gravar notas exatamente no formato da extensão `ai-notes-md`
(VS Code): separador `---`, seção `# AI Notes`, bloco
`## Instructions for AI Agents` com o mesmo texto, e uma seção `## NOTE-XXX`
por nota com os campos `Status`, `Lines`, `Selected Text`, `Human Comment`,
`Expected AI Action` e `Created At`, em inglês.

#### Scenario: Primeira nota em um arquivo

- **GIVEN** `design.md` não tem seção `# AI Notes`
- **WHEN** o usuário salva um comentário com `Ctrl+S`
- **THEN** o final do arquivo recebe `---`, `# AI Notes`, as instruções para agentes e `## NOTE-001` com `Status: pending`

#### Scenario: Nota criada no VS Code

- **GIVEN** a extensão `ai-notes-md` criou `NOTE-003` em `proposal.md`
- **WHEN** o usuário abre `proposal.md` no leitor
- **THEN** a nota aparece abaixo do bloco correspondente
- **AND** a próxima nota criada no plugin recebe o id `NOTE-004`

### Requirement: Gravar a cada Ctrl+S

O plugin MUST gravar a nota no arquivo no momento do `Ctrl+S`, sem esperar o
leitor fechar, preservando todo o conteúdo do arquivo fora da seção
`# AI Notes`.

#### Scenario: Pane fecha inesperadamente

- **GIVEN** o usuário salvou 2 notas com `Ctrl+S`
- **WHEN** a pane do plugin fecha antes do fluxo de fechamento normal
- **THEN** as 2 notas continuam no arquivo

### Requirement: Editar e apagar notas pendentes no leitor

O leitor MUST permitir editar uma nota pendente salva: `c` sempre cria uma nota
nova e `Shift+C` abre a nota do bloco atual com o texto preenchido. Salvar com
`Ctrl+S` MUST trocar só o campo `Human Comment` da mesma nota, preservando
`Status`, `Lines`, `Selected Text` e `Created At`. Salvar uma nota em edição com
o texto vazio MUST apagar a nota, sem diálogo de confirmação. A caixa de nota
MUST aceitar `Ctrl+U` para limpar a linha atual.

#### Scenario: Editar uma nota salva

- **GIVEN** o bloco atual tem `NOTE-001` pendente com o comentário "Qual token?"
- **WHEN** o usuário pressiona `Shift+C`, troca o texto por "Qual token e qual escopo?" e salva com `Ctrl+S`
- **THEN** o arquivo mantém `NOTE-001` com o novo `Human Comment`
- **AND** os demais campos da nota ficam iguais
- **AND** a nota continua legível pela extensão `ai-notes-md`

#### Scenario: Bloco com várias notas

- **GIVEN** o bloco atual tem `NOTE-001` e `NOTE-002`
- **WHEN** o usuário pressiona `Shift+C`
- **THEN** o leitor mostra uma lista numerada com as duas notas
- **AND** o número escolhido abre essa nota para edição

#### Scenario: Apagar uma nota

- **GIVEN** o usuário abriu `NOTE-001` com `Shift+C`
- **WHEN** ele apaga todo o texto (por exemplo com `Ctrl+U`) e salva com `Ctrl+S`
- **THEN** `NOTE-001` é removida do arquivo
- **AND** se não restar nota pendente, a seção `# AI Notes` inteira é removida

#### Scenario: Nota que sumiu do arquivo

- **GIVEN** o agente já resolveu e apagou `NOTE-001` enquanto o leitor estava aberto
- **WHEN** o usuário salva a edição de `NOTE-001`
- **THEN** o leitor avisa que a nota não está mais no arquivo
- **AND** nada é gravado

#### Scenario: Bloco sem nota

- **GIVEN** o bloco atual não tem nota salva
- **WHEN** o usuário pressiona `Shift+C`
- **THEN** a linha de status avisa que não há nota neste bloco e sugere `c`

### Requirement: Âncora da nota

Cada nota MUST registrar as linhas reais do arquivo (`Lines: início-fim`) e o
texto selecionado. Ao reabrir, o plugin MUST encontrar o bloco pelo texto
selecionado quando as linhas tiverem mudado.

#### Scenario: Linhas deslocadas por uma edição

- **GIVEN** `NOTE-001` aponta para as linhas 40-42
- **AND** o agente inseriu 5 linhas antes desse trecho
- **WHEN** o usuário reabre o artefato
- **THEN** a nota aparece abaixo do bloco que agora está nas linhas 45-47

### Requirement: Artefato final sempre limpo

As notas MUST ser temporárias. Toda decisão MUST ser refletida na estrutura
padrão do SDD (requirements, scenarios, design, tasks). Uma nota resolvida
MUST ser removida, e quando não restar nenhuma nota pendente a seção
`# AI Notes` inteira MUST ser removida, incluindo o `---` acima dela.

#### Scenario: Última nota resolvida

- **GIVEN** `design.md` tem só `NOTE-001` pendente
- **WHEN** o agente aplica a nota no design e a resolve
- **THEN** `design.md` não contém mais `# AI Notes` nem o `---` adicionado pelo plugin

#### Scenario: Arquivar com notas pendentes

- **GIVEN** um artefato da change ainda tem notas pendentes
- **WHEN** o usuário tenta arquivar a change
- **THEN** o plugin ou o fluxo de arquivamento avisa que há notas pendentes
