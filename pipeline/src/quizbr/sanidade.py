from quizbr import config
from quizbr.recode import DIMENSOES

# Faixas amplas de participação esperada por categoria (fração da população
# adulta). Conferidas contra tabelas públicas do IBGE; propositalmente largas —
# pegam catástrofe de parsing, não flutuação amostral.
MARGENS_ESPERADAS = {
    "sexo": [(0.44, 0.52), (0.48, 0.56)],
    "regiao": [(0.05, 0.12), (0.22, 0.32), (0.38, 0.48),
               (0.11, 0.18), (0.06, 0.11)],
    "internet": [(0.75, 0.97), (0.03, 0.25)],
}


def _margem(core, dim_nome):
    nomes = [n for n, _ in DIMENSOES]
    d = nomes.index(dim_nome)
    tam = len(DIMENSOES[d][1])
    somas = [0.0] * tam
    for chave, (peso, _n) in core["cells"].items():
        somas[int(chave.split("|")[d])] += peso
    total = core["meta"]["total_pop"]
    return [s / total for s in somas]


def checar_sanidade(core, checar_margens=None):
    total = core["meta"]["total_pop"]
    lo, hi = config.POPULACAO_ADULTA_ESPERADA
    assert lo <= total <= hi, (
        f"população adulta ponderada = {total:,.0f}, fora de [{lo:,}–{hi:,}]. "
        "Peso errado ou filtro de idade quebrado?")
    for peso, n in core["cells"].values():
        assert peso > 0 and n > 0, "célula com peso/n não positivo"
    dims = (MARGENS_ESPERADAS.keys() if checar_margens is None
            else checar_margens)
    if checar_margens is False:
        dims = []
    for nome in dims:
        obtido = _margem(core, nome)
        for i, (mn, mx) in enumerate(MARGENS_ESPERADAS[nome]):
            assert mn <= obtido[i] <= mx, (
                f"margem de {nome}[{i}] = {obtido[i]:.3f}, "
                f"esperado [{mn}–{mx}]. Recodificação ou layout errados?")
