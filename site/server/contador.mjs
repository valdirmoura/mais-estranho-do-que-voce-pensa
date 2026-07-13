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
