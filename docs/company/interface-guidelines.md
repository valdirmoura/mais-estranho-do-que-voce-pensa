# Interface Guidelines

Status: padrão corporativo inicial para interfaces digitais da Anmaru.

Este guia orienta telas, componentes, tokens e padrões visuais. Ele complementa `brand-guidelines.md`: a marca define identidade; este documento define como essa identidade vira produto.

## Princípios de interface

- Mobile-first: a primeira experiência precisa funcionar bem em telas pequenas.
- Clareza antes de densidade: mostre o que o usuário precisa decidir agora.
- Ação primária única: cada tela deve ter uma ação principal evidente.
- Consistência por tokens: componentes não devem depender de hex solto.
- Linguagem consistente: use os termos canônicos do produto antes de criar novos nomes.
- Estados visíveis: carregando, vazio, erro, sucesso, bloqueio e sem permissão precisam ter mensagem clara.
- Acessibilidade obrigatória: contraste adequado, foco visível, labels corretos e controles com tamanho tocável.
- Ajuste por projeto: cada produto pode ter cores próprias, mas deve preservar tipografia, espaçamento, hierarquia e estados.

## Arquitetura de tokens

Use três camadas:

1. **Tokens globais**: paleta bruta, fontes, escala, raio, sombra e espaçamento.
2. **Tokens semânticos**: usos como texto, fundo, borda, foco, ação e feedback.
3. **Tokens de componente**: botão, campo, card, badge, tabela, modal e navegação.

Não codifique cores diretamente em componentes. Quando um projeto precisar de cor própria, ajuste os tokens semânticos ou de componente.

## Tokens recomendados

### Cores semânticas

```css
:root {
  --color-brand-primary: #222831;
  --color-brand-secondary: #393E46;
  --color-brand-action: #FFD369;
  --color-brand-action-hover: #FFD369;
  --color-brand-light: #EEEEEE;

  --color-bg-page: #EEEEEE;
  --color-bg-surface: #EEEEEE;
  --color-bg-subtle: #EEEEEE;
  --color-bg-info-subtle: #EEEEEE;
  --color-bg-action-subtle: rgba(255, 211, 105, 0.28);

  --color-text-primary: #222831;
  --color-text-secondary: #393E46;
  --color-text-muted: #393E46;
  --color-text-heading: #222831;
  --color-text-inverse: #EEEEEE;
  --color-text-on-action: #222831;

  --color-border-subtle: rgba(57, 62, 70, 0.22);
  --color-border-strong: #393E46;
  --color-border-focus: #FFD369;

  --color-status-success-bg: #E6F4EA;
  --color-status-success-text: #1F7A4D;
  --color-status-warning-bg: #FFF4D6;
  --color-status-warning-text: #7A4300;
  --color-status-error-bg: #FDECEC;
  --color-status-error-text: #B42318;
  --color-status-info-bg: #EEEEEE;
  --color-status-info-text: #393E46;
}
```

### Tipografia

```css
:root {
  --font-family-body: "Work Sans", system-ui, sans-serif;
  --font-family-display: "Work Sans", system-ui, sans-serif;
  --font-family-mono: "Geist Mono", "JetBrains Mono", ui-monospace, monospace;

  --font-size-xs: 0.75rem;
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-md: 1.125rem;
  --font-size-lg: 1.25rem;
  --font-size-xl: 1.5rem;
  --font-size-2xl: 2rem;
  --font-size-3xl: 2.75rem;

  --font-weight-regular: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;
  --font-weight-heavy: 800;

  --line-height-tight: 1.08;
  --line-height-normal: 1.45;
  --line-height-loose: 1.65;
  --letter-spacing-normal: 0;
  --letter-spacing-label: 0.06em;
}
```

### Espaçamento, bordas e sombra

```css
:root {
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-5: 1.5rem;
  --space-6: 2rem;
  --space-7: 3rem;
  --space-8: 4rem;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-full: 999px;

  --shadow-surface: 0 14px 34px rgba(34, 40, 49, 0.12);
  --shadow-overlay: 0 24px 60px rgba(34, 40, 49, 0.22);
  --focus-ring: 0 0 0 3px rgba(255, 211, 105, 0.48);
}
```

## Componentes base

### Header

- Deve ficar no topo e preservar acesso rápido aos fluxos principais.
- Pode ser sticky em ferramentas operacionais.
- Marca ou produto no canto esquerdo; navegação e ações de sessão no canto direito.
- Em mobile, priorize título da tela, ação principal e menu compacto.

### Botão primário

- Use `--color-brand-action` com texto `--color-text-on-action`.
- Deve representar a ação mais importante da tela.
- Não use texto branco em botão dourado; o contraste correto é com texto escuro.
- Evite mais de um botão primário no mesmo grupo visual.
- Altura mínima recomendada: `44px` em telas tocáveis.

### Botão secundário

- Fundo claro ou transparente.
- Borda neutra.
- Use para navegação, cancelamento leve, visualização ou ações alternativas.
- Não deve competir visualmente com o botão primário.

### Botão destrutivo

- Use apenas para remoção, perda de dados ou interrupção real.
- Exija texto explícito: `Excluir projeto`, `Cancelar envio`, `Remover acesso`.
- Evite rótulos genéricos como `Confirmar` quando a ação for destrutiva.

