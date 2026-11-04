## 1. Confirm platform support / Confirmar suporte da plataforma

- [ ] 1.1 Inspect Herdr's theme API and install/update behavior; record only integration options that preserve the approved blue/cyan palette and need no separate online component fetch. / Verificar a API de tema e o install/update do Herdr; registrar apenas integrações que preservem a paleta azul/ciano aprovada e não exijam busca separada de componentes online.
- [ ] 1.2 Choose the canonical source location and define the development-time sync, version pin, and source digest for the copy bundled in each plugin checkout. / Escolher onde fica a fonte canônica e definir a sincronização durante o desenvolvimento, a versão fixa e o resumo da cópia embutida em cada checkout.

## 2. Build the shared visual contract / Criar o contrato visual compartilhado

- [ ] 2.1 Create the canonical, versioned Python curses module with the current blue/cyan roles and readable 256-color, basic-color, and monochrome fallbacks. / Criar o módulo canônico e versionado em Python curses com os papéis azuis/ciano atuais e alternativas legíveis para 256 cores, cores básicas e ausência de cores.
- [ ] 2.2 Add reusable frame, title-bar, and full-row selection drawing functions, including narrow-pane and active-cursor handling. / Adicionar funções reutilizáveis para borda, barra de título e seleção em toda a linha, incluindo pane estreita e cursor ativo.
- [ ] 2.3 Add shared conformance checks for approved role values, frame bounds, wrapped and code rows, and the bundled source version or digest. / Adicionar checagens compartilhadas dos papéis aprovados, limites da borda, linhas quebradas e de código, e versão ou resumo da fonte embutida.

## 3. Adopt in Comments / Adotar no Comments

- [ ] 3.1 Commit the pinned shared UI copy inside herdr-output-comment-composer and replace its duplicated palette and frame/selection drawing. / Incluir no commit a cópia fixa da interface em herdr-output-comment-composer e substituir sua paleta e desenho duplicados de borda e seleção.
- [ ] 3.2 Run its existing tests and conformance checks; confirm the blue selection, bright border, and title bar in a virtual terminal. / Executar os testes existentes e as checagens de conformidade; confirmar seleção azul, borda destacada e barra de título em terminal virtual.

## 4. Adopt in Spec Review / Adotar no Spec Review

- [ ] 4.1 Commit the pinned shared UI copy inside herdr-spec-review and replace its duplicated palette and frame drawing. / Incluir no commit a cópia fixa da interface em herdr-spec-review e substituir sua paleta e desenho duplicados da borda.
- [ ] 4.2 Use the shared blue full-row selection in the picker and artifact reader, including wrapped text, code, and tables. / Usar a seleção azul compartilhada em toda a linha nas listas e no leitor, inclusive texto quebrado, código e tabelas.
- [ ] 4.3 Run its existing tests and conformance checks; inspect a virtual terminal at 256 and basic colors and a narrow pane. / Executar os testes existentes e as checagens de conformidade; inspecionar um terminal virtual com 256 cores, cores básicas e pane estreita.

## 5. Release and verify / Publicar e verificar

- [ ] 5.1 Document the shared version, update procedure, and visual roles for future plugins in English and Brazilian Portuguese. / Documentar a versão compartilhada, a atualização e os papéis visuais para futuros plugins em inglês e português do Brasil.
- [ ] 5.2 Release both complete plugin checkouts, run Herdr plugin update for each, disconnect the network, and confirm both panes use the same selected-row and frame styles without fetching components. / Publicar os checkouts completos, executar o update de cada plugin pelo Herdr, desconectar a rede e confirmar as mesmas seleções e bordas sem buscar componentes.
