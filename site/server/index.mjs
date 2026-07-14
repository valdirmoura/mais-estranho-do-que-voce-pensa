import http from "node:http";
import path from "node:path";
import { fileURLToPath } from "node:url";
import handler from "serve-handler";
import { createClient } from "redis";
import { lerOuIncrementar } from "./contador.mjs";
import { registrarEvento, lerEstatisticas } from "./eventos.mjs";

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
  const responderJson = (obj) => {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify(obj));
  };
  if (req.url === "/api/contador") {
    return responderJson(await lerOuIncrementar(clienteRedis, req.method));
  }
  if (req.method === "POST" && req.url === "/api/evento/visita") {
    return responderJson(await registrarEvento(clienteRedis, "visita"));
  }
  if (req.method === "POST" && req.url === "/api/evento/share") {
    return responderJson(await registrarEvento(clienteRedis, "share"));
  }
  if (req.method === "GET" && req.url === "/api/estatisticas") {
    return responderJson(await lerEstatisticas(clienteRedis));
  }
  await handler(req, res, { public: DIST_DIR });
});

servidor.listen(PORT, () => {
  console.log(
    `quiz-app ouvindo na porta ${PORT} (redis: ${clienteRedis ? "conectado" : "indisponível"})`,
  );
});
