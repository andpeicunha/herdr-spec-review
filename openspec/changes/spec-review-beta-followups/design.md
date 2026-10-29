## Context

O MVP do `spec-review` está publicado em beta. O spike da change anterior mostrou que `openspec validate --strict` aceita uma seção `# AI Notes` dentro de um spec, mas `openspec archive` copia a seção (com o `---` acima dela) para o spec principal, sem aviso. As notas são temporárias, então qualquer sobra vira lixo permanente nos specs.

## Goals / Non-Goals

**Goals:**

- Dar ao usuário, e ao agente, uma forma rápida de saber se uma change está limpa antes de arquivar.
- Fechar as pendências do beta sem mudar o leitor nem o formato das notas.

**Non-Goals:**

- Alterar o `openspec archive` em si.
- Suportar formatos de SDD além do OpenSpec.

## Decisions

### D1. Checagem como comando do plugin

- **Escolha**: um comando `python3 -m specreview.cli check <change>` que lista, por artefato, as notas pendentes e qualquer seção `# AI Notes` restante, e sai com código diferente de zero quando há sobras. O servidor MCP expõe o mesmo resultado na tool `pending_notes` (por change) para o agente.
- **Alternativas**: hook `pre-archive` do OpenSpec (depende de suporte da CLI), ou só o lembrete no prompt do agente (não impede o vazamento).
- **Por quê**: funciona hoje, sem depender do OpenSpec, e pode virar hook depois.

### D2. Decisões pendentes ficam como tarefas

Medir o tempo de descoberta, o formato de `Expected AI Action` e o guard de archive ficam nas tarefas, porque dependem de uso real do beta.

## Risks / Trade-offs

- [A checagem só ajuda quem a roda] → lembrar o agente no prompt de handoff e documentar no README; avaliar o hook depois.
- [Servidor MCP em versão diferente do plugin instalado] → documentado como limite do beta; tarefa de manutenção.
