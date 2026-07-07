import { useState } from "react";
import type { Core, Bonus as BonusDados, Resultado as R } from "../lib/tipos";
import { buscarBonus } from "../lib/lookup";

const DISCLAIMER = `As 8 perguntas principais vêm de uma única pesquisa \
(PNAD Contínua/IBGE), o que permite calcular sua combinação exata. Religião \
e política não existem na PNAD: usamos o ESEB 2022 (CESOP/UNICAMP, ~2 mil \
entrevistados) e estimamos a probabilidade condicionada ao seu perfil \
demográfico (região, sexo, idade, escolaridade). É uma aproximação honesta, \
não uma contagem exata — por isso o bônus é separado.`;

export default function Bonus({ core, indices }:
  { core: Core; indices: number[] }) {
  const [dados, setDados] = useState<BonusDados | null>(null);
  const [erro, setErro] = useState(false);
  const [aberto, setAberto] = useState(false);
  const [rel, setRel] = useState<number | null>(null);
  const [pol, setPol] = useState<number | null>(null);

  const abrir = () => {
    setAberto(true);
    if (!dados) {
      fetch("/data/bonus.json")
        .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
        .then(setDados)
        .catch(() => setErro(true));
    }
  };

  if (!aberto) {
    return (
      <button onClick={abrir}
        className="min-h-11 rounded-lg border border-tinta/40 px-6 py-3 hover:border-realce hover:bg-realce/20 transition">
        Bônus: e se contarmos religião e política?
      </button>
    );
  }
  if (erro) return <p>Não foi possível carregar o bônus.</p>;
  if (!dados) return <p>Carregando bônus…</p>;

  if (rel === null) {
    return <Escolha titulo="Qual sua religião?" opcoes={dados.meta.religiao}
      onEscolher={setRel} />;
  }
  if (pol === null) {
    return <Escolha titulo="Em política, como você se posiciona?"
      opcoes={dados.meta.politica} onEscolher={setPol} />;
  }

  const r: R = buscarBonus(core, dados, indices, rel, pol);
  return (
    <div className="space-y-4 text-center">
      {r.tipo === "exato" ? (
        <p className="text-2xl font-bold">
          Com religião e política: cerca de 1 em{" "}
          {r.umEmX.toLocaleString("pt-BR")} brasileiros adultos.
        </p>
      ) : (
        <p className="text-2xl font-bold">
          Combinação rara demais para estimar com segurança: menos de 1 em{" "}
          {r.limiteUmEm.toLocaleString("pt-BR")}.
        </p>
      )}
      <details className="text-sm text-tinta/60 text-left">
        <summary>Por que este número é uma estimativa?</summary>
        <p className="mt-2">{DISCLAIMER}</p>
      </details>
    </div>
  );
}

function Escolha({ titulo, opcoes, onEscolher }:
  { titulo: string; opcoes: string[]; onEscolher: (i: number) => void }) {
  return (
    <div className="space-y-3">
      <h3 className="text-xl font-bold text-tinta">{titulo}</h3>
      <div className="grid gap-2">
        {opcoes.map((o, i) => (
          <button key={i} onClick={() => onEscolher(i)}
            className="min-h-11 rounded-lg border border-tinta/25 px-4 py-3 text-left
                       hover:border-realce hover:bg-realce/20 transition">
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}
