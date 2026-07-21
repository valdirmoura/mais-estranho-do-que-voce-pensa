# Migração para a VPS Oracle — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sair da Vercel e hospedar o quiz inteiramente na VPS Oracle da Anmaru (`147.15.78.16`), com um servidor Node próprio (estáticos + contador) e Redis auto-hospedado, seguindo a convenção já usada pelos outros projetos da VPS.

**Architecture:** Um container `quiz-app` (Node) serve os arquivos estáticos do Astro e responde `/api/contador`; um container `quiz-redis` (`redis:7-alpine`) guarda a contagem, isolado numa rede interna própria. O Caddy central (`vps-gateway`, já rodando) ganha um bloco de site novo fazendo reverse proxy para `quiz-app:3000`. DNS só muda por último, depois de tudo verificado localmente e na VPS.

**Tech Stack:** Node 22 (`http` nativo + `serve-handler` + cliente `redis`), Docker/Docker Compose, Caddy 2.8 (já existente), Astro 7 (build estático, sem mudança).

**Spec:** `docs/superpowers/specs/2026-07-13-migracao-vps-oracle-design.md`

## Global Constraints

- VPS Oracle: IP `147.15.78.16`, usuário SSH `ubuntu`, chave privada em
  `C:\Users\valdir\apps\anmaru\VPS Oracle\ssh-key-2026-07-08.key`.
- Rede Docker pública compartilhada: `vps_public` (externa, definida em
  `~/vps-gateway/infra/vps/compose.yml` — já existe na VPS, não recriar).
- Convenção de projeto na VPS: pasta própria `~/<projeto>/infra/vps/` com
  `compose.yml`, `.env.example`, `README.md`. Isolamento total de outros
  projetos: nenhuma rede, volume ou variável compartilhada além do
  necessário para o Caddy alcançar o container.
- Contador: Redis próprio (`redis:7-alpine`), nunca exposto fora da rede
  interna do projeto (`quiz_internal`) — sem Upstash, sem serviço externo.
- Vercel é descomissionado ao final — sem multihome, sem fallback. Migração
  futura para VPS Hostinger fica fora de escopo deste plano.
- Domínio: `voceestranho.anmaru.com`. O registro DNS só muda de CNAME
  (Vercel) para A (VPS) na Task 6, depois de tudo verificado localmente e
  na VPS sem depender do domínio.
- A Task 5 edita um arquivo (`Caddyfile`) que serve OUTROS projetos já em
  produção (n8n do trendclima). Só **adicionar** um bloco novo ao final;
  nunca editar ou remover blocos existentes. Validar sintaxe antes de
  recarregar o Caddy.
- Commits: Conventional Commits em pt-BR, footer
  `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Repositório GitHub é público: `https://github.com/valdirmoura/voce-estranho` — clone HTTPS na VPS não precisa de credencial.

---

### Task 1: Lógica pura do contador (TDD)

**Files:**
- Create: `site/server/contador.mjs`
- Test: `site/server/contador.test.mjs`

**Interfaces:**
- Produces: `export async function lerOuIncrementar(clienteRedis, metodo)` —
  `clienteRedis` é `null` ou um objeto com métodos assíncronos `incr(chave)`
  e `get(chave)` (mesma forma do cliente oficial `redis`); `metodo` é
  `"GET"` ou `"POST"`. Retorna sempre `{ count: number | null }`. Nunca
  lança exceção. Task 2 consome esta função diretamente.

- [ ] **Step 1: Escrever os testes (falhando)**

```js
// site/server/contador.test.mjs
import { describe, it, expect, vi } from "vitest";
import { lerOuIncrementar } from "./contador.mjs";

describe("lerOuIncrementar", () => {
  it("sem cliente redis, retorna count:null", async () => {
    const r = await lerOuIncrementar(null, "GET");
    expect(r).toEqual({ count: null });
  });

  it("POST incrementa via incr()", async () => {
    const cliente = { incr: vi.fn().mockResolvedValue(7) };
    const r = await lerOuIncrementar(cliente, "POST");
    expect(cliente.incr).toHaveBeenCalledWith("quiz:conclusoes");
    expect(r).toEqual({ count: 7 });
  });

  it("GET sem chave existente retorna 0", async () => {
    const cliente = { get: vi.fn().mockResolvedValue(null) };
    const r = await lerOuIncrementar(cliente, "GET");
    expect(cliente.get).toHaveBeenCalledWith("quiz:conclusoes");
    expect(r).toEqual({ count: 0 });
  });

  it("GET com chave existente retorna o valor como numero", async () => {
    const cliente = { get: vi.fn().mockResolvedValue("42") };
    const r = await lerOuIncrementar(cliente, "GET");
    expect(r).toEqual({ count: 42 });
  });

  it("erro no redis retorna count:null (gracioso, nunca quebra)", async () => {
    const cliente = { incr: vi.fn().mockRejectedValue(new Error("timeout")) };
    const r = await lerOuIncrementar(cliente, "POST");
    expect(r).toEqual({ count: null });
  });
});
```

