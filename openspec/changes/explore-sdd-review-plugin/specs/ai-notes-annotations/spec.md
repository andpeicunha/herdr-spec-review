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
