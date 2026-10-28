## Why

Leio muitos SDDs (changes OpenSpec) e hoje o caminho até o artefato certo é lento: achar a change em aberto (às vezes em um worktree), abrir o arquivo no editor, anotar dúvidas e depois explicar ao agente o que mudar. No VS Code isso foi resolvido em parte com a extensão `ai-notes-md`, mas o meu fluxo de trabalho com agentes acontece no Herdr, e lá não existe nada parecido.

Já temos no plugin `herdr-output-comment-composer` uma UI de terminal madura (blocos selecionáveis, tabelas, código linha a linha, caixa de comentário, envio ao agente). O momento é bom para reaproveitar essa base em um plugin focado em revisar SDDs.

## What Changes

Novo plugin Herdr, `herdr-spec-review`, com este fluxo:

1. **Duas entradas**:
   - **Pelo agente**: durante a conversa, o usuário pede para abrir a proposal ou qualquer artefato em que estão trabalhando, e o agente abre o leitor direto nele, por uma tool MCP.
   - **Pelo atalho do Herdr**: o usuário abre o plugin e escolhe o que quer analisar.
2. **Descoberta e escolha (entrada pelo atalho)**: o usuário escolhe o repositório, depois a change e depois o artefato (`proposal.md`, `design.md`, `tasks.md` ou um `specs/**/spec.md`). O plugin encontra as changes OpenSpec em aberto (`openspec/changes/*`, ignorando `archive/`) no repositório escolhido e em todos os seus git worktrees. O repositório da pane atual já vem selecionado.
3. **Leitura e comentários**: o artefato abre em uma pane no estilo do comment composer, onde o usuário navega por blocos e comenta com `c`.
4. **AI Notes no próprio Markdown**: cada `Ctrl+S` grava a nota no arquivo, no mesmo formato da extensão `ai-notes-md` (seção `# AI Notes`, instruções para agentes, `## NOTE-XXX` com `Status: pending`). As notas sobrevivem a fechar e reabrir a leitura.
5. **Handoff ao agente**: ao fechar, se houver notas novas, o plugin pede confirmação e envia uma mensagem curta para o agente da sessão atual, apontando o arquivo com notas pendentes. O usuário pode responder não para terminar a análise depois: nada é enviado e as notas ficam no arquivo como pendentes. Na próxima leitura elas reaparecem, e o próximo envio cobre todas as notas pendentes do arquivo.
6. **Ciclo das notas**: o agente aplica cada nota na estrutura padrão do SDD (requirements, scenarios, design, tasks) e remove a nota resolvida. Quando não restam notas pendentes, a seção `# AI Notes` inteira some. **O artefato final fica sempre limpo.**

## Capabilities

### New Capabilities

- `sdd-discovery`: encontrar changes OpenSpec em aberto no repositório e nos seus worktrees.
- `artifact-picker`: escolher a change e o artefato a ler, com status de cada um.
- `artifact-reader`: ler o artefato em blocos e criar comentários, reaproveitando a UI do comment composer.
- `ai-notes-annotations`: gravar e ler notas no formato `ai-notes-md` dentro do próprio Markdown, incluindo o ciclo até a limpeza total.
- `agent-handoff`: avisar o agente da sessão atual sobre notas pendentes, com confirmação.
- `agent-launch`: servidor MCP para o agente abrir um artefato direto no leitor (por exemplo, a proposal que acabou de criar), além da entrada manual pelo atalho do Herdr.

### Modified Capabilities

Nenhuma (projeto novo).

## Impact

- **Novo repositório** `herdr-spec-review` (plugin Herdr em Python + `curses`, sem dependências externas além de `git`, `jq` e do próprio Herdr).
- **Reuso** do pacote `occ/` do `herdr-output-comment-composer` (renderização Markdown, layout, `TextBuffer`, UI). Começa como cópia; uma biblioteca compartilhada fica para depois.
- **Contrato compartilhado** com a extensão `ai-notes-md` (VS Code): o formato das notas passa a ser um contrato entre as duas ferramentas. Notas criadas em uma aparecem na outra.
- **Artefatos OpenSpec** passam a receber, temporariamente, uma seção `# AI Notes`. Precisa ser compatível com `openspec validate` e `openspec archive` (ver design).
- **Herdr**: usa `herdr agent prompt` para o handoff e as convenções de plugin (`HERDR_PLUGIN_CONFIG_DIR`, `HERDR_PLUGIN_STATE_DIR`, tópico `herdr-plugin`).
