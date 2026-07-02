# Design: "Você é mais estranho do que pensa" — versão brasileira

**Data:** 2026-07-02
**Status:** Aprovado
**Inspiração:** https://www.atvbt.com/youre-weirder-than-you-think (Uri, atvbt.com)

## Objetivo

Ferramenta pública na web + artigo em pt-BR. Quiz interativo que mostra quantos
brasileiros adultos compartilham exatamente a combinação de características do
usuário, usando microdados reais com correlações preservadas (sem multiplicação
de probabilidades independentes). Potencial de compartilhamento viral, com o
contexto da eleição de 2026 como gancho editorial.

## Decisões de produto

- **Núcleo (8 perguntas, PNAD Contínua):** sexo, faixa etária, região,
  cor/raça, escolaridade, renda domiciliar per capita, situação de trabalho,
  acesso à internet. Correlações exatas dentro de uma única fonte.
- **Bônus opcional (ESEB 2022 + Censo 2022):** religião e posicionamento
  político, condicionados à demografia do usuário (região, sexo, faixa etária,
  escolaridade). Opt-in, com disclaimer expansível explicando a mistura de
  fontes e a amostra menor.
- **Resultado:** "1 em X brasileiros adultos têm exatamente sua combinação",
  com comparação concreta (ex.: "menos gente que a cidade Y"). Com bônus,
  estimativa refinada exibida separadamente.
- Público: 18+. Idioma: pt-BR.

## Arquitetura

Site 100% estático com tabelas pré-computadas. Nenhum backend em produção.

```
pipeline (Python, offline)          site (Astro + React island)
┌──────────────────────────┐        ┌────────────────────────────┐
│ microdados PNAD (IBGE)   │──┐     │ artigo (estático, SEO)     │
│ microdados ESEB (CESOP)  │──┼───▶ │ quiz React                 │
│ agregados Censo 2022     │──┘     │  └ lookup em core.json /   │
│  └ recodifica, pondera,  │        │    bonus.json no navegador │
│    agrega → JSON esparso │        └────────────────────────────┘
└──────────────────────────┘                 deploy: Vercel
```

### Componente 1 — Pipeline de dados (`pipeline/`)

- Baixa microdados da PNAD Contínua anual mais recente (FTP público do IBGE,
  ~400 mil pessoas), parse fixed-width com dicionário de layout.
- Filtra 18+; recodifica em categorias grossas:
  - sexo (2), faixa etária (6: 18–24, 25–34, 35–44, 45–54, 55–64, 65+),
    região (5), cor/raça (5: branca, preta, parda, amarela, indígena),
    escolaridade (5), renda domiciliar per capita em faixas de salário
    mínimo (5), situação de trabalho (5: carteira, informal, conta própria,
    desempregado, fora da força), internet (2).
  - Espaço total: 75.000 células.
- Agrega peso amostral (projeção populacional) por célula → tabela conjunta
  esparsa → `data/core.json` (esperado: centenas de KB gzipado). Guarda também
  n amostral bruto por célula.
- ESEB 2022: distribuição de religião × posição política condicionada a
  (região, sexo, faixa etária, escolaridade) → `data/bonus.json`. Células de
  condicionamento com n pequeno recuam para condicionamento mais grosso
  (ex.: só região + escolaridade) — regra registrada no JSON.
- Censo 2022 (tabelas agregadas de religião, divulgadas em 2025): validação
  das margens de religião do ESEB.
- **Sanidade automática:** soma dos pesos = população adulta oficial (±1%);
  margens univariadas batem com tabelas publicadas do IBGE.

### Componente 2 — Site (`site/`)

- Astro + ilha React (quiz) + Tailwind. Página única: artigo com quiz
  embutido.
- Fluxo do quiz: 8 perguntas → resultado → convite ao bônus (opt-in) →
  resultado refinado com disclaimer.
- Lookup 100% client-side nos JSONs. Nada é enviado a servidor — destacar
  como argumento de privacidade.
- Compartilhamento: resultado codificado em query params + Web Share API +
  botão copiar. URL compartilhada renderiza o resultado sem respostas cruas
  expostas além das categorias.

### Células raras / vazias

- Célula com peso zero ou n amostral < limiar: exibir piso honesto —
  "tão raro que não apareceu entre ~400 mil entrevistados: menos de 1 em N"
  (N derivado do total ponderado / resolução da amostra). Nunca exibir
  "0 pessoas".
- Detalhe metodológico (expansível) mostra n amostral e explica pesos.

## Tratamento de erros

- Pipeline: falha ruidosa se layout do IBGE mudar (validação de colunas);
  checks de sanidade abortam build se margens divergirem.
- Site: JSON ausente/corrompido → mensagem de erro amigável, sem quiz
  quebrado silencioso.

## Testes

- **Pipeline (pytest):** margens vs. IBGE oficial, soma total, ausência de
  valores negativos, esquema dos JSONs, regra de recuo do bônus.
- **Site (vitest):** lookup de perfil conhecido → número esperado; célula
  vazia → mensagem de piso; encode/decode de URL de compartilhamento.

## Deploy

Vercel, site estático (output do Astro). Pipeline roda localmente; JSONs
commitados no repositório (dados públicos, tamanho pequeno).

## Fora de escopo (YAGNI)

- Backend/API, DuckDB-WASM, contas de usuário, analytics além do básico,
  outras ondas históricas da PNAD, versão em outros idiomas.
