## Why

A change `explore-sdd-review-plugin` entregou o MVP do plugin `spec-review` (beta público) e foi arquivada. Restaram pendências que não bloqueiam o uso, mas precisam de dono: o plugin ainda não protege o `openspec archive` contra notas esquecidas, faltam decisões e documentação, e o servidor MCP depende de um caminho fixo.

## What Changes

- **Arquivamento seguro**: uma checagem "pronto para arquivar" que lista as notas pendentes e as seções `# AI Notes` restantes de uma change antes do `openspec archive` (hoje o archive copia a seção para os specs principais sem avisar).
- **Decisões e medições**: onde mora o guard de archive, formato de `Expected AI Action` e o tempo de descoberta em um repositório real com vários worktrees.
- **Documentação**: formato de notas em `docs/ai-notes-format.md` e prints do fluxo no README.
- **Instalação e manutenção**: trocar o plugin linkado pela instalação do GitHub e achar um jeito de o servidor MCP acompanhar a versão instalada (o Herdr instala cada update em uma pasta nova).
- **Código compartilhado**: extrair o núcleo comum (markdown, layout, editor) entre este plugin e o `herdr-output-comment-composer`, e portar para o composer o que fizer falta (zoom, edição de notas).

## Capabilities

### New Capabilities

- `archive-readiness`: checar se uma change pode ser arquivada sem deixar notas ou seções `# AI Notes` para trás.

### Modified Capabilities

Nenhuma.

## Impact

- Novo comando de checagem no plugin (CLI e, se couber, no picker).
- Documentação (`README.md`, `docs/`).
- Sem mudança de comportamento do leitor ou do formato das notas.
