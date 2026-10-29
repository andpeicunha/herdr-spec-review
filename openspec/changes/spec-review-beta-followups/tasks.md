## 1. Decisões e medições

- [ ] 1.1 Medir o tempo de descoberta em um repositório real com vários worktrees
- [ ] 1.2 Decidir o formato de `Expected AI Action` (tipos fixos ou texto livre)

## 2. Contrato e documentação

- [ ] 2.1 Documentar o formato `ai-notes-md` v0.0.17 em `docs/ai-notes-format.md`
- [ ] 2.2 Acrescentar prints do fluxo ao README

## 3. Arquivamento seguro

- [ ] 3.1 Decidir onde fica o guard de archive (comando `check`, hook do OpenSpec ou só o prompt do agente)
- [ ] 3.2 Implementar a checagem "pronto para arquivar" (`python3 -m specreview.cli check <change>`) e expor o resultado ao MCP
- [ ] 3.3 Lembrar a checagem na mensagem de handoff ao agente

## 4. Instalação e manutenção

- [ ] 4.1 Trocar o plugin linkado localmente pela instalação do GitHub
- [ ] 4.2 Achar um jeito de o servidor MCP acompanhar a versão instalada (o Herdr instala cada update em uma pasta nova)

## 5. Ajuda de atalhos

- [x] 5.1 Tecla `?` com janela de atalhos no leitor e nas listas, rodapé enxuto com `? help`
- [x] 5.2 Paginar com `Alt+↑`/`Alt+↓` (meia página) em vez de `Shift+↑`/`Shift+↓`

## 6. Código compartilhado

- [ ] 6.1 Extrair o núcleo compartilhado (markdown, layout, editor) entre `herdr-output-comment-composer` e este plugin: hoje as correções são aplicadas nos dois
- [ ] 6.2 Portar o zoom e a edição de notas para o comment composer, se fizerem falta lá
