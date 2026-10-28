## 1. Spikes e decisões em aberto

- [x] 1.1 Testar `openspec validate --strict` e `openspec archive` com uma seção `# AI Notes` em `spec.md` (resultado em design D4: passa no validate, vaza no archive)
- [ ] 1.2 Medir o tempo de descoberta em um repositório real com vários worktrees
- [ ] 1.3 Decidir onde fica o guard de archive (Open Questions do design)
- [ ] 1.4 Decidir o formato de `Expected AI Action` (tipos fixos ou texto livre)

## 2. Contrato de AI Notes

- [ ] 2.1 Documentar o formato `ai-notes-md` v0.0.17 em `docs/ai-notes-format.md`
- [ ] 2.2 Implementar parser e escritor de notas (append atômico, próximo id, remoção da seção quando vazia)
- [ ] 2.3 Testes de ida e volta com arquivos gerados pela extensão do VS Code
- [ ] 2.4 Abrir item para corrigir o README do `ai-notes-md` (ainda descreve histórico `✅`)

## 3. Base do plugin

- [ ] 3.1 Criar `herdr-plugin.toml`, launcher (`herdr/pane.sh`) e `bin/` seguindo as convenções do Herdr
- [ ] 3.2 Copiar de `occ/` os módulos `markdown`, `layout`, `editor`, `settings` e as partes reutilizáveis de `ui`
- [ ] 3.3 Configurar testes (`python3 -m unittest discover -s tests`) e o harness de render em terminal virtual

## 4. Descoberta e picker

- [ ] 4.1 Descoberta: repositório a partir do cwd da pane, `git worktree list --porcelain`, `openspec/changes/*` sem `archive/`
- [ ] 4.2 Tela de changes: lista com worktree/branch, notas pendentes e filtro por texto
- [ ] 4.3 Tela de artefatos: ordem do fluxo SDD e notas pendentes por arquivo
- [ ] 4.4 Lembrar a última change e o último artefato por repositório no state dir
- [ ] 4.5 Lista de outros repositórios: panes do Herdr + `SPEC_REVIEW_ROOTS`

## 5. Leitor e notas

- [ ] 5.1 Abrir o artefato no leitor, escondendo a seção `# AI Notes`
- [ ] 5.2 Mostrar notas pendentes abaixo do bloco, com reposicionamento por `Selected Text`
- [ ] 5.3 `c` + `Ctrl+S` grava a nota no arquivo com as linhas reais
- [ ] 5.4 Navegação por requirement/scenario e por seção `##`
- [ ] 5.5 Detectar mudança do arquivo no disco e oferecer recarregar
- [x] 5.7 Editar (`Shift+C`) e apagar notas pendentes no leitor, e `Ctrl+U` na caixa de nota
- [x] 5.6 Zoom simulado (`+`/`-`/`0`, níveis -2 a +3, tabelas na largura toda, nível salvo)

## 6. Handoff e limpeza

- [ ] 6.1 Diálogo de confirmação ao fechar, só quando houve `Ctrl+S`
- [ ] 6.2 Mensagem curta via `herdr agent prompt`, com fallback para copiar o texto
- [ ] 6.3 Checagem "pronto para arquivar" que lista notas e seções `# AI Notes` restantes

## 7. MCP e entrada do agente

- [ ] 7.1 Servidor MCP stdio (initialize, tools/list, tools/call) sem dependências
- [ ] 7.2 Tools `list_open_changes`, `list_artifacts`, `open_artifact`, `pending_notes`
- [ ] 7.3 `open_artifact` abre o leitor na pane do agente e valida o caminho
- [ ] 7.4 Registrar no Claude Code e testar o fluxo real (abrir, comentar, handoff de volta)
- [ ] 7.5 Registrar no Codex depois do primeiro teste

## 8. Publicação

- [ ] 8.1 README com fluxo, teclas, settings, MCP e prints
- [ ] 8.2 Repositório no GitHub com tópico `herdr-plugin` e release `v0.1.0`
- [ ] 8.3 Trocar o plugin linkado localmente pela instalação do GitHub
