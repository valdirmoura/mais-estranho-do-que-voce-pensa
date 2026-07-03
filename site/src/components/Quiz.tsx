import { useEffect, useRef, useState } from "react";
import type { Core } from "../lib/tipos";
import { buscar } from "../lib/lookup";
import { codificar, decodificar } from "../lib/share";
import Pergunta from "./Pergunta";
import Resultado from "./Resultado";

export default function Quiz() {
  const [core, setCore] = useState<Core | null>(null);
  const [erro, setErro] = useState(false);
  const [respostas, setRespostas] = useState<number[]>([]);
  const pingou = useRef(false);
  const veioDeUrl = useRef(false);
  const [contagem, setContagem] = useState<number | null>(null);

  useEffect(() => {
    fetch("/data/core.json")
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((c: Core) => {
        setCore(c);
        const r = new URLSearchParams(location.search).get("r");
        if (r) {
          const idx = decodificar(r, c.meta.dims);
          if (idx) {
            veioDeUrl.current = true;
            setRespostas(idx);
          }
        }
      })
      .catch(() => setErro(true));
  }, []);

  useEffect(() => {
    if (core && respostas.length === core.meta.dims.length && !pingou.current) {
      pingou.current = true;
      const metodo = veioDeUrl.current ? "GET" : "POST"; // GET só lê o total
      fetch("/api/contador", { method: metodo })
        .then((r) => r.json()).then((j) => setContagem(j.count))
        .catch(() => {});
    }
  }, [respostas, core]);

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
    <Resultado r={r} meta={core.meta} urlShare={urlShare} core={core}
      indices={respostas} contagem={contagem}
      aoRefazer={() => {
        setRespostas([]);
        pingou.current = false;
        veioDeUrl.current = false;
        setContagem(null);
        history.replaceState(null, "", location.pathname);
      }} />
  );
}