- [ ] **Step 2: Rodar, verificar falha**

```bash
cd site
npx vitest run server/contador.test.mjs
```
Expected: FAIL — `Cannot find module './contador.mjs'` (ou similar).

- [ ] **Step 3: Implementar**

```js
// site/server/contador.mjs
const CHAVE = "quiz:conclusoes";

export async function lerOuIncrementar(clienteRedis, metodo) {
  if (!clienteRedis) return { count: null };
  try {
    const valor =
      metodo === "POST"
        ? await clienteRedis.incr(CHAVE)
        : await clienteRedis.get(CHAVE);
    return { count: valor === null ? 0 : Number(valor) };
  } catch {
    return { count: null };
  }
}
```

- [ ] **Step 4: Rodar, verificar sucesso**

```bash
npx vitest run server/contador.test.mjs
```
Expected: 5 testes passando.

- [ ] **Step 5: Rodar a suíte inteira do site (não deve quebrar nada existente)**

```bash
npx vitest run
```
Expected: todos os testes (os 7 já existentes de `src/lib` + os 5 novos)
passando, 12 no total.

- [ ] **Step 6: Commit**

```bash
git add site/server/contador.mjs site/server/contador.test.mjs
git commit -m "feat: lógica pura do contador de conclusões (Redis)"
```

---

### Task 2: Servidor Node (estáticos + API) e remoção da camada Vercel

**Files:**
- Create: `site/server/index.mjs`
- Modify: `site/package.json`
- Delete: `site/api/contador.ts`

**Interfaces:**
- Consumes: `lerOuIncrementar` de `site/server/contador.mjs` (Task 1).
- Produces: processo HTTP ouvindo em `process.env.PORT` (padrão `3000`);
  serve `site/dist/` como estático e responde `GET`/`POST` em
  `/api/contador`. Variável de ambiente `REDIS_URL` (se ausente ou
  inválida, o servidor sobe mesmo assim com `clienteRedis = null`).
  Task 3 (Dockerfile) e Task 4 (compose.yml) dependem desse contrato de
  variáveis de ambiente e porta.

- [ ] **Step 1: Instalar as dependências novas e remover a da Vercel**

```bash
cd site
npm install redis serve-handler
npm uninstall @vercel/node
```

- [ ] **Step 2: Adicionar o script `start` em `site/package.json`**

Abra `site/package.json` e adicione `"start"` ao bloco `"scripts"` (mantendo
os demais como estão):

```json
    "dados": "node scripts/copiar-dados.mjs",
    "assets": "node scripts/gerar-assets.mjs",
    "start": "node server/index.mjs"
```

- [ ] **Step 3: Implementar o servidor**

```js
// site/server/index.mjs
import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import handler from "serve-handler";
import { createClient } from "redis";
import { lerOuIncrementar } from "./contador.mjs";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DIST_DIR = path.join(__dirname, "..", "dist");
const PORT = Number(process.env.PORT) || 3000;

async function criarClienteRedis() {
  const url = process.env.REDIS_URL;
  if (!url) return null;
  const cliente = createClient({ url });
  cliente.on("error", (erro) => console.error("[redis] erro:", erro.message));
  try {
    await cliente.connect();
    return cliente;
  } catch (erro) {
    console.error("[redis] falha ao conectar:", erro.message);
    return null;
  }
}

const clienteRedis = await criarClienteRedis();

const servidor = http.createServer(async (req, res) => {
  if (req.url === "/api/contador") {
    const resultado = await lerOuIncrementar(clienteRedis, req.method);
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(resultado));
    return;
  }
  await handler(req, res, { public: DIST_DIR });
});

servidor.listen(PORT, () => {
  console.log(
    `quiz-app ouvindo na porta ${PORT} (redis: ${clienteRedis ? "conectado" : "indisponível"})`,
  );
});
```

- [ ] **Step 4: Remover o arquivo específico da Vercel**

