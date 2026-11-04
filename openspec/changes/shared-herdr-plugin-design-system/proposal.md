## Why / Por quê

Comments and Spec Review run in separate Herdr plugin checkouts and each draws its own curses UI. Their selection colors and row coverage have drifted; even recent border changes had to be copied into both repositories.

Comments e Spec Review rodam em instalações separadas de plugins Herdr e cada um desenha sua própria interface curses. As cores e a área destacada da seleção ficaram diferentes; até a mudança recente da borda precisou ser copiada nos dois repositórios.

## What Changes / O que muda

- Define one small terminal-only design system, with no web components, using semantic colors and reusable drawing rules for pane frames, title bars, cursors, selected rows, and readable fallback modes.
- Definir um sistema visual pequeno e exclusivo do terminal, sem componentes web, com cores semânticas e regras reutilizáveis para bordas, títulos, cursores, linhas selecionadas e modos de cor alternativos.
- Make Spec Review use the same blue, full-row selection behavior as Comments, including wrapped text and code, while keeping each plugin's own content and actions.
- Fazer o Spec Review usar a mesma seleção azul em toda a linha que o Comments, inclusive texto quebrado e código, mantendo o conteúdo e as ações próprios de cada plugin.
- Bundle a pinned version of the shared terminal UI inside each GitHub plugin release. A normal Herdr plugin update MUST install everything needed; no separate online component lookup or download is allowed during installation or pane use.
- Embutir uma versão fixa da interface compartilhada de terminal em cada publicação dos plugins no GitHub. Um update normal do plugin pelo Herdr DEVE instalar tudo que é necessário; não pode haver busca nem download separado de componentes online durante a instalação ou o uso da pane.
- Check Herdr theme support for compatibility, while keeping today's blue selection, cyan border, and title-bar pattern. The shared source MUST make later visual updates easy to apply across the plugins.
- Verificar o suporte a temas do Herdr por compatibilidade, mantendo a seleção azul, a borda ciano e o padrão atual da barra de título. A fonte compartilhada DEVE facilitar a aplicação de futuras mudanças visuais nos plugins.

## Capabilities / Capacidades

### New Capabilities / Novas capacidades

- shared-terminal-ui: one visual contract and reusable terminal UI primitives for Comments, Spec Review, and future compatible Herdr plugins.
- shared-terminal-ui: um contrato visual e componentes reutilizáveis de interface de terminal para Comments, Spec Review e futuros plugins Herdr compatíveis.

### Modified Capabilities / Capacidades modificadas

- artifact-reader: selected blocks in Spec Review gain the shared blue, full-row highlight.
- artifact-reader: blocos selecionados no Spec Review passam a ter o destaque azul compartilhado em toda a linha.

## Impact / Impacto

- Code and tests in herdr-spec-review and herdr-output-comment-composer; a small canonical Python curses UI source and its pinned bundled copies will be added.
- Código e testes em herdr-spec-review e herdr-output-comment-composer; serão adicionadas uma pequena fonte canônica da interface Python curses e suas cópias embutidas com versão fixa.
- Herdr GitHub installations remain independent. Note storage, artifact discovery, agent prompts, and keyboard actions do not change.
- As instalações dos plugins pelo GitHub continuam independentes. O armazenamento de notas, a descoberta de artefatos, os prompts ao agente e os atalhos não mudam.
