## Context

- **Hoje**: para revisar um SDD eu abro o arquivo no editor, anoto com a extensão `ai-notes-md` (VS Code) ou escrevo o feedback direto para o agente. O trabalho com agentes acontece no Herdr, então a revisão força uma troca de ferramenta.
- **Base existente**: o plugin `herdr-output-comment-composer` (v0.4.1) já resolve leitura e comentário no terminal: pacote `occ/` com `markdown.py` (blocos, negrito, tabelas, código linha a linha, regras), `layout.py` (linhas, paginação, scrollbar), `editor.py` (`TextBuffer`), `ui.py` (curses) e `herdr_io.py` (envio ao agente). Segue as convenções de plugin do Herdr (`config.env`, state dir, tópico `herdr-plugin`).
- **Formato de notas existente**: `ai-notes-md` v0.0.17 grava notas no próprio Markdown. O código atual (não o README dele, que está desatualizado) instrui o agente a **apagar** a nota resolvida e a remover a seção `# AI Notes` inteira quando não sobrar nenhuma pendente.
- **Restrições**: Python 3 + `curses`, sem dependências pip (igual ao composer); Herdr ≥ 0.9.5; Linux e macOS.

## Goals / Non-Goals

**Goals:**

- Do Herdr até o artefato certo em poucos toques: changes em aberto do repositório e dos worktrees → change → artefato.
- Ler e comentar com a mesma qualidade do comment composer.
- Notas persistidas no próprio Markdown, compatíveis com `ai-notes-md`, para retomar a leitura depois.
- Handoff curto e confirmado para o agente da sessão atual.
- Artefatos finais sempre limpos: decisões vão para a estrutura do SDD, notas somem.

**Non-Goals:**

- Editar o texto do artefato no plugin (quem edita é o agente ou o editor).
- Suportar formatos de SDD além do OpenSpec no MVP.
- Publicar comentários como review de PR no GitHub (fica para depois).
- Substituir a extensão do VS Code: as duas ferramentas convivem.

## Decisions

### D1. Plugin separado, copiando `occ/` (B), com biblioteca compartilhada depois (C)

- **Escolha**: novo repositório `herdr-spec-review` com uma cópia dos módulos de `occ/` que fazem sentido (markdown, layout, editor, partes da UI, settings).
- **Alternativas**:
  - (A) um "modo arquivo" dentro do comment composer: mais rápido, mas mistura dois produtos em um plugin e em um card do marketplace.
  - (C) extrair já uma biblioteca compartilhada: melhor a longo prazo, mas exige refatorar o composer antes de validar o novo produto.
- **Por quê**: valida o produto rápido sem arriscar o composer. Quando os dois estiverem estáveis, extraímos o núcleo comum (C).

### D2. Descoberta por `git worktree list` a partir do cwd da pane

- `git -C <cwd> rev-parse --show-toplevel` acha o repositório; `git worktree list --porcelain` lista checkout principal + worktrees (inclusive em `.worktrees/`).
- Em cada um, lê `openspec/changes/*/`, ignorando `archive/`. Nada de `openspec list --json` no MVP: ler o filesystem é mais rápido, não depende da versão da CLI e funciona em worktrees sem configuração.
- A mesma change pode aparecer em mais de um worktree; cada entrada mostra caminho e branch.
- **Alternativa**: `openspec list --json` em cada worktree. Fica como fallback se a estrutura de pastas mudar.

### D3. Notas no próprio artefato, contrato compartilhado com `ai-notes-md`

- O plugin grava exatamente os mesmos textos da extensão: `---`, `# AI Notes`, o bloco `## Instructions for AI Agents` (texto da v0.0.17, que manda apagar notas resolvidas e limpar a seção) e `## NOTE-XXX` com `Status`, `Lines`, `Selected Text`, `Human Comment`, `Expected AI Action`, `Created At`.
- Ids continuam a sequência existente no arquivo (`NOTE-004` depois de `NOTE-003`), venham as notas do VS Code ou do Herdr.
- Gravação a cada `Ctrl+S`, de forma atômica (escreve em arquivo temporário no mesmo diretório e renomeia), mexendo só na seção `# AI Notes`.
- **Âncora**: `Lines` vem das linhas reais do arquivo para o bloco selecionado. Ao reabrir, se as linhas não batem mais com `Selected Text`, o plugin procura o texto no arquivo e reposiciona a nota.
- **Próximo passo do contrato**: documentar o formato em um `docs/ai-notes-format.md` (aqui ou em um repo próprio) e corrigir o README do `ai-notes-md`, que ainda descreve o histórico `✅`.
- **Alternativas**: `review.md` ou `notes.md` por change (sidecar). Evita tocar nos artefatos, mas perde a compatibilidade com o VS Code e quebra a regra "o Markdown é a fonte da verdade" do `ai-notes-md`.

### D4. Resultado do spike: notas no spec passam no `validate`, mas vazam no `archive`

Teste feito em uma cópia deste repositório (2026-10-27), com uma nota no formato exato acrescentada ao final de `specs/sdd-discovery/spec.md`, `proposal.md` e `design.md`:

| Verificação | Resultado |
| --- | --- |
| `openspec validate --strict` | **passa**, sem aviso |
| Requirements do spec | continuam corretos (3 ADDED) |
| Último scenario do spec | absorve o `---` no texto dele |
| `openspec archive` | **vaza** `---` e `# AI Notes` para `openspec/specs/sdd-discovery/spec.md`, sem aviso |