```bash
git rm site/api/contador.ts
rmdir site/api 2>/dev/null || true
```

- [ ] **Step 5: Build e verificação manual sem Redis (deve subir e responder count:null)**

```bash
npm run build
PORT=3001 node server/index.mjs &
sleep 1
curl -s http://localhost:3001/ | grep -o "<title>[^<]*</title>"
curl -s http://localhost:3001/api/contador
kill %1
```
Expected: título `<title>Você é mais estranho do que pensa</title>`;
`{"count":null}` (sem `REDIS_URL`, gracioso).

- [ ] **Step 6: Verificação manual com Redis local (deve incrementar de verdade)**

```bash
docker run --rm -d --name quiz-redis-dev -p 6379:6379 redis:7-alpine
sleep 1
REDIS_URL=redis://127.0.0.1:6379 PORT=3001 node server/index.mjs &
sleep 1
curl -s -X POST http://localhost:3001/api/contador
curl -s -X POST http://localhost:3001/api/contador
curl -s http://localhost:3001/api/contador
kill %1
docker rm -f quiz-redis-dev
```
Expected: `{"count":1}`, `{"count":2}`, `{"count":2}` (GET não incrementa).

- [ ] **Step 7: Rodar a suíte de testes (nada deve ter quebrado)**

```bash
npx vitest run
```
Expected: 12 testes passando (Task 1 não é afetada por esta task).

- [ ] **Step 8: Commit**

```bash
git add site/server/index.mjs site/package.json site/package-lock.json
git commit -m "feat: servidor Node substitui a função serverless da Vercel"
```

---

### Task 3: Dockerfile multi-stage + verificação local com Docker

**Files:**
- Create: `site/Dockerfile`
- Create: `site/.dockerignore`

**Interfaces:**
- Consumes: `site/server/index.mjs` (Task 2), contrato de env vars
  `PORT`/`REDIS_URL`.
- Produces: imagem Docker `quiz-app` que expõe a porta `3000` e roda
  `node server/index.mjs`. Task 4 (compose.yml) referencia este Dockerfile
  via `build: { context: ../../site, dockerfile: Dockerfile }`.

- [ ] **Step 1: Criar o `.dockerignore`**

```
# site/.dockerignore
node_modules
dist
.astro
.env
.env.*
*.log
```

- [ ] **Step 2: Criar o Dockerfile**

```dockerfile
# site/Dockerfile
FROM node:22-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM node:22-alpine AS runtime
WORKDIR /app
ENV NODE_ENV=production
COPY package.json package-lock.json ./
RUN npm ci --omit=dev
COPY --from=build /app/dist ./dist
COPY server ./server
EXPOSE 3000
CMD ["node", "server/index.mjs"]
```

- [ ] **Step 3: Buildar a imagem localmente**

```bash
cd site
docker build -t quiz-app:local .
```
Expected: build completo sem erro, última linha `naming to
docker.io/library/quiz-app:local`.

- [ ] **Step 4: Rodar a imagem localmente com Redis, ponta a ponta**

```bash
docker network create quiz-test-net
docker run -d --name quiz-redis-test --network quiz-test-net redis:7-alpine
docker run -d --name quiz-app-test --network quiz-test-net \
  -e REDIS_URL=redis://quiz-redis-test:6379 -e PORT=3000 \
  -p 3002:3000 quiz-app:local
sleep 2
curl -s http://localhost:3002/ | grep -o "<title>[^<]*</title>"
curl -s -X POST http://localhost:3002/api/contador
curl -s http://localhost:3002/data/core.json | head -c 80
```
Expected: título correto; `{"count":1}`; início do JSON do `core.json`
(algo como `{"meta":{"fonte":"PNAD Contínua 2025 (IBGE)"`).

- [ ] **Step 5: Limpar os recursos de teste**

```bash
docker rm -f quiz-app-test quiz-redis-test
docker network rm quiz-test-net
```

- [ ] **Step 6: Commit**

```bash
git add site/Dockerfile site/.dockerignore
git commit -m "feat: Dockerfile multi-stage para o quiz-app"
```

---

### Task 4: `infra/vps/` — compose, env e README (com dry-run local)

**Files:**
- Create: `infra/vps/compose.yml`
- Create: `infra/vps/.env.example`
- Create: `infra/vps/README.md`

**Interfaces:**
- Consumes: `site/Dockerfile` (Task 3, via `build.context: ../../site`),
  rede externa `vps_public` (já existe na VPS; para o dry-run local, esta
  task cria uma rede local com o mesmo nome).
