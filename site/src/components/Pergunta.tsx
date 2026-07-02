interface Props {
  titulo: string;
  opcoes: string[];
  onResponder: (i: number) => void;
  numero: number;
  total: number;
}

const TITULOS: Record<string, string> = {
  sexo: "Qual seu sexo?",
  faixa_etaria: "Qual sua idade?",
  regiao: "Em que região do Brasil você mora?",
  cor: "Qual sua cor ou raça (categorias do IBGE)?",
  escolaridade: "Até onde você estudou?",
  renda: "Qual a renda da sua casa, por pessoa?",
  trabalho: "Qual sua situação de trabalho?",
  internet: "Seu domicílio tem acesso à internet?",
};

export default function Pergunta({ titulo, opcoes, onResponder, numero, total }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-500">Pergunta {numero} de {total}</p>
      <h2 className="text-2xl font-bold">{TITULOS[titulo] ?? titulo}</h2>
      <div className="grid gap-2">
        {opcoes.map((o, i) => (
          <button key={i} onClick={() => onResponder(i)}
            className="rounded-xl border border-neutral-300 px-4 py-3 text-left
                       hover:border-emerald-600 hover:bg-emerald-50 transition">
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}
