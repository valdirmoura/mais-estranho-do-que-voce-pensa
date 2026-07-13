# Deploy — voceestranho (VPS Oracle)

Pré-requisito: a VPS já roda a base `vps-gateway` (Caddy) com a rede
externa `vps_public` criada (ver `~/vps-gateway`).

## Primeira vez

```bash
git clone https://github.com/valdirmoura/mais-estranho-do-que-voce-pensa.git ~/voceestranho
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
