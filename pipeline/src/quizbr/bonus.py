"""Bônus ESEB 2022 -> distribuições condicionais religião×política.

Consome pipeline/raw/eseb2022.sav (download manual documentado no README —
CESOP/UNICAMP) e produz pipeline/out/bonus.json com as distribuições de
religião × posicionamento político condicionadas em até 4 níveis de recuo
(regiao|sexo|faixa3|escol3 -> regiao|escol3 -> escol3 -> global)."""
import json
from collections import Counter, defaultdict
import pyreadstat
from quizbr import config

RELIGIOES = ["Católica", "Evangélica", "Outras religiões", "Sem religião"]
POLITICAS = ["Esquerda", "Centro", "Direita", "Não se posiciona"]

# Nomes confirmados contra o codebook ESEB 2022 (tabela de frequências
# CESOP/QUAEST 04810, pipeline/raw/TF_04810.pdf): UF p.2 (código IBGE de 2
# dígitos), D02 p.6, D01A_IDADE p.7-11 (anos completos), D03 p.12, Q19
# (autoposicionamento 0-10) e D10 p.168. A validação abaixo falha
# ruidosamente listando colunas candidatas se algum nome não bater no .sav.
MAPA_ESEB = {"religiao": "D10", "escala_lr": "Q19",
             "uf": "UF", "sexo": "D02", "idade": "D01A_IDADE",
             "escolaridade": "D03"}

# D10 -> índice em RELIGIOES. Códigos confirmados no TF_04810.pdf p.168.
# Código 7 (Mórmon/Adventista/Testemunha de Jeová) vai para Evangélica
# porque a Adventista domina a categoria no Brasil e o Censo IBGE a
# classifica como evangélica de missão; 100 (acredita em Deus, sem
# religião declarada) segue o critério do Censo para "sem religião".
MAPA_RELIGIAO = {
    3: 0,                     # Católica
    5: 1, 7: 1,               # Evangélica; Mórmon/Adventista/TJ
    1: 2,                     # Budista
    2: 2, 10: 2,              # Candomblé, Umbanda
    4: 2,                     # Espírita Kardecista/Espiritualista
    6: 2,                     # Judaica
    9: 2,                     # Seicho-No-Ie/Messiânica/Perfeita Liberdade
    101: 2, 102: 2,           # Pagão; "Cristão" genérico (sem denominação)
    96: 3, 97: 3, 100: 3,     # Ateu/agnóstico; Não tem religião; Acredita em Deus
    # 98 (Não respondeu) e 99 (Não sabe) fora de propósito -> .get() retorna
    # None e o respondente é descartado (ver recodificar_religiao).
}

# D03 -> índice em escol5 (mesmos 5 níveis do núcleo PNADC, ver recode.py).
# Códigos confirmados no TF_04810.pdf p.12: 1 analfabeto, 2 primário
# incompleto, 3 primário completo, 4 ginásio incompleto, 5 ginásio completo,
# 6 colegial incompleto, 7 colegial completo, 8 universitário incompleto/
# técnico, 9 universitário completo, 10 pós-graduação.
MAPA_ESCOLARIDADE = {
    1: 0, 2: 0, 3: 0, 4: 0,  # até fundamental incompleto
    5: 1, 6: 1,              # fundamental completo / médio incompleto
    7: 2,                    # médio completo
    8: 3,                    # superior incompleto (ou técnico pós-médio)
    9: 4, 10: 4,             # superior completo / pós-graduação
    # 99 (Não respondeu) fora de propósito -> .get() retorna None e o
    # respondente é descartado (ver recodificar_escolaridade).
}

# Substrings usadas para sugerir colunas candidatas quando um nome do
# MAPA_ESEB não bate com o .sav (religião, escolaridade, sexo, idade, UF,
# escala esquerda-direita).
_PISTAS_COLUNAS = {
    "religiao": "reli",
    "escolaridade": "esc",
    "sexo": "sexo",
    "idade": "idade",
    "uf": "uf",
    "escala_lr": "esquerda",
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


def validar_mapa_eseb(colunas):
    faltantes = [campo for campo, col in MAPA_ESEB.items() if col not in colunas]
    if faltantes:
        candidatas = {
            campo: [c for c in colunas
                    if _PISTAS_COLUNAS.get(campo, campo).lower() in c.lower()]
            for campo in faltantes
        }
        raise ValueError(
            f"MAPA_ESEB aponta para colunas ausentes no .sav: "
            f"{[MAPA_ESEB[c] for c in faltantes]} (campos: {faltantes}). "
            f"Colunas candidatas por substring: {candidatas}. "
            "Confira o codebook do ESEB 2022 (CESOP) e ajuste MAPA_ESEB."
        )


def _faixa6(idade):
    if idade is None or idade < 18:
        return None
    for i, teto in enumerate((24, 34, 44, 54, 64)):
        if idade <= teto:
            return i
    return 5


def _regiao(uf):
    if uf is None:
        return None
    return {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}.get(int(uf) // 10)


def recodificar_religiao(codigo):
    if codigo is None:
        return None
    return MAPA_RELIGIAO.get(int(codigo))


def recodificar_escolaridade(codigo):
    if codigo is None:
        return None
    return MAPA_ESCOLARIDADE.get(int(codigo))


def recodificar_respondente(linha):
    """Recodifica uma linha bruta do .sav (dict de coluna -> valor) para
    dict(regiao, sexo, f3, e3, rel, pol). Retorna None se algum campo
    obrigatório (regiao, sexo, faixa etária, escolaridade, religião) estiver
    ausente/NS-NR — política ausente vira 'não se posiciona' (índice 3), não
    descarta o respondente."""
    uf = linha.get(MAPA_ESEB["uf"])
    sexo_bruto = linha.get(MAPA_ESEB["sexo"])
    idade = linha.get(MAPA_ESEB["idade"])
    escol_bruta = linha.get(MAPA_ESEB["escolaridade"])
    religiao_bruta = linha.get(MAPA_ESEB["religiao"])
    escala_bruta = linha.get(MAPA_ESEB["escala_lr"])

    regiao = _regiao(uf)
    sexo = {1: 0, 2: 1}.get(int(sexo_bruto)) if sexo_bruto is not None else None
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
    caminho = config.RAW / "eseb2022.sav"
    df, meta = pyreadstat.read_sav(caminho)
    validar_mapa_eseb(set(df.columns))

    respondentes = []
    for reg in df.to_dict("records"):
        linha = {k: (None if v != v else v) for k, v in reg.items()}  # NaN -> None
        r = recodificar_respondente(linha)
        if r is not None:
            respondentes.append(r)

    dist = montar_niveis(respondentes)
    saida = {
        "meta": {
            "fonte": "ESEB 2022 (CESOP/UNICAMP)",
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
