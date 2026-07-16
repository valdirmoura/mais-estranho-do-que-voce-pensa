"""Bônus religião×política -> distribuições condicionais.

Fonte: CSES Módulo 6 (Comparative Study of Electoral Systems, Universidade
de Michigan). O componente brasileiro do Módulo 6 É o ESEB 2022 (mesmo
estudo, n=2001) — obtido sem cadastro em https://cses.org/data-download/,
ao contrário do .sav nativo do CESOP. As variáveis são harmonizadas pelo
CSES (nomes/códigos próprios, não os nativos do ESEB).

Consome pipeline/raw/cses6/cses6.sav (download documentado no README),
filtra o Brasil (F1004 == "BRA_2022") e produz pipeline/out/bonus.json com
as distribuições de religião × posicionamento político condicionadas em até
4 níveis de recuo (regiao|sexo|faixa3|escol3 -> regiao|escol3 -> escol3 ->
global)."""
import json
from collections import Counter, defaultdict
import pyreadstat
from quizbr import config

RELIGIOES = ["Católica", "Evangélica", "Outras religiões", "Sem religião"]
POLITICAS = ["Esquerda", "Centro", "Direita", "Não se posiciona"]

# Identificador do estudo brasileiro no arquivo integrado do CSES.
BRASIL = "BRA_2022"

# Variáveis do CSES Módulo 6 (codebook part2). Confirmadas contra as
# distribuições do ESEB (pipeline/raw/TF_04810.pdf): F2002 sexo (0=M,1=F),
# F2001_A idade em anos, F2003 escolaridade (ISCED harmonizado), F2011
# religião (códigos CSES), F2018 região (1=SE,2=NE,3=CO,4=N,5=S, mesma
# ordem do ESEB REG), F3020_R autoposição esquerda-direita 0-10.
MAPA_CSES = {"pais": "F1004", "sexo": "F2002", "idade": "F2001_A",
             "escolaridade": "F2003", "religiao": "F2011",
             "regiao": "F2018", "escala_lr": "F3020_R"}

# F2018 (região CSES) -> índice na ordem de região do núcleo
# (recode.py DIMENSOES: Norte0, Nordeste1, Sudeste2, Sul3, Centro-Oeste4).
MAPA_REGIAO = {1: 2, 2: 1, 3: 4, 4: 0, 5: 3}

# F2002 (gênero CSES) -> índice do núcleo (Homem0, Mulher1).
MAPA_SEXO = {0: 0, 1: 1}

# F2011 (religião CSES) -> índice em RELIGIOES. Códigos confirmados nos
# rótulos do .sav para o Brasil. Mórmons (1502, n=12) vão para "Outras"
# porque o CSES os separa dos protestantes/evangélicos e o Censo IBGE
# também os conta à parte.
MAPA_RELIGIAO = {
    1101: 0,                      # Católica romana
    1200: 1,                      # Protestante/evangélica (sem denominação)
    2000: 2, 4000: 2, 6400: 2,    # Judaica, Budista, Novas religiões
    7200: 2,                      # Espírita/Espiritismo
    7900: 2, 7901: 2,             # Etnorreligiões (umbanda/candomblé/outras)
    1502: 2, 9600: 2,             # Mórmons; Outra não especificada
    8200: 3, 8300: 3,             # Ateu; Nenhuma
    # 9997/9998 (recusou/não sabe) fora de propósito -> .get() retorna None
    # e o respondente é descartado (ver recodificar_religiao).
}

# F2003 (escolaridade CSES, escala ISCED) -> índice em escol5 (mesmos 5
# níveis do núcleo PNADC, ver recode.py). O ISCED harmonizado não distingue
# "superior incompleto" — sem impacto, porque es3() colapsa escol5 3 e 4 no
# mesmo grupo de conditioning do bônus.
MAPA_ESCOLARIDADE = {
    96: 0, 1: 0, 2: 0,   # Nenhuma; ISCED 0 (infantil); ISCED 1 (primário)
    3: 1,                # ISCED 2 (fundamental II)
    4: 2,               # ISCED 3 (médio)
    7: 4, 8: 4,          # ISCED 6 (bacharelado); ISCED 7 (mestrado+)
    # 97 (recusou) fora de propósito -> .get() retorna None e o respondente
    # é descartado (ver recodificar_escolaridade).
}


def fe3(faixa6):
    return [0, 0, 1, 1, 2, 2][faixa6]


