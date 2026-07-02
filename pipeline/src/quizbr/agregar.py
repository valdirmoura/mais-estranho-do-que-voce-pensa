import json
import sys
from collections import defaultdict
import pandas as pd
from quizbr import config, leitor
from quizbr.recode import DIMENSOES, recodificar_linha


def agregar(df, peso_col, sm):
    cells = defaultdict(lambda: [0.0, 0])
    total_pop, total_n = 0.0, 0
    cols = [c for c in df.columns if c != peso_col]
    for reg in df.to_dict("records"):
        v = {k: (None if pd.isna(reg[k]) else reg[k]) for k in cols}
        idx = recodificar_linha(v, sm)
        if idx is None:
            continue
        peso = float(reg[peso_col])
        chave = "|".join(str(i) for i in idx)
        cells[chave][0] += peso
        cells[chave][1] += 1
        total_pop += peso
        total_n += 1
    return {
        "meta": {
            "fonte": f"PNAD Contínua {config.ANO} (IBGE)",
            "ano": config.ANO,
            "salario_minimo": sm,
            "total_pop": round(total_pop, 1),
            "total_n": total_n,
            "dims": [[nome, labels] for nome, labels in DIMENSOES],
        },
        "cells": {k: [round(p, 1), n] for k, (p, n) in cells.items()},
    }


def _rdpc_fallback(df):
    dom = ["UPA", "V1008", "V1014"]
    renda_dom = df.groupby(dom)["VD4020"].transform(
        lambda s: s.fillna(0).sum())
    return renda_dom / df["V2001"]


def _juntar_cores(a, b):
    """Combina dois cores (saída de agregar()) célula a célula, somando
    peso e n. meta é recomputada a partir das células combinadas."""
    cells = defaultdict(lambda: [0.0, 0])
    for k, (p, n) in a["cells"].items():
        cells[k][0] += p
        cells[k][1] += n
    for k, (p, n) in b["cells"].items():
        cells[k][0] += p
        cells[k][1] += n
    total_pop = round(sum(p for p, _ in cells.values()), 1)
    total_n = sum(n for _, n in cells.values())
    meta = dict(a["meta"])
    meta["total_pop"] = total_pop
    meta["total_n"] = total_n
    return {
        "meta": meta,
        "cells": {k: [round(p, 1), n] for k, (p, n) in cells.items()},
    }


def main():
    posicoes = leitor.parse_input_sas(
        (config.RAW / "input_pnad.txt").read_text(encoding="latin-1"))
    variaveis = config.VARIAVEIS_NUCLEO + [config.PESO, config.VAR_INTERNET]
    tem_rdpc = config.VAR_RDPC in posicoes
    if tem_rdpc:
        variaveis.append(config.VAR_RDPC)
    else:
        print(f"AVISO: {config.VAR_RDPC} ausente; usando fallback "
              "VD4020 somado por domicílio / V2001.")
        variaveis += ["VD4020", "V2001", "UPA", "V1008", "V1014"]
    txts = list((config.RAW / "pnad").glob("*.txt"))
    if len(txts) != 1:
        sys.exit(f"Esperava exatamente 1 .txt em raw/pnad, achei: {txts}")

    # Arquivo de microdados é grande (~1.5GB); processa em pedaços e acumula
    # células para não estourar memória com um read_fwf de arquivo inteiro.
    core = None
    n_pedacos = 0
    for pedaco in leitor.ler_microdados_em_pedacos(txts[0], posicoes, variaveis):
        pedaco["RDPC"] = (pedaco[config.VAR_RDPC] if tem_rdpc
                           else _rdpc_fallback(pedaco))
        pedaco["INTERNET"] = pedaco[config.VAR_INTERNET]
        parcial = agregar(pedaco, peso_col=config.PESO, sm=config.SALARIO_MINIMO)
        core = parcial if core is None else _juntar_cores(core, parcial)
        n_pedacos += 1
        print(f"  pedaço {n_pedacos}: +{parcial['meta']['total_n']} linhas "
              f"válidas (acumulado n={core['meta']['total_n']})")

    from quizbr.sanidade import checar_sanidade
    checar_sanidade(core)
    config.OUT.mkdir(parents=True, exist_ok=True)
    destino = config.OUT / "core.json"
    destino.write_text(json.dumps(core, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {destino} ({len(core['cells'])} células, "
          f"n={core['meta']['total_n']}, pop={core['meta']['total_pop']:,.0f})")


if __name__ == "__main__":
    main()
