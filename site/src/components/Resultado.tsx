import type { Resultado as R, CoreMeta, Core } from "../lib/tipos";
import Bonus from "./Bonus";

const COMPARACOES: [number, string][] = [
  [1_000, "menos gente que um show de bairro"],
  [10_000, "cabe num ginásio pequeno"],
  [100_000, "menos que um Maracanã lotado"],
  [1_000_000, "menos que a população de Florianópolis"],
];

function comparar(pessoas: number): string {
  for (const [teto, frase] of COMPARACOES) if (pessoas < teto) return frase;
  return "ainda assim, uma fatia minúscula do Brasil";
}

export default function Resultado({ r, meta, urlShare, core, indices, contagem, aoRefazer }:
  { r: R; meta: CoreMeta; urlShare: string; core: Core; indices: number[];
    contagem: number | null; aoRefazer: () => void }) {
  const compartilhar = async () => {
    navigator.sendBeacon("/api/evento/share");
    const dados = { title: "Você é mais estranho do que pensa",
      text: "Descobri quão raro é meu perfil no Brasil. E o seu?", url: urlShare };
    if (navigator.share) await navigator.share(dados);
    else { await navigator.clipboard.writeText(urlShare); alert("Link copiado!"); }
  };
  return (
    <div className="space-y-6 text-center">
      {r.tipo === "exato" ? (
        <>
          <p className="text-lg">Sua combinação exata aparece em</p>
          <p className="text-6xl font-extrabold text-destaque">
            1 em {r.umEmX.toLocaleString("pt-BR")}
          </p>
          <p className="text-lg">
            brasileiros adultos — cerca de {r.pessoas.toLocaleString("pt-BR")} pessoas.
            <br /><span className="text-tinta/60">({comparar(r.pessoas)})</span>
          </p>
          <details className="text-sm text-tinta/60">
            <summary>Como esse número foi calculado?</summary>
            <p className="mt-2 text-left">
              Fonte: {meta.fonte}, amostra de {meta.total_n.toLocaleString("pt-BR")}{" "}
              pessoas com pesos que projetam a população adulta
              ({Math.round(meta.total_pop / 1e6)} milhões). Sua combinação teve{" "}
              {r.nAmostral.toLocaleString("pt-BR")} respondentes na amostra.
              Nenhuma resposta sua saiu do seu aparelho.
            </p>
          </details>
        </>
      ) : (
        <>
          <p className="text-lg">Sua combinação é tão rara que</p>
          <p className="text-4xl font-extrabold text-destaque">
            não apareceu nem uma vez
          </p>
          <p className="text-lg">
            entre {r.limiteUmEm.toLocaleString("pt-BR")} entrevistados do IBGE.
            Estimativa honesta: menos de 1 em {r.limiteUmEm.toLocaleString("pt-BR")}.
          </p>
        </>
      )}
      <div className="flex justify-center gap-3">
        <button onClick={compartilhar}
          className="min-h-11 rounded-lg bg-tinta px-6 py-3 font-bold text-fundo">
          Compartilhar meu resultado
        </button>
        <button onClick={aoRefazer}
          className="min-h-11 rounded-lg border border-tinta/40 px-6 py-3">
          Refazer
        </button>
      </div>
      {contagem !== null && (
        <p className="text-sm text-tinta/60">
          {contagem.toLocaleString("pt-BR")} pessoas já fizeram o quiz
        </p>
      )}
      <div className="pt-4">
        <Bonus core={core} indices={indices} />
      </div>
    </div>
  );
}
