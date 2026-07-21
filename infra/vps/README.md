# Deploy — voceestranho (VPS Oracle)

Pré-requisito: a VPS já roda a base `vps-gateway` (Caddy) com a rede
externa `vps_public` criada (ver `~/vps-gateway`).

## Primeira vez

```bash
git clone https://github.com/valdirmoura/voce-estranho.git ~/voceestranho
cd ~/voceestranho/infra/vps
cp .env.example .env
docker compose --env-file .env -f compose.yml up -d --build
```

## Atualizações seguintes

```bash
cd ~/voceestranho
git pull
cd infra/vps
docker compose --env-file .env -f compose.yml up -d --build
```

## Verificação

```bash
docker compose --env-file .env -f compose.yml ps
docker run --rm --network vps_public curlimages/curl curl -s http://quiz-app:3000/
docker run --rm --network vps_public curlimages/curl curl -s -X POST http://quiz-app:3000/api/contador
```

## Ligar ao Caddy central

Adicionar ao final de `~/vps-gateway/infra/vps/Caddyfile` (nunca editar
blocos existentes de outros projetos):

```
voceestranho.anmaru.com {
  encode gzip
  reverse_proxy quiz-app:3000
}
```

Depois:

```bash
cd ~/vps-gateway/infra/vps
docker compose --env-file .env -f compose.yml exec caddy caddy validate --config /etc/caddy/Caddyfile
docker compose --env-file .env -f compose.yml restart caddy
```

O certificado HTTPS só é emitido depois que o registro DNS de
`voceestranho.anmaru.com` apontar (tipo A) para o IP público da VPS.

## Monitoramento

- **Uptime:** monitor HTTP(s) no UptimeRobot para
  `https://voceestranho.anmaru.com/`, checagem a cada 5 min, alerta por
  e-mail.
- **Healthcheck interno:** o `quiz-app` tem healthcheck no compose
  (`wget` em `/api/contador` a cada 30s); `restart: unless-stopped`
  religa os containers em caso de crash ou reboot da VPS.
- **Estatísticas anônimas:** `curl -s https://voceestranho.anmaru.com/api/estatisticas`
  → `{"visitas":n,"shares":n,"conclusoes":n}` (contadores no Redis, sem
  nenhum dado pessoal).

## Persistência do contador (Redis)

O Redis roda com AOF (`--appendonly yes`) e volume `quiz_redis_data`.
Atenção: com AOF ligado, o Redis ignora o `dump.rdb` no boot e carrega só
o `appendonlydir/` — foi o que zerou o contador na ativação do AOF em
2026-07-14 (valor restaurado manualmente com
`docker exec quiz-redis redis-cli set quiz:conclusoes 5`). Com o AOF já
ativo, restarts e rebuilds preservam os dados normalmente.