- Produces: pilha Docker Compose nomeada `voceestranho`, serviços
  `quiz-app` (porta interna `3000`, variável `PORT`/`REDIS_URL`) e
  `quiz-redis` — nomes de container usados literalmente pela Task 5 ao
  editar o Caddyfile (`reverse_proxy quiz-app:3000`).

- [ ] **Step 1: Criar `infra/vps/.env.example`**

```bash
# infra/vps/.env.example
REDIS_URL=redis://quiz-redis:6379
PORT=3000
```

- [ ] **Step 2: Criar `infra/vps/compose.yml`**

```yaml
# infra/vps/compose.yml
name: voceestranho

services:
  quiz-redis:
    image: redis:7-alpine
    container_name: quiz-redis
    restart: unless-stopped
    volumes:
      - quiz_redis_data:/data
    networks:
      - quiz_internal
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  quiz-app:
    build:
      context: ../../site
      dockerfile: Dockerfile
    container_name: quiz-app
    restart: unless-stopped
    depends_on:
      quiz-redis:
        condition: service_healthy
    environment:
      REDIS_URL: ${REDIS_URL}
      PORT: ${PORT}
    networks:
      - vps_public
      - quiz_internal

networks:
  vps_public:
    external: true
    name: vps_public
  quiz_internal:
    internal: true

volumes:
  quiz_redis_data:
```

- [ ] **Step 3: Criar `infra/vps/README.md`**

```markdown
# Deploy — voceestranho (VPS Oracle)

Pré-requisito: a VPS já roda a base `vps-gateway` (Caddy) com a rede
externa `vps_public` criada (ver `~/vps-gateway`).

## Primeira vez

\`\`\`bash
git clone https://github.com/valdirmoura/voce-estranho.git ~/voceestranho
cd ~/voceestranho/infra/vps
cp .env.example .env
docker compose --env-file .env -f compose.yml up -d --build
\`\`\`

## Atualizações seguintes

\`\`\`bash
cd ~/voceestranho
git pull
cd infra/vps
docker compose --env-file .env -f compose.yml up -d --build
\`\`\`

## Verificação

\`\`\`bash
docker compose --env-file .env -f compose.yml ps
docker run --rm --network vps_public curlimages/curl curl -s http://quiz-app:3000/
docker run --rm --network vps_public curlimages/curl curl -s -X POST http://quiz-app:3000/api/contador
\`\`\`

## Ligar ao Caddy central

Adicionar ao final de `~/vps-gateway/infra/vps/Caddyfile` (nunca editar
blocos existentes de outros projetos):

\`\`\`
voceestranho.anmaru.com {
  encode gzip
  reverse_proxy quiz-app:3000
}
\`\`\`

Depois:

\`\`\`bash
cd ~/vps-gateway/infra/vps
docker compose --env-file .env -f compose.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose --env-file .env -f compose.yml restart caddy
\`\`\`

O certificado HTTPS só é emitido depois que o registro DNS de
`voceestranho.anmaru.com` apontar (tipo A) para o IP público da VPS.
```

- [ ] **Step 4: Dry-run local completo (sem tocar na VPS)**

```bash
cd infra/vps
cp .env.example .env
docker network create vps_public
docker compose --env-file .env -f compose.yml config >/dev/null && echo "compose.yml válido"
docker compose --env-file .env -f compose.yml up -d --build
sleep 2
docker compose --env-file .env -f compose.yml ps
docker run --rm --network vps_public curlimages/curl curl -s http://quiz-app:3000/ | grep -o "<title>[^<]*</title>"
docker run --rm --network vps_public curlimages/curl curl -s -X POST http://quiz-app:3000/api/contador
```
Expected: `compose.yml válido`; ambos os serviços `running`/`healthy`;
título correto; `{"count":1}`.

- [ ] **Step 5: Limpar o dry-run**

```bash
docker compose --env-file .env -f compose.yml down -v
docker network rm vps_public
rm .env
```

- [ ] **Step 6: Commit**

```bash
git add infra/vps/compose.yml infra/vps/.env.example infra/vps/README.md
git commit -m "feat: infra/vps para deploy do quiz na VPS Oracle"
```

---

### Task 5: Deploy real na VPS + ligação ao Caddy (sem tocar em DNS)

