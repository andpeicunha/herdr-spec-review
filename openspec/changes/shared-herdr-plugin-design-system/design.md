## Context / Contexto

Herdr owns pane placement and starts each plugin command. Comments and Spec Review are separate Python curses programs in separate GitHub installations. They currently define color pairs and draw frames and selected rows in their own UI modules. The frame styles were synchronized manually, but Spec Review still uses an older selection pair and colors only the text.

O Herdr controla a posição da pane e inicia o comando de cada plugin. Comments e Spec Review são programas Python curses separados, em instalações GitHub separadas. Hoje cada módulo de interface define seus pares de cores e desenha bordas e linhas selecionadas. As bordas foram sincronizadas manualmente, mas o Spec Review ainda usa uma seleção antiga e colore apenas o texto.

The beta follow-up change already tracks sharing Markdown, layout, and editor code. This change owns only visual tokens and terminal drawing primitives, so the two efforts can proceed independently.

A change de pendências do beta já acompanha o compartilhamento de código de Markdown, layout e editor. Esta change trata apenas de tokens visuais e componentes de desenho no terminal, para que os dois trabalhos possam avançar separadamente.

## Goals / Non-Goals · Objetivos / Fora do escopo

**Goals / Objetivos:**

- One semantic visual contract for both plugins and future Python curses plugins. / Um contrato visual semântico para os dois plugins e futuros plugins Python curses.
- The same blue, full-row selection and visible pane frame across supported color modes. / A mesma seleção azul em toda a linha e a mesma borda visível nos modos de cor suportados.
- Independent GitHub installs that bundle a pinned shared-UI version, with no separate online component fetch during plugin update or runtime. / Instalações GitHub independentes que embutem uma versão fixa da interface compartilhada, sem busca separada de componentes online durante o update ou a execução.
- Repeatable visual checks that catch drift. / Verificações visuais repetíveis que detectem diferenças.

**Non-Goals / Fora do escopo:**

- Sharing artifact discovery, AI Notes, prompts, keyboard behavior, Markdown parsing, layout, or the editor. / Compartilhar descoberta de artefatos, AI Notes, prompts, atalhos, análise de Markdown, layout ou editor.
- Changing Herdr's pane manager or requiring all third-party plugins to adopt this UI. / Alterar o gerenciador de panes do Herdr ou exigir que todos os plugins de terceiros adotem esta interface.

## Decisions / Decisões

### D1. Keep the approved palette behind semantic roles / Manter a paleta aprovada em papéis semânticos

Expose roles such as pane_border, pane_title, selected, active_cursor, muted, comment, and error. The first version MUST preserve the approved blue selected row and title, cyan border, and readable basic-color and monochrome fallbacks. Inspect Herdr's theme API only to find a compatible integration point; a Herdr theme MUST NOT silently change this approved plugin palette. Later visual changes are made once in the canonical source, then adopted through an explicit bundled-version update in each plugin.

Expor papéis como pane_border, pane_title, selected, active_cursor, muted, comment e error. A primeira versão DEVE preservar a linha selecionada e o título azuis, a borda ciano e alternativas legíveis com cores básicas ou sem cores. Verificar a API de temas do Herdr apenas para encontrar uma integração compatível; um tema do Herdr NÃO DEVE mudar silenciosamente a paleta aprovada dos plugins. Mudanças visuais futuras são feitas uma vez na fonte canônica e adotadas por uma atualização explícita da versão embutida em cada plugin.

Alternative: keep numeric curses colors in each plugin. This caused the current drift.
Alternativa: manter números de cores curses em cada plugin. Isso causou a diferença atual.

### D2. Share drawing primitives, not whole applications / Compartilhar componentes de desenho, não os aplicativos inteiros

The shared interface provides small functions for the frame, title bar, and full-width selected display row. A plugin supplies its label, content width, selected rows, and text; it retains its own navigation and data model. The selected-row function paints the gutter and remaining cells before the plugin draws text, and preserves a distinct active cursor in a range.

A interface compartilhada oferece funções pequenas para borda, barra de título e linha visual selecionada em toda a largura. O plugin informa seu nome, largura do conteúdo, linhas selecionadas e texto; a navegação e o modelo de dados continuam no plugin. A função de seleção colore primeiro a margem e as células restantes, e depois o plugin desenha o texto, preservando um cursor ativo distinto em uma seleção de várias linhas.

Alternative: reuse the complete Comments composer inside Spec Review. That would couple different content and note workflows.
Alternativa: reutilizar o composer completo do Comments no Spec Review. Isso acoplaria fluxos diferentes de conteúdo e notas.

