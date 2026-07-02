import { useEffect, useState } from "react";
import type { Core } from "../lib/tipos";
import { buscar } from "../lib/lookup";
import { codificar, decodificar } from "../lib/share";
import Pergunta from "./Pergunta";
import Resultado from "./Resultado";

export default function Quiz() {
  const [core, setCore] = useState<Core | null>(null);
  const [erro, setErro] = useState(false);
  const [respostas, setRespostas] = useState<number[]>([]);

  useEffect(() => {
    fetch("/data/core.json")
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((c: Core) => {
        setCore(c);
        const r = new URLSearchParams(location.search).get("r");
        if (r) {
          const idx = decodificar(r, c.meta.dims);
          if (idx) setRespostas(idx);
        }
      })
      .catch(() => setErro(true));
  }, []);

  if (erro) return <p>Não foi possível carregar os dados. Recarregue a página.</p>;
  if (!core) return <p>Carregando…</p>;

  const dims = core.meta.dims;
  if (respostas.length < dims.length) {
    const i = respostas.length;
    return (
      <Pergunta titulo={dims[i][0]} opcoes={dims[i][1]}
        numero={i + 1} total={dims.length}
        onResponder={(op) => setRespostas([...respostas, op])} />
    );
  }

  const r = buscar(core, respostas);
  const urlShare = `${location.origin}${location.pathname}?r=${codificar(respostas)}`;
  return (
    <Resultado r={r} meta={core.meta} urlShare={urlShare}
      aoRefazer={() => { setRespostas([]); history.replaceState(null, "", location.pathname); }} />
  );
}
