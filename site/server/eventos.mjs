const CHAVES_EVENTO = { visita: "quiz:visitas", share: "quiz:shares" };
const CHAVES_ESTATISTICAS = ["quiz:visitas", "quiz:shares", "quiz:conclusoes"];

export async function registrarEvento(clienteRedis, tipo) {
  const chave = CHAVES_EVENTO[tipo];
  if (!clienteRedis || !chave) return { ok: false };
  try {
    await clienteRedis.incr(chave);
    return { ok: true };
  } catch {
    return { ok: false };
  }
}

export async function lerEstatisticas(clienteRedis) {
  if (!clienteRedis) return { visitas: null, shares: null, conclusoes: null };
  try {
    const [visitas, shares, conclusoes] =
      await clienteRedis.mGet(CHAVES_ESTATISTICAS);
    const numero = (v) => (v === null ? 0 : Number(v));
    return {
      visitas: numero(visitas),
      shares: numero(shares),
      conclusoes: numero(conclusoes),
    };
  } catch {
    return { visitas: null, shares: null, conclusoes: null };
  }
}
