import json
import sys
from collections import defaultdict
import pandas as pd
from quizbr import config, leitor
from quizbr.recode import DIMENSOES, recodificar_linha


def agregar(df, peso_col, sm, arredondar=True):
    """Agrega df em células por dimensão, somando peso e contando n.

    Por padrão (arredondar=True) os pesos/total_pop retornados já vêm
    arredondados para 1 casa decimal — comportamento público estável usado
    pelos testes e por chamadas avulsas. Internamente (ex.: pipeline em
    pedaços, ver main()) usa-se arredondar=False para acumular valores RAW
    e só arredondar uma única vez, no momento da serialização final —
    evitando drift de arredondamento composto ao longo de vários pedaços.
    """
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
    meta = {
        "fonte": f"PNAD Contínua {config.ANO} (IBGE)",
        "ano": config.ANO,
        "salario_minimo": sm,
        "total_pop": round(total_pop, 1) if arredondar else total_pop,
        "total_n": total_n,
        "dims": [[nome, labels] for nome, labels in DIMENSOES],
    }
    if arredondar:
        cells_out = {k: [round(p, 1), n] for k, (p, n) in cells.items()}
    else:
        cells_out = {k: [p, n] for k, (p, n) in cells.items()}
    return {"meta": meta, "cells": cells_out}


def _arredondar_core(core):
    """Aplica o arredondamento final (1 casa decimal) a um core com pesos
    RAW — usado uma única vez, no ponto de serialização."""
    meta = dict(core["meta"])
    meta["total_pop"] = round(meta["total_pop"], 1)
    return {
        "meta": meta,
        "cells": {k: [round(p, 1), n] for k, (p, n) in core["cells"].items()},
    }


def _rdpc_fallback(df):
    dom = ["UPA", "V1008", "V1014"]
    renda_dom = df.groupby(dom)["VD4020"].transform(
        lambda s: s.fillna(0).sum())
    return renda_dom / df["V2001"]


def _juntar_cores(a, b):
    """Combina dois cores (saída de agregar(..., arredondar=False)) célula a
    célula, somando peso RAW e n. meta é recomputada a partir das células
    combinadas. Não arredonda — os cores de entrada e o resultado devem
    conter pesos RAW; o arredondamento acontece uma única vez, no momento
    da serialização final (ver _arredondar_core / main())."""
    cells = defaultdict(lambda: [0.0, 0])
    for k, (p, n) in a["cells"].items():
        cells[k][0] += p
        cells[k][1] += n
    for k, (p, n) in b["cells"].items():
        cells[k][0] += p
        cells[k][1] += n
    total_pop = sum(p for p, _ in cells.values())
    total_n = sum(n for _, n in cells.values())
    meta = dict(a["meta"])
    meta["total_pop"] = total_pop
    meta["total_n"] = total_n
    return {
        "meta": meta,
        "cells": {k: [p, n] for k, (p, n) in cells.items()},
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
        parcial = agregar(pedaco, peso_col=config.PESO, sm=config.SALARIO_MINIMO,
                           arredondar=False)
        core = parcial if core is None else _juntar_cores(core, parcial)
        n_pedacos += 1
        print(f"  pedaço {n_pedacos}: +{parcial['meta']['total_n']} linhas "
              f"válidas (acumulado n={core['meta']['total_n']})")

    # Arredonda uma única vez, aqui, no ponto de serialização — os pedaços
    # acumulados acima carregam pesos RAW (sem arredondamento) para evitar
    # drift composto ao longo de vários pedaços.
    core = _arredondar_core(core)

    from quizbr.sanidade import checar_sanidade
    checar_sanidade(core)
    config.OUT.mkdir(parents=True, exist_ok=True)
    destino = config.OUT / "core.json"
    destino.write_text(json.dumps(core, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {destino} ({len(core['cells'])} células, "
          f"n={core['meta']['total_n']}, pop={core['meta']['total_pop']:,.0f})")


if __name__ == "__main__":
    main()
