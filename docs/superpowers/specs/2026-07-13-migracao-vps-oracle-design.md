# Design: migração do quiz para a VPS Oracle da Anmaru

**Data:** 2026-07-13
**Status:** Aprovado

## Objetivo

Sair da Vercel (limite gratuito estourado) e hospedar o quiz inteiramente na
VPS Oracle da Anmaru (`147.15.78.16`), seguindo a convenção já estabelecida
por outros projetos hospedados lá (`vps-gateway`/Caddy como proxy reverso
central + pasta própria por projeto em `~/<projeto>/infra/vps/`).

Vercel é totalmente descomissionado ao final — sem multihome, sem fallback.
Migração futura para uma VPS Hostinger é um projeto separado, fora de escopo.

## Estado atual da VPS (levantado via SSH, 2026-07-13)

- `vps-gateway`: Caddy 2.8, rede externa `vps_public`, Caddyfile em
  `~/vps-gateway/infra/vps/Caddyfile` — um bloco de site por subdomínio,
  reverse proxy para `container:porta`.
- `trendclima`: n8n + Postgres, rede interna própria `trendclima_internal`
  + `vps_public` só no n8n (o serviço que o Caddy precisa alcançar).
- Recursos livres: ~37 GB de disco, ~10 GB de RAM disponível — folga ampla
  para o quiz (estático + um processo Node pequeno).

## Arquitetura

```
Caddy (vps-gateway, já existe)
  └─ voceestranho.anmaru.com → reverse_proxy quiz-app:3000

~/voceestranho/infra/vps/  (novo)
  ├─ quiz-app   (rede vps_public + quiz_internal)
  │    serve estáticos do Astro + responde /api/contador
  └─ quiz-redis (rede quiz_internal, nunca exposto)
```

- **Um único container de aplicação** (`quiz-app`), não dois: a superfície é
  pequena demais (estáticos + uma rota de API) para justificar separar
  web/api. Node serve os dois papéis.
- **Redis próprio** (`redis:alpine`) em vez de Upstash — self-hosted na
  própria VPS, sem serviço externo, sem custo variável. Fecha de vez a
  pendência antiga do contador (nunca chegou a ser configurado na Vercel).
- Isolamento total de outros projetos: nenhuma rede, volume ou variável
  compartilhada com `trendclima` ou `vps-gateway` além do necessário (Caddy
  alcançando `quiz-app` pela rede pública interna do Docker).

## Mudanças no repositório

- **Remove:** `site/api/contador.ts` e a dependência `@vercel/node`
  (específicos da Vercel).
- **Cria `site/server/index.mjs`:** servidor Node — `serve-handler` para os
  arquivos estáticos, cliente `redis` oficial para o contador. Contrato
  idêntico ao endpoint antigo: GET lê a contagem, POST incrementa; qualquer
  falha ao falar com o Redis retorna `{count:null}` (gracioso, nunca quebra
  o quiz — mesma filosofia do endpoint Vercel original).
- **Cria `site/Dockerfile`:** multi-stage — estágio de build roda
  `npm ci && npm run build` (Astro); imagem final carrega só `dist/`,
  `server/` e as dependências de produção.
- **Cria `infra/vps/`** na raiz do repositório: `compose.yml`,
  `.env.example`, `README.md` — mesmo padrão dos outros projetos na VPS
  (dois serviços: `quiz-app` e `quiz-redis`; `vps_public` externa e
  `quiz_internal` interna).
- **Sem mudança:** pipeline Python e os dados (`core.json`/`bonus.json`)
  continuam versionados como estão; chegam na VPS pelo próprio `git pull`.

## Sequência de corte

1. Na VPS: `git pull` do repositório em `~/voceestranho`, depois
   `docker compose build && up -d` dentro de `infra/vps/`.
2. Testar **antes** de tocar em DNS:
   `docker run --rm --network vps_public curlimages/curl curl http://quiz-app:3000/`
   — confirma o container respondendo sem depender do domínio.
3. Editar o Caddyfile central (`vps-gateway`), adicionar o bloco de site,
   recarregar o Caddy.
4. Trocar o DNS na Hostinger: registro `voceestranho` de
   **CNAME → cname.vercel-dns.com** para **A → 147.15.78.16**.
5. Aguardar propagação; o Caddy emite certificado Let's Encrypt sozinho
   assim que o DNS resolver para a VPS (mesmo fluxo já usado em
   `n8n.trendclima.com.br`). Janela curta de possível oscilação é esperada
   e aceitável.
6. Confirmar `https://voceestranho.anmaru.com/` no ar: quiz completo
   funcionando, contador incrementando de verdade (primeira vez que liga).
7. **Decomissionar a Vercel:** remover o projeto do dashboard, limpar
   `.vercel/` local (já ignorado no git), atualizar a seção "Pendências"
   do README raiz — os itens Upstash e Vercel Analytics deixam de existir
   nesse hosting.

## Fora de escopo

- Migração futura para VPS Hostinger — projeto separado.
- ESEB/bônus religião-política — independente do hosting, segue pendente
  do cadastro CESOP.
- Substituto para o Vercel Analytics — sai junto com a Vercel; se
  analytics de acesso for desejado depois, é uma feature nova a discutir,
  não decidida aqui (YAGNI).

## Testes

- Servidor Node (`site/server/index.mjs`): teste de que `GET /api/contador`
  retorna `{count:null}` quando o Redis está indisponível, e incrementa
  corretamente quando disponível (mock ou Redis efêmero em teste).
- Verificação manual pós-deploy: passo 2 e 6 da sequência de corte acima.
