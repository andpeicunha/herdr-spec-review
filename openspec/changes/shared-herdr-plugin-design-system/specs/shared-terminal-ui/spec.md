## ADDED Requirements

### Requirement: Shared semantic colors / Cores semânticas compartilhadas

The design system MUST define named roles for pane border, pane title, selected row, active cursor, secondary text, comments, and errors. Its first version MUST preserve the current Comments blue selection and title and the approved cyan pane border. Both plugins MUST resolve each shared role through the same versioned rules for 256-color, basic-color, and monochrome terminals; a Herdr theme MUST NOT silently replace the approved palette.

Both plugins MUST start with the curated `herdr-dark` theme when no theme is configured or the configured value is invalid. The `terminal` theme remains an explicit option for users who want the terminal's own colors.

O sistema visual DEVE definir papéis nomeados para borda da pane, título, linha selecionada, cursor ativo, texto secundário, comentários e erros. Sua primeira versão DEVE preservar a seleção e o título azuis atuais do Comments e a borda ciano aprovada. Os dois plugins DEVEM resolver cada papel pelas mesmas regras versionadas em terminais de 256 cores, cores básicas e sem cores; um tema do Herdr NÃO DEVE substituir silenciosamente a paleta aprovada.

#### Scenario: Same theme in both plugins / Mesmo tema nos dois plugins

- **WHEN** Comments and Spec Review use the same design-system version in a 256-color terminal
- **THEN** the title and selected row match the current Comments blue, and the pane border matches the approved cyan
- **QUANDO** Comments e Spec Review usam a mesma versão do sistema visual em um terminal de 256 cores
- **ENTÃO** o título e a linha selecionada usam o azul atual do Comments, e a borda usa o ciano aprovado

#### Scenario: Limited terminal colors / Cores limitadas no terminal

- **WHEN** either plugin runs with only basic colors or no color support
- **THEN** its selected row and pane boundary remain distinguishable using the defined fallback styles
- **QUANDO** um dos plugins roda com apenas cores básicas ou sem suporte a cores
- **ENTÃO** a linha selecionada e o limite da pane continuam distinguíveis pelos estilos alternativos definidos

### Requirement: Shared pane frame / Moldura compartilhada da pane

The design system MUST provide a reusable frame with a visible border, a filled title bar, and a plugin-specific name. The frame MUST remain legible in a narrow pane without writing outside its bounds.

O sistema visual DEVE oferecer uma moldura reutilizável com borda visível, barra de título preenchida e nome próprio do plugin. A moldura DEVE continuar legível em uma pane estreita sem escrever fora dos seus limites.

#### Scenario: Open plugin pane / Abrir a pane do plugin

- **WHEN** either plugin opens its zoomed pane
- **THEN** the border and title bar use the shared style, while the title identifies that plugin
- **QUANDO** um dos plugins abre sua pane ampliada
- **ENTÃO** a borda e a barra de título usam o estilo compartilhado, enquanto o título identifica o plugin

#### Scenario: Narrow pane / Pane estreita

- **WHEN** a pane is too narrow for the full title and open-pane label
- **THEN** optional title text is shortened without hiding the plugin name or breaking the border
- **QUANDO** a pane é estreita demais para o título completo e o aviso de pane aberta
- **ENTÃO** o texto opcional é encurtado sem esconder o nome do plugin nem quebrar a borda

### Requirement: Full-row selection / Seleção em toda a linha

The design system MUST provide a selected-row style that covers the gutter, visible text, and remaining cells of each selected display row. It MUST preserve readable text on wrapped rows and code rows. A separate active-cursor role MUST stay visible within a multi-row selection.

O sistema visual DEVE oferecer um estilo de seleção que cubra a margem, o texto visível e as células restantes de cada linha selecionada. Ele DEVE manter o texto legível em linhas quebradas e linhas de código. Um papel separado para o cursor ativo DEVE continuar visível dentro de uma seleção de várias linhas.

#### Scenario: Wrapped selected block / Bloco selecionado com quebra de linha

- **WHEN** a selected block occupies several display rows
- **THEN** every display row of that block has the shared selection background through the pane's content width
- **QUANDO** um bloco selecionado ocupa várias linhas visuais
- **ENTÃO** todas as linhas visuais do bloco têm o fundo de seleção compartilhado até o fim da área de conteúdo da pane

#### Scenario: Selected code / Código selecionado

- **WHEN** a code line or code-frame line is selected
- **THEN** the selected-row style remains visible and the code text remains readable
- **QUANDO** uma linha de código ou da moldura do bloco de código é selecionada
- **ENTÃO** o estilo de seleção continua visível e o código permanece legível

### Requirement: Independent plugin installation / Instalação independente dos plugins

Each GitHub-installed plugin MUST bundle the complete shared terminal UI at a pinned version inside its own checkout. A normal Herdr plugin install or update MUST install that complete checkout without a separate online component lookup or download. The pane MUST run offline without another plugin's checkout and MUST NOT load web components or browser assets. Version and bundled-source changes MUST be explicit in each plugin repository.

Cada plugin instalado pelo GitHub DEVE embutir toda a interface compartilhada de terminal, com versão fixa, dentro do próprio checkout. Um install ou update normal pelo Herdr DEVE instalar esse checkout completo sem busca nem download separado de componentes online. A pane DEVE funcionar offline, sem o checkout de outro plugin e sem carregar componentes web ou recursos de navegador. Mudanças de versão e do código embutido DEVEM ser explícitas em cada repositório.

#### Scenario: Update and run offline / Atualizar e executar offline

- **WHEN** a user updates one plugin with Herdr and then disconnects the network
- **THEN** its pane starts with the bundled pinned UI and performs no online component lookup
- **QUANDO** uma pessoa atualiza um plugin pelo Herdr e depois desconecta a rede
- **ENTÃO** a pane abre com a interface fixa embutida e não procura componentes online

#### Scenario: Install one plugin alone / Instalar apenas um plugin

- **WHEN** a user installs only Spec Review or only Comments through Herdr
- **THEN** its pane starts and uses the bundled pinned UI with no other plugin installed
- **QUANDO** uma pessoa instala somente Spec Review ou somente Comments pelo Herdr
- **ENTÃO** a pane abre e usa a interface fixa embutida sem exigir o outro plugin

### Requirement: Visual conformance / Conformidade visual

The shared UI MUST have a repeatable check for its approved semantic colors, full-row selection, and bundled source version or digest. Each adopting plugin MUST run that check against its pinned copy so a visual change is applied explicitly rather than drifting between plugins.

A interface compartilhada DEVE ter uma verificação repetível das cores semânticas aprovadas, da seleção em toda a linha e da versão ou resumo do código embutido. Cada plugin que a adotar DEVE executar essa verificação com sua cópia fixa para que mudanças visuais sejam aplicadas explicitamente, sem divergência entre plugins.

#### Scenario: Detect style drift / Detectar diferença de estilo

- **WHEN** a plugin changes a shared color or selected-row renderer independently
- **THEN** its conformance check fails before release
- **QUANDO** um plugin altera sozinho uma cor compartilhada ou o desenho da linha selecionada
- **ENTÃO** sua verificação de conformidade falha antes da publicação