### Formulários

- Campos com altura mínima de `44px`.
- Labels acima do campo.
- Mensagens de ajuda curtas abaixo ou próximas do campo.
- Erros devem explicar o problema e a correção esperada.
- Campos obrigatórios devem ser evidentes pelo contexto, label ou validação.

### Painéis e cards

- Use cards para itens repetidos, resultados, métricas e blocos de formulário.
- Evite cards aninhados.
- Raio padrão de `8px`, borda sutil e sombra leve quando precisar separar a camada.
- Não transforme toda seção em card se um layout aberto resolver melhor.

### Status e badges

- Use formato pill.
- Texto curto, preferencialmente substantivo ou estado canônico.
- Use mono para status técnicos, códigos, IDs e metadados.
- Não dependa apenas da cor: inclua texto claro.

### Tabelas e métricas

- Tabelas devem ser simples, escaneáveis e responsivas.
- Números e contadores podem usar fonte mono.
- Cards de métrica devem destacar o número antes do label.
- Em mobile, tabelas podem virar listas compactas quando houver muitas colunas.

### Modais e overlays

- Use modal apenas quando a decisão bloquear o fluxo atual.
- O título deve explicar a decisão, não apenas repetir o botão.
- Deve haver fechamento por teclado e foco gerenciado.
- Ação destrutiva em modal deve ser explícita.

## Responsividade

Breakpoints recomendados:

- `520px`: celular pequeno; ações e grids viram uma coluna.
- `768px`: celular grande/tablet; navegação pode mudar de menu para abas.
- `960px`: tablet/desktop pequeno; grids podem ganhar duas ou três colunas.
- `1180px`: largura máxima confortável para ferramentas internas.

Regras:

- Botões importantes devem ocupar largura total em telas pequenas.
- Grids devem usar `auto-fit` com largura mínima clara.
- Não dependa de hover para operações essenciais.
- Evite texto que só funciona em desktop.
- Use largura máxima para leitura longa; use largura ampla apenas para dados e ferramentas.

## Acessibilidade

- Todo controle interativo precisa ter estado de foco visível.
- O foco recomendado usa `--focus-ring`.
- Tamanho mínimo de alvo: `24px` por WCAG 2.2 AA; use `44px` como padrão prático para toque.
- Texto normal deve ter contraste mínimo de `4.5:1`; texto grande, `3:1`.
- Não comunique erro apenas por cor.
- Labels visuais devem corresponder ao nome acessível do controle.
- Respeite `prefers-reduced-motion`.

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    scroll-behavior: auto !important;
    transition: none !important;
    animation: none !important;
  }
}
```

## Estados obrigatórios

Toda tela relevante deve prever:

- **Carregando**: indique o que está sendo carregado.
- **Vazio**: explique o estado e a próxima ação possível.
- **Erro**: diga o que falhou e o que o usuário pode tentar.
- **Sucesso**: confirme a ação sem criar ruído.
- **Bloqueado**: explique permissão, pré-requisito ou etapa pendente.
- **Offline ou indisponível**: preserve dados locais quando possível e explique recuperação.

## Tema escuro e alto contraste

Novos apps devem nascer com tokens preparados para temas, mesmo que a primeira versão use apenas tema claro.

Arquitetura recomendada:

```css
:root {
  color-scheme: light;
}

[data-theme="dark"] {
  color-scheme: dark;
  --color-bg-page: #222831;
  --color-bg-surface: #393E46;
  --color-bg-subtle: #393E46;
  --color-text-primary: #EEEEEE;
  --color-text-secondary: #EEEEEE;
  --color-text-heading: #EEEEEE;
  --color-border-subtle: rgba(238, 238, 238, 0.22);
  --color-border-strong: #FFD369;
}
```

## Ajuste por projeto

Cada novo produto pode adaptar:

- Cor primária local.
- Cor de ação local.
- Densidade de layout.
- Componentes específicos do domínio.
- Imagens, ícones e tom visual compatíveis com o público.

Cada novo produto deve preservar:

- `Work Sans` como fonte padrão.
- Escala de espaçamento baseada em tokens.
- Raio padrão de `8px` para cards e controles.
- Foco visível.
- Estados de interface documentados.
- Contraste mínimo validado.
- Separação entre tokens globais, semânticos e de componente.

## Checklist para novos apps

- Existe ação primária clara?
- Cores usam tokens, não hex solto?
- Tipografia segue `Work Sans`?
- Bordas, radius e sombras seguem o padrão?
- Mobile funciona antes do desktop?
- Estados de vazio, erro, sucesso e bloqueio foram definidos?
- Foco de teclado está visível?
- Alvos de toque têm tamanho suficiente?
- Contraste de texto foi validado?
- Os termos de domínio foram conferidos antes de nomear telas e campos?
- As exceções visuais do produto foram registradas?

## Referências usadas para este padrão

- WCAG 2.2 para contraste mínimo, foco visível, alvo de toque e critérios testáveis.
- Design Tokens Community Group para tokens como vocabulário comum entre design, código e documentação.
- Work Sans como família tipográfica aberta, otimizada para uso em tela.