### D3. Bundle a pinned source version in every plugin / Embutir uma versão fixa da fonte em cada plugin

The canonical source is a small, versioned Python curses module. Each plugin repository commits its pinned copy and version identifier before release. Herdr plugin install or update downloads that complete plugin checkout; it MUST NOT fetch the UI module separately or search online for components. The current system-Python launcher imports only files inside its own checkout, so the pane runs offline and without another plugin. A development-time sync step updates the bundled copy from the canonical source, and conformance checks detect drift. Inspect Herdr's build/install behavior to confirm this path, not to defer the offline-bundle decision.

A fonte canônica é um pequeno módulo Python curses versionado. Cada repositório de plugin inclui no commit sua cópia com versão fixa antes da publicação. O install ou update do plugin pelo Herdr baixa esse checkout completo; NÃO DEVE buscar o módulo de interface separadamente nem procurar componentes online. O launcher atual em Python do sistema importa apenas arquivos do próprio checkout, então a pane funciona offline e sem outro plugin. Uma etapa de sincronização durante o desenvolvimento atualiza a cópia a partir da fonte canônica, e as checagens de conformidade detectam diferenças. Verificar o build/install do Herdr confirma esse caminho, sem reabrir a decisão de embutir a interface offline.

Alternative: import code from a sibling checkout or download a shared UI package during install or pane startup. Either adds a dependency outside the complete plugin release and can break offline use.
Alternativa: importar código de outro checkout ou baixar um pacote de interface durante a instalação ou a abertura da pane. Ambos criam uma dependência fora da publicação completa do plugin e podem quebrar o uso offline.

### D4. Verify the rendered result / Verificar o resultado desenhado

Run both plugin test suites and a virtual terminal check at 256 colors and basic colors. Inspect cell foreground/background across selected wrapped and code rows, frame edges, and narrow titles. A shared conformance test checks the role definitions and pinned version in each plugin. Manual inspection in Herdr is the final visual check, not the only evidence.

Executar as suítes dos dois plugins e uma verificação em terminal virtual com 256 cores e cores básicas. Inspecionar cor de texto e fundo das células em linhas selecionadas com quebra e código, bordas e títulos estreitos. Um teste de conformidade compartilhado verifica os papéis e a versão fixa em cada plugin. A inspeção manual no Herdr é a última verificação visual, não a única evidência.

## Risks / Trade-offs · Riscos / Trocas

- Different terminal palettes can shift exact hues. Use semantic color roles, contrast-aware fallbacks, and virtual terminal checks. / Paletas de terminal diferentes podem mudar os tons exatos. Usar papéis semânticos, alternativas com contraste e testes em terminal virtual.
- Bundled source can drift if a plugin skips the development-time sync step. Record the pinned version and source digest; fail conformance when the copy differs. / O código embutido pode divergir se o plugin pular a sincronização durante o desenvolvimento. Registrar a versão fixa e o resumo da fonte; falhar a checagem de conformidade quando a cópia for diferente.
- A shared drawing API can grow too large. Keep only repeated visual primitives in it; leave workflows local. / Uma API compartilhada pode crescer demais. Manter nela apenas componentes visuais repetidos; deixar os fluxos em cada plugin.

## Migration Plan / Plano de migração

1. Check Herdr theme and install behavior for compatibility; publish the approved blue/cyan role contract. / Verificar tema e instalação do Herdr por compatibilidade; publicar o contrato aprovado de papéis azuis/ciano.
2. Add the canonical source, commit its pinned copy inside Comments, and add conformance checks without changing its intended visual behavior. / Adicionar a fonte canônica, incluir sua cópia fixa no commit do Comments e adicionar checagens de conformidade sem mudar seu visual esperado.
3. Commit the pinned copy inside Spec Review and replace its old selection with the shared full-row blue style. / Incluir a cópia fixa no commit do Spec Review e trocar a seleção antiga pelo destaque azul compartilhado em toda a linha.
4. Release each complete plugin checkout, run Herdr plugin update, disconnect the network, and verify both panes. If a release regresses, revert that plugin's pin and bundled copy together. / Publicar o checkout completo de cada plugin, executar o update pelo Herdr, desconectar a rede e verificar as duas panes. Se houver regressão, voltar juntos a versão fixa e o código embutido daquele plugin.

## Open Questions / Questões em aberto

- Does Herdr expose a supported theme API that can be used without changing the approved palette? / O Herdr oferece uma API de tema que possa ser usada sem mudar a paleta aprovada?
- Where should the canonical versioned source live so future personal Herdr plugins can adopt it? / Onde deve ficar a fonte canônica versionada para que futuros plugins Herdr pessoais possam adotá-la?