**Files:**
- Nenhum arquivo deste repositório é modificado nesta task — ela executa
  comandos via SSH na VPS e edita `~/vps-gateway/infra/vps/Caddyfile`
  (arquivo de outro projeto, compartilhado).

**Interfaces:**
- Consumes: tudo commitado nas Tasks 1–4 (o `git clone`/`git pull` na VPS
  traz tudo de uma vez).
- Produces: containers `quiz-app` e `quiz-redis` rodando na VPS, na rede
  `vps_public`; bloco de site novo no Caddyfile central, ainda sem DNS
  apontando (Task 6 termina o corte).

⚠️ Esta task toca um arquivo compartilhado com outros projetos em produção
(o Caddyfile também serve `n8n.trendclima.com.br`). Rode com atenção,
adicionando apenas — nunca removendo ou editando blocos existentes.

- [ ] **Step 1: Clonar (ou atualizar) o repositório na VPS**

```bash
KEY="C:\Users\valdir\apps\anmaru\VPS Oracle\ssh-key-2026-07-08.key"
ssh -i "$KEY" ubuntu@147.15.78.16 "test -d ~/voceestranho && (cd ~/voceestranho && git pull) || git clone https://github.com/valdirmoura/voce-estranho.git ~/voceestranho"
```
Expected: `Cloning into 'voceestranho'...` (primeira vez) ou `Already
up to date.`/lista de arquivos atualizados (vezes seguintes).

- [ ] **Step 2: Subir a pilha do projeto**

```bash
ssh -i "$KEY" ubuntu@147.15.78.16 "cd ~/voceestranho/infra/vps && cp -n .env.example .env && docker compose --env-file .env -f compose.yml up -d --build"
```
Expected: build da imagem `quiz-app`, depois `Container quiz-redis
Healthy`, `Container quiz-app Started`.

- [ ] **Step 3: Verificar os containers sem depender do domínio**

```bash
ssh -i "$KEY" ubuntu@147.15.78.16 "docker run --rm --network vps_public curlimages/curl curl -s http://quiz-app:3000/ | grep -o '<title>[^<]*</title>'"
ssh -i "$KEY" ubuntu@147.15.78.16 "docker run --rm --network vps_public curlimages/curl curl -s -X POST http://quiz-app:3000/api/contador"
```
Expected: título `<title>Você é mais estranho do que pensa</title>`;
`{"count":1}` (primeira conclusão real na VPS).

- [ ] **Step 4: Adicionar o bloco no Caddyfile central (idempotente)**

```bash
ssh -i "$KEY" ubuntu@147.15.78.16 'grep -q "voceestranho.anmaru.com" ~/vps-gateway/infra/vps/Caddyfile || printf "\nvoceestranho.anmaru.com {\n  encode gzip\n  reverse_proxy quiz-app:3000\n}\n" >> ~/vps-gateway/infra/vps/Caddyfile'
```
Expected: sem saída (bloco adicionado) ou nada acontece se já existir
(idempotente — seguro rodar de novo).

- [ ] **Step 5: Validar a sintaxe e recarregar o Caddy**

```bash
ssh -i "$KEY" ubuntu@147.15.78.16 "cd ~/vps-gateway/infra/vps && docker compose --env-file .env -f compose.yml exec caddy caddy validate --config /etc/caddy/Caddyfile"
ssh -i "$KEY" ubuntu@147.15.78.16 "cd ~/vps-gateway/infra/vps && docker compose --env-file .env -f compose.yml restart caddy"
```
Expected: `Valid configuration`; container `caddy` reiniciado sem erro.

- [ ] **Step 6: Confirmar que o n8n do trendclima continua no ar (não quebrou nada compartilhado)**

```bash
ssh -i "$KEY" ubuntu@147.15.78.16 "curl -sk -o /dev/null -w '%{http_code}\n' https://n8n.trendclima.com.br/"
```
Expected: `401` (basic auth exigido — é o comportamento normal, confirma
que o Caddy está respondendo para esse host).

---

### Task 6: Corte de DNS, confirmação em produção e decomissionamento da Vercel

**Files:**
- Modify: `README.md` (raiz)

**Interfaces:**
- Consumes: container `quiz-app` já rodando na VPS e bloco já presente no
  Caddyfile (Task 5).

Esta task tem um passo que só o humano pode fazer (painel de DNS da
Hostinger) — o restante é automatizável.

- [ ] **Step 1 (ação humana): trocar o registro DNS**