def es3(escol5):
    return [0, 0, 1, 2, 2][escol5]


def politica_de_escala(v):
    if v is None or not (0 <= v <= 10):
        return 3
    if v <= 3:
        return 0
    if v <= 6:
        return 1
    return 2


def montar_niveis(respondentes, n_minimo=30):
    chaves = [
        lambda r: f"{r['regiao']}|{r['sexo']}|{r['f3']}|{r['e3']}",
        lambda r: f"{r['regiao']}|{r['e3']}",
        lambda r: f"{r['e3']}",
        lambda r: "",
    ]
    dist = {}
    for nivel, chave_fn in enumerate(chaves):
        grupos = defaultdict(Counter)
        tamanhos = Counter()
        for r in respondentes:
            k = chave_fn(r)
            grupos[k][f"{r['rel']}|{r['pol']}"] += 1
            tamanhos[k] += 1
        dist[str(nivel)] = {
            k: {rp: c / tamanhos[k] for rp, c in cnt.items()}
            for k, cnt in grupos.items()
            if tamanhos[k] >= (n_minimo if nivel < 3 else 1)
        }
    return dist


def _faixa6(idade):
    if idade is None or idade < 18:
        return None
    for i, teto in enumerate((24, 34, 44, 54, 64)):
        if idade <= teto:
            return i
    return 5


def recodificar_regiao(codigo):
    if codigo is None:
        return None
    return MAPA_REGIAO.get(int(codigo))


def recodificar_religiao(codigo):
    if codigo is None:
        return None
    return MAPA_RELIGIAO.get(int(codigo))


def recodificar_escolaridade(codigo):
    if codigo is None:
        return None
    return MAPA_ESCOLARIDADE.get(int(codigo))


def recodificar_respondente(linha):
    """Recodifica uma linha bruta do CSES (dict de coluna -> valor) para
    dict(regiao, sexo, f3, e3, rel, pol). Retorna None se algum campo
    obrigatório (regiao, sexo, faixa etária, escolaridade, religião) estiver
    ausente/NS-NR — política ausente vira 'não se posiciona' (índice 3), não
    descarta o respondente."""
    regiao_bruta = linha.get(MAPA_CSES["regiao"])
    sexo_bruto = linha.get(MAPA_CSES["sexo"])
    idade = linha.get(MAPA_CSES["idade"])
    escol_bruta = linha.get(MAPA_CSES["escolaridade"])
    religiao_bruta = linha.get(MAPA_CSES["religiao"])
    escala_bruta = linha.get(MAPA_CSES["escala_lr"])

    regiao = recodificar_regiao(regiao_bruta)
    sexo = MAPA_SEXO.get(int(sexo_bruto)) if sexo_bruto is not None else None
    faixa6 = _faixa6(idade)
    escol5 = recodificar_escolaridade(escol_bruta)
    rel = recodificar_religiao(religiao_bruta)
    pol = politica_de_escala(
        int(escala_bruta) if escala_bruta is not None else None)

    if None in (regiao, sexo, faixa6, escol5, rel):
        return None
    return dict(regiao=regiao, sexo=sexo, f3=fe3(faixa6), e3=es3(escol5),
                rel=rel, pol=pol)


def main():
    caminho = config.RAW / "cses6" / "cses6.sav"
    colunas = list(MAPA_CSES.values())
    df, meta = pyreadstat.read_sav(caminho, usecols=colunas)
    df = df[df[MAPA_CSES["pais"]] == BRASIL]

    respondentes = []
    for reg in df.to_dict("records"):
        linha = {k: (None if v != v else v) for k, v in reg.items()}  # NaN -> None
        r = recodificar_respondente(linha)
        if r is not None:
            respondentes.append(r)

    dist = montar_niveis(respondentes)
    saida = {
        "meta": {
            "fonte": "ESEB 2022 via CSES Módulo 6 (CSES, Universidade de Michigan)",
            "n": len(respondentes),
            "religiao": RELIGIOES,
            "politica": POLITICAS,
            "niveis": ["regiao|sexo|faixa3|escol3", "regiao|escol3",
                       "escol3", "global"],
        },
        "dist": dist,
    }
    config.OUT.mkdir(parents=True, exist_ok=True)
    destino = config.OUT / "bonus.json"
    destino.write_text(json.dumps(saida, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {destino} (n={len(respondentes)})")


if __name__ == "__main__":
    main()
