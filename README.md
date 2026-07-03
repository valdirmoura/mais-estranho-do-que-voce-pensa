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

## Estrutura do repositório

```
.
├── pipeline/          # Pipeline Python: baixa e processa os microdados
│   ├── src/quizbr/    #   baixar.py, leitor.py, recode.py, agregar.py, bonus.py, sanidade.py
│   ├── raw/           #   dados brutos baixados (fora do git, .gitkeep only)
│   ├── out/           #   core.json / bonus.json gerados (fora do git)
│   └── tests/
├── site/               # Astro 7 + React 19 + Tailwind 4
│   ├── src/pages/index.astro     # artigo + ilha do quiz
│   ├── src/components/           # Quiz, Pergunta, Resultado, Bonus
│   ├── src/lib/                  # lookup, share, tipos
│   ├── api/contador.ts           # serverless function (contador anônimo, Upstash)
│   ├── scripts/copiar-dados.mjs  # copia pipeline/out/*.json -> site/public/data/
│   └── public/data/              # core.json (e bonus.json, se gerado) servidos estaticamente
└── docs/, .superpowers/          # specs, planos e histórico de execução do projeto
```

## Rodando o pipeline de dados

Pré-requisitos: Python 3.11+, dependências em `pipeline/pyproject.toml` (pandas, pyreadstat etc).

```bash
cd pipeline
python -m venv .venv && .venv/Scripts/activate   # ou source .venv/bin/activate no Linux/Mac
pip install -e .
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

### 2. Bônus (ESEB 2022 — manual)

O ESEB exige cadastro gratuito no CESOP/UNICAMP:

1. Acesse https://cesop.unicamp.br/, localize "ESEB 2022" no catálogo.
2. Baixe o arquivo SPSS (`.sav`) e salve como `pipeline/raw/eseb2022.sav`.
3. Rode:

```bash
python -m quizbr.bonus       # gera pipeline/out/bonus.json
```

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

## Deploy (Vercel)

O diretório raiz do projeto Vercel é `site/`. Build estático (Astro) +
`site/api/contador.ts` como serverless function (detectado automaticamente).

```bash
cd site
npx vercel --yes     # primeira vez: cria o projeto
npx vercel --prod     # deploy de produção
```

Depois do primeiro deploy:

- **Vercel Analytics:** ative no dashboard do projeto (Analytics tab).
- **Contador de conclusões:** crie um banco Upstash Redis pelo marketplace
  de integrações da Vercel, defina as env vars `UPSTASH_REDIS_REST_URL` e
  `UPSTASH_REDIS_REST_TOKEN` no projeto e faça redeploy. Sem essas env
  vars, `/api/contador` responde `{ "count": null }` e o site funciona
  normalmente sem exibir o contador.

## Pendências (para o usuário)

- [ ] Baixar `eseb2022.sav` do CESOP e rodar `python -m quizbr.bonus`, depois
      `npm run dados` (dentro de `site/`) e redeploy, para ativar o bônus de
      religião/política em produção.
- [ ] Criar um banco Upstash Redis no marketplace da Vercel e configurar
      `UPSTASH_REDIS_REST_URL` / `UPSTASH_REDIS_REST_TOKEN` nas env vars do
      projeto, depois redeploy, para ativar o contador de conclusões.
- [ ] Ativar o Vercel Analytics no dashboard do projeto.