**Conclusão**: notas dentro dos artefatos funcionam durante a revisão, mas precisam ser removidas antes de arquivar. O OpenSpec não detecta o problema.

**Decisões derivadas**:

- A regra "artefato final sempre limpo" (spec `ai-notes-annotations`) vira uma proteção concreta: o picker marca changes com notas pendentes, e o plugin oferece uma checagem "pronto para arquivar" que lista notas e seções `# AI Notes` restantes.
- A mensagem de handoff sempre lembra o agente de limpar a seção quando não houver mais notas pendentes.
- Avaliar um guard no fluxo de archive (por exemplo, um hook `pre-archive` ou um comando `herdr-spec-review check <change>` usado antes de `openspec archive`).

### D5. Handoff confirmado e curto

- Ao fechar o leitor, se houve `Ctrl+S` nesta sessão, um diálogo mostra "Enviar N notas (design.md, specs/auth/spec.md) ao agente? y/n".
- A mensagem enviada por `herdr agent prompt` contém só os caminhos e a instrução de processar as AI Notes pendentes, aplicando as decisões na estrutura do SDD e limpando a seção no final. O conteúdo das notas não é repetido: o agente lê o arquivo.
- Em caso de falha, o texto aparece para o usuário copiar.

### D6. Fluxo de telas

```
[changes]  ──Enter──▶  [artefatos]  ──Enter──▶  [leitor]  ──q──▶  [confirmar envio?]
    ▲  Esc                  ▲  Esc                                      │
    └───────────────────────┴────────── volta ao picker ────────────────┘
```

O picker lembra a última change e o último artefato por repositório (state dir do plugin).

### D7. MCP como entrada padrão do agente

- **Escolha**: servidor MCP via stdio em Python puro (só o JSON-RPC necessário: `initialize`, `tools/list`, `tools/call`), registrado uma vez em cada agente (`claude mcp add --scope user`, `~/.codex/config.toml`).
- **Tools**: `list_open_changes`, `list_artifacts`, `open_artifact`, `pending_notes`.
- **Pane certa**: o agente inicia o servidor, então o servidor herda o `HERDR_PANE_ID` do agente. `open_artifact` chama `herdr plugin pane open --target-pane $HERDR_PANE_ID --env SPEC_REVIEW_ARTIFACT=<path>`, e o handoff volta para esse mesmo agente.
- **CLI interna**: o servidor e o launcher usam o mesmo módulo Python. Um comando `bin/spec-review` fica disponível para testes e para agentes sem MCP.
- **Alternativas**:
  - CLI + skill (o agente roda um comando no shell): sem servidor, mas depende de o agente ter shell e de uma skill instalada por agente.
  - Code Mode (estilo Cloudflare: a API vira uma interface TypeScript, o modelo escreve código executado em sandbox): vale para APIs grandes ou chamadas encadeadas. Com 4 tools pequenas, o custo de um sandbox não compensa. Fica como nota se a API crescer.
- **Por quê MCP**: decisão do usuário. Funciona com qualquer cliente MCP, as tools ficam descobríveis e tipadas, e não depende de skill.

### D8. De onde vêm os repositórios

- Padrão: o repositório do cwd da pane de origem.
- Lista "outros repositórios": cwd de todas as panes abertas no Herdr (`herdr pane list`) mais os diretórios com `openspec/` encontrados em `SPEC_REVIEW_ROOTS` (lista separada por `:`, um nível de profundidade), sem duplicados.
- `SPEC_REVIEW_ROOTS` vem de `config.env` no config dir do plugin, como no comment composer. Sem valor padrão.

## Risks / Trade-offs

- [Notas vazam para os specs principais no `archive`] → regra de artefato limpo, marcação de pendências no picker, checagem "pronto para arquivar" e lembrete no handoff (D4).
- [Edição simultânea: o agente reescreve o arquivo enquanto o leitor grava uma nota] → gravação atômica que relê o arquivo antes de anexar; o leitor detecta mudança no disco e oferece recarregar.
- [Contrato com `ai-notes-md` muda em uma das ferramentas] → documentar o formato e cobrir com testes de ida e volta (nota criada por uma ferramenta lida pela outra).
- [Âncoras perdidas depois de reescritas grandes] → buscar por `Selected Text`; se não achar, mostrar a nota em uma lista "notas sem âncora" no topo do leitor.
- [Cópia de `occ/` diverge do composer] → aceito no MVP; extrair biblioteca compartilhada quando os dois estiverem estáveis (D1).
- [Muitos worktrees deixam a descoberta lenta] → só leitura de diretórios, sem chamar a CLI do OpenSpec; medir no spike.

## Open Questions

- O guard de archive fica no plugin (comando `check`), em um hook do OpenSpec ou só no prompt do agente?
- `Expected AI Action`: usar tipos fixos (pergunta, mudança, bloqueio) mapeados para esse campo, ou manter texto livre como no VS Code?
- O leitor deve permitir marcar uma nota como resolvida manualmente (apagar a nota) quando o usuário mesmo decide?
- Vale um modo "diff desde a última leitura" para releituras depois que o agente gera uma nova versão?
- Onde fica a documentação do contrato de AI Notes: neste repo, no `ai-notes-md` ou em um repo próprio?
- Atalho padrão no Herdr: `prefix+r` (review) colide com algo do seu setup?
- Se a API do plugin crescer (workspaces, worktrees, notas, histórico), vale testar uma interface no estilo Code Mode (`search` + `execute` sobre uma API tipada)?
