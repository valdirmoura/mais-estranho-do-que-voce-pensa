# Brand Guidelines

Status: padrão corporativo inicial para projetos da Anmaru.

Este guia define a base de identidade para produtos, documentos, protótipos e interfaces digitais criados dentro da Anmaru. Ele deve ser usado antes de iniciar um novo projeto, escolher cores locais, criar telas, escrever textos comerciais ou montar dashboards.

## Princípio da marca

A marca Anmaru deve comunicar clareza, critério e capacidade de transformar problemas reais em soluções digitais simples de operar.

Use uma linguagem visual direta, limpa e confiável. Evite excesso de decoração, efeitos chamativos, metáforas visuais genéricas ou estilos que pareçam uma campanha isolada em vez de um sistema consistente.

## Nome e assinatura

- Nome corporativo: Anmaru
- Uso em produtos: `Anmaru` pode aparecer como assinatura institucional; o nome do produto deve ser curto, funcional e fácil de reconhecer.
- Assinatura recomendada para novos produtos: uma frase curta que explique o papel do produto, não uma promessa ampla.

Em novos produtos da empresa, mantenha a mesma lógica: nome claro, função evidente e assinatura apenas quando ela reduzir ambiguidade.

## Arquitetura de marca

- **Anmaru**: marca institucional e padrão visual comum.
- **Produto**: aplicação, ferramenta ou serviço específico criado pela empresa.
- **Módulo**: área interna de um produto.
- **Fluxo**: sequência de ações que resolve uma tarefa do usuário.

Evite criar nomes novos para módulos ou fluxos quando uma descrição funcional resolver melhor.

## Cores da marca

A paleta abaixo é a base corporativa oficial da Anmaru. Todo projeto novo deve manter esta estrutura: cor escura institucional, grafite de apoio, acento dourado, neutro claro, feedback e estados.

### Paleta principal

| Uso | Cor | Hex |
| --- | --- | --- |
| Preto Anmaru | Base institucional, navegação, títulos e fundos inversos | `#222831` |
| Grafite Anmaru | Superfícies escuras, apoios, bordas fortes e estados secundários | `#393E46` |
| Dourado Anmaru | Ação principal, destaque e pontos de decisão | `#FFD369` |
| Claro Anmaru | Fundo claro, superfícies suaves e áreas de leitura | `#EEEEEE` |

### Paleta de interface

| Uso | Cor | Hex |
| --- | --- | --- |
| Texto principal | Texto de leitura e labels importantes em fundo claro | `#222831` |
| Texto secundário | Apoio, metadados e descrições | `#393E46` |
| Texto inverso | Texto sobre fundos escuros | `#EEEEEE` |
| Fundo de página | Base de telas e documentos digitais | `#EEEEEE` |
| Superfície escura | Headers, barras laterais, rodapés e áreas de comando | `#222831` |
| Superfície grafite | Painéis escuros, estados elevados e blocos de apoio | `#393E46` |
| Linha sutil | `#393E46` com baixa opacidade em fundos claros | `rgba(57, 62, 70, 0.22)` |
| Linha forte | Separação estrutural em fundos claros | `#393E46` |
| Fundo informativo | Áreas de apoio e destaques leves | `#EEEEEE` |
| Fundo de ação suave | `#FFD369` com baixa opacidade | `rgba(255, 211, 105, 0.28)` |

### Feedback

| Uso | Cor | Hex |
| --- | --- | --- |
| Sucesso | Confirmação e conclusão | `#1F7A4D` |
| Alerta | Atenção sem bloqueio | `#A15C00` |
| Erro | Falha, perigo e ação destrutiva | `#B42318` |
| Informação | Estado neutro-informativo | `#393E46` |

## Regras de uso de cor

- Use `#222831` para estrutura, confiança, navegação, títulos e fundos institucionais.
- Use `#393E46` para apoio, superfícies escuras secundárias e hierarquia intermediária.
- Use `#FFD369` para a ação principal da tela ou para decisões que exigem atenção.
- Em componentes com fundo `#FFD369`, use texto `#222831`; não use texto branco sobre dourado.
- Não use dourado em excesso; se tudo parece acionável, nada parece prioritário.
- Não comunique significado apenas por cor. Combine cor com texto, ícone, padrão ou posição.
- Valide contraste antes de aprovar novas combinações. Texto normal deve mirar WCAG AA.
- Cores específicas de produto devem ser adicionadas como tokens semânticos, não como hex solto no componente.

## Tipografia

### Fontes

- Fonte principal: `Work Sans`
- Fonte de apoio/monoespacada: `Geist Mono`, `JetBrains Mono` ou `ui-monospace`
- Fallback: `system-ui, sans-serif` para texto comum e `monospace` para códigos/metadados.

### Uso

- Use `Work Sans` para títulos, corpo, botões, formulários, navegação e materiais digitais.
- Use mono apenas para código, IDs, labels técnicas, métricas tabulares e metadados.
- Use pesos `400`, `500`, `600` e `700` como padrão. Reserve `800` para títulos de alto impacto.
- Evite letter spacing negativo. Labels em caixa alta podem usar letter spacing positivo discreto.
- Texto de interface deve ser curto, específico e orientado à ação.

## Forma visual

- Raio padrão: `8px`
- Pills e badges: `999px`
- Bordas: finas, neutras e consistentes.
- Sombras: leves, usadas para separar camadas, nunca como efeito decorativo pesado.
- Layout: mobile-first, com conteúdo denso, legível e bem hierarquizado.
- Imagens: use imagens reais ou geradas quando o usuário precisa reconhecer produto, pessoa, lugar ou objeto. Não substitua conteúdo concreto por abstrações decorativas.

## Voz visual e textual

A marca deve parecer:

- Clara
- Criteriosa
- Confiável
- Operacional
- Humana sem informalidade excessiva

Evite:

- Linguagem promocional exagerada
- Jargões sem necessidade
- Promessas absolutas
- Interfaces com cara de campanha quando o produto é operacional
- Elementos visuais que escondam a informação principal

## Aplicação em produtos

Todo novo app da Anmaru deve:

- Usar `Work Sans` como fonte padrão.
- Definir uma paleta local a partir dos tokens corporativos.
- Ter uma ação primária claramente identificável por tela.
- Manter hierarquia forte em títulos, labels e estados.
- Priorizar legibilidade, acessibilidade e velocidade de uso.
- Evitar estilos locais que contradigam este guia sem decisão registrada.
- Documentar exceções de marca em um ADR, README de design ou seção equivalente do projeto.

## Checklist de marca

- O produto usa `Anmaru` como assinatura institucional quando necessário?
- O nome do produto é curto, funcional e memorável?
- A paleta local está mapeada para tokens semânticos?
- A cor principal e a cor de ação não competem entre si?
- A tipografia usa `Work Sans` de forma consistente?
- As telas parecem parte do mesmo sistema, mesmo com ajustes por projeto?
- A linguagem promete apenas o que o produto realmente entrega?

## Referências usadas para este padrão

- WCAG 2.2 para contraste, foco visível, alvo de toque e acessibilidade de interface.
- Design Tokens Community Group para separar decisões visuais em tokens reutilizáveis.
- Work Sans como fonte aberta otimizada para texto digital em tamanhos médios.





