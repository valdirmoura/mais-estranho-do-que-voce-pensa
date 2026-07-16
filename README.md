# Você é mais estranho do que pensa

Quiz que estima, com dados reais do IBGE, quantos brasileiros adultos
compartilham exatamente o seu perfil — cruzando sexo, idade, região,
cor/raça, escolaridade, renda domiciliar per capita, situação de trabalho e
acesso à internet no domicílio. Um bônus opcional soma religião e
posicionamento político, condicionado à demografia, com dados do ESEB 2022.

Adaptação para dados brasileiros de ["You're Weirder Than You
Think"](https://www.atvbt.com/youre-weirder-than-you-think), de Uri
(atvbt.com).

## Como funciona

- **Núcleo (8 perguntas):** PNAD Contínua 2025, visita 1 (IBGE) —
  308.384 entrevistados adultos, pesos amostrais projetando ~161,2 milhões
  de adultos. O resultado é uma **contagem direta** de combinações na
  amostra ponderada — não multiplicação de probabilidades independentes
  (as características do mundo real são correlacionadas: escolaridade e
  renda andam juntas, por exemplo). Quando uma combinação não aparece na
  amostra, o quiz nunca diz "0 pessoas": mostra um piso honesto, "menos de
  1 em 308 mil".
- **Bônus (religião + política):** ESEB 2022 (CESOP/UNICAMP), estimativa
  condicionada ao perfil demográfico do usuário — aproximada, por isso
  aparece separada do resultado principal.
- **Privacidade:** o cálculo roda 100% no navegador. Nenhuma resposta é
  enviada a um servidor. O único dado que sai do aparelho é um contador
  anônimo de "quiz concluído" (sem payload de respostas).

Hospedado na VPS Oracle da Anmaru: https://voceestranho.anmaru.com/

## Estrutura do repositório

```
.
├── infra/vps/         # Deploy na VPS Oracle (compose.yml, .env.example, README.md)
├── pipeline/          # Pipeline Python: baixa e processa os microdados
│   ├── src/quizbr/    #   baixar.py, leitor.py, recode.py, agregar.py, bonus.py, sanidade.py
│   ├── raw/           #   dados brutos baixados (fora do git, .gitkeep only)
│   ├── out/           #   core.json / bonus.json gerados (commitados no git)
│   └── tests/
├── site/               # Astro 7 + React 19 + Tailwind 4
│   ├── src/pages/index.astro     # artigo + ilha do quiz
│   ├── src/components/           # Quiz, Pergunta, Resultado, Bonus
│   ├── src/lib/                  # lookup, share, tipos
│   ├── server/                   # servidor Node (estáticos + /api/contador, Redis)
│   ├── Dockerfile                # imagem usada pelo infra/vps/compose.yml
│   ├── scripts/copiar-dados.mjs  # copia pipeline/out/*.json -> site/public/data/
│   └── public/data/              # core.json (e bonus.json, se gerado) servidos estaticamente
└── docs/, .superpowers/          # specs, planos e histórico de execução do projeto
```

## Rodando o pipeline de dados

Pré-requisitos: Python 3.11+, dependências em `pipeline/pyproject.toml` (pandas, pyreadstat etc).

```bash
python -m venv .venv && .venv\Scripts\activate   # ou source .venv/bin/activate no Linux/Mac
.venv\Scripts\pip install -r pipeline\requirements.txt
.venv\Scripts\pip install -e pipeline
```

### 1. Núcleo (PNAD Contínua)

Confirme ano/visita/variáveis antes de rodar — **os nomes de arquivo e as
posições de coluna do IBGE mudam a cada ano**. Veja o passo a passo completo
em [`pipeline/README.md`](pipeline/README.md). Resumo:

```bash
python -m quizbr.baixar      # baixa pipeline/raw/pnad.zip (~180 MB) e o dicionário
python -m quizbr.agregar     # gera pipeline/out/core.json
```

Para atualizar para um novo ano da PNAD: edite `pipeline/src/quizbr/config.py`
(`ANO`, `SALARIO_MINIMO`, `PNAD_ZIP_URL`, `PNAD_INPUT_URL`,
`VAR_INTERNET`, `VAR_RDPC`) seguindo o procedimento de confirmação
documentado em `pipeline/README.md`, depois rode `baixar` e `agregar` de novo.

### 2. Bônus (ESEB 2022 via CSES Módulo 6 — manual)

Religião e política vêm do ESEB 2022. Em vez do `.sav` nativo do CESOP
(que exige cadastro), usamos o **componente brasileiro do CSES Módulo 6**
(Comparative Study of Electoral Systems, Universidade de Michigan) — mesmo
estudo, n=2001, com download direto e sem cadastro:

1. Baixe em https://cses.org/data-download/cses-module-6-2021-2026/ os
   arquivos SPSS e codebook (`cses6_spss.zip`, `cses6_codebook.zip`).
2. Extraia para `pipeline/raw/cses6/` (deve conter `cses6.sav`).
3. Rode:

```bash
python -m quizbr.bonus       # filtra BRA_2022 e gera pipeline/out/bonus.json
```

`bonus.py` usa as variáveis harmonizadas do CSES (F2002 sexo, F2001_A idade,
F2003 escolaridade ISCED, F2011 religião, F2018 região, F3020_R esquerda-
direita), confirmadas contra o codebook do ESEB (`pipeline/raw/TF_04810.pdf`).

O site funciona normalmente sem esse arquivo — o bônus apenas fica
indisponível (degradação graciosa).

### 3. Levar os dados para o site

```bash
cd site
npm run dados     # copia pipeline/out/{core,bonus}.json -> site/public/data/
```

## Rodando o site localmente

```bash
cd site
npm install
npm run dev        # http://localhost:4321
```

Outros comandos: `npm run build` (build estático em `site/dist/`), `npm run
preview` (serve o build), `npm test` (vitest).

## Deploy (VPS Oracle)

O quiz roda inteiramente na VPS Oracle da Anmaru (`147.15.78.16`), como
dois containers Docker: `quiz-app` (Node — estáticos + `/api/contador`) e
`quiz-redis` (contador de conclusões, self-hosted). Instruções completas
em [`infra/vps/README.md`](infra/vps/README.md).

Resumo:

```bash
ssh ubuntu@147.15.78.16
cd ~/voceestranho && git pull
cd infra/vps && docker compose --env-file .env -f compose.yml up -d --build
```

O domínio `voceestranho.anmaru.com` aponta (registro A) direto para a
VPS; o Caddy central (`vps-gateway`) faz o proxy reverso e emite o
certificado HTTPS automaticamente.

## Pendências (para o usuário)

- [ ] **Divulgar o link** para amigos e conhecidos — o restante é orgânico.
      Estatísticas anônimas:
      `curl https://voceestranho.anmaru.com/api/estatisticas`.

Concluído: o bônus de religião/política está **ativo em produção**, com dados
do ESEB 2022 via CSES Módulo 6 (ver "Bônus" acima). Nota: o ESEB não é
ponderado para representatividade populacional (~49% católica, ~31%
evangélica na amostra, vs ~57%/27% no Censo 2022), por isso o bônus é
rotulado no site como aproximação, separado do resultado principal.