No painel da Hostinger, no registro `voceestranho`:
1. Apagar o registro **CNAME** existente (apontando para
   `cname.vercel-dns.com`) — não tentar editar o tipo dentro do mesmo
   registro, isso causa o erro "CNAME must not be used with any other
   type on the same name".
2. Criar um registro novo: Tipo **A**, Nome `voceestranho`, Valor
   `147.15.78.16`, TTL `14400`.

- [ ] **Step 2: Aguardar propagação e emissão do certificado**

```bash
until curl -sk -o /dev/null -w "%{http_code}" https://voceestranho.anmaru.com/ 2>/dev/null | grep -q 200; do sleep 15; done
echo "HTTPS pronto"
```
(Rodar em background/monitor — pode levar de minutos a algumas horas
dependendo do TTL antigo do CNAME.)

- [ ] **Step 3: Verificação funcional completa em produção**

```bash
curl -s https://voceestranho.anmaru.com/ | grep -o "<title>[^<]*</title>"
curl -s https://voceestranho.anmaru.com/data/core.json | head -c 80
curl -s -X POST https://voceestranho.anmaru.com/api/contador
curl -s https://voceestranho.anmaru.com/ | grep -o 'rel="canonical" href="[^"]*"'
```
Expected: título correto; início do `core.json`; `{"count":2}` (contando
a conclusão real da Task 5); canonical já é
`https://voceestranho.anmaru.com/` (nenhuma mudança de código necessária
aqui, o valor já está correto desde a migração de domínio anterior).

- [ ] **Step 4: Descomissionar a Vercel**

```bash
cd site
npx vercel remove voceestranho --yes
rm -rf .vercel
```
Expected: `Success! Project removed`. Confirmar no dashboard da Vercel
que o projeto sumiu.

- [ ] **Step 5: Atualizar o README raiz**

Em `README.md`, na seção **"Estrutura do repositório"**, atualizar a
árvore do `site/` (remover `api/contador.ts`, adicionar `server/`) e
acrescentar `infra/vps/` na árvore de topo:

```
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

Substituir toda a seção **"Deploy (Vercel)"** por:

```markdown
## Deploy (VPS Oracle)

O quiz roda inteiramente na VPS Oracle da Anmaru (`147.15.78.16`), como
dois containers Docker: `quiz-app` (Node — estáticos + `/api/contador`) e
`quiz-redis` (contador de conclusões). Instruções completas em
[`infra/vps/README.md`](infra/vps/README.md).

Resumo:

```bash
ssh ubuntu@147.15.78.16
cd ~/voceestranho && git pull
cd infra/vps && docker compose --env-file .env -f compose.yml up -d --build
```

O domínio `voceestranho.anmaru.com` aponta (registro A) direto para a
VPS; o Caddy central (`vps-gateway`) faz o proxy reverso e emite o
certificado HTTPS automaticamente.
```

Substituir a seção **"Pendências (para o usuário)"** — remover os itens
de Upstash e Vercel Analytics (não existem mais nesse hosting), mantendo
apenas o item do ESEB:

```markdown
## Pendências (para o usuário)

- [ ] Baixar `eseb2022.sav` do CESOP e rodar `python -m quizbr.bonus`, depois
      `npm run dados` (dentro de `site/`), `git push` e um novo deploy na
      VPS, para ativar o bônus de religião/política em produção.
```

- [ ] **Step 6: Commit**

```bash
git add README.md
git commit -m "docs: atualizar README para o deploy na VPS Oracle (pós-migração)"
git push
```

---

## Riscos mapeados

1. **Caddyfile compartilhado** (Task 5) — mitigado: só adiciona bloco,
   nunca edita/remove; valida sintaxe antes de recarregar; confirma que o
   n8n do trendclima segue respondendo depois.
2. **Redis não sobe a tempo do quiz-app tentar conectar** — mitigado:
   `depends_on: condition: service_healthy` no compose.yml + healthcheck
   `redis-cli ping`.
3. **Falha de conexão ao Redis em qualquer momento** — mitigado: `try/catch`
   em `criarClienteRedis()` e em `lerOuIncrementar()`; sempre degrada para
   `{count:null}`, nunca derruba o servidor.
4. **Janela de ar entre o corte de DNS e a emissão do certificado** (Task
   6) — esperada e documentada na spec; mitigada por fazer todo o resto
   (Tasks 1–5) primeiro e só then tocar em DNS.
5. **TTL antigo do CNAME (14400s = 4h) atrasando a propagação** — sem
   mitigação automática; Step 2 da Task 6 apenas espera.
