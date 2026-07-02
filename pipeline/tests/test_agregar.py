import pandas as pd
from quizbr.agregar import agregar, _juntar_cores, _arredondar_core

def _df(linhas):
    return pd.DataFrame(linhas)

BASE = dict(V2007=2, V2009=30, UF=35, V2010=4, VD3004=5,
            RDPC=1412.0, VD4001=1, VD4002=1, VD4009=1, INTERNET=1)

def test_agrega_pesos_e_n():
    df = _df([{**BASE, "PESO": 100.0}, {**BASE, "PESO": 50.0},
              {**BASE, "V2007": 1, "PESO": 30.0}])
    core = agregar(df, peso_col="PESO", sm=1412.0)
    assert core["cells"]["1|1|2|2|2|1|0|0"] == [150.0, 2]
    assert core["cells"]["0|1|2|2|2|1|0|0"] == [30.0, 1]
    assert core["meta"]["total_pop"] == 180.0
    assert core["meta"]["total_n"] == 3

def test_linha_invalida_excluida():
    df = _df([{**BASE, "PESO": 100.0}, {**BASE, "V2009": 15, "PESO": 999.0}])
    core = agregar(df, peso_col="PESO", sm=1412.0)
    assert core["meta"]["total_n"] == 1
    assert core["meta"]["total_pop"] == 100.0


def _core_raw(chave, peso, n, total_pop, total_n):
    return {
        "meta": {
            "fonte": "PNAD Contínua 2025 (IBGE)",
            "ano": 2025,
            "salario_minimo": 1412.0,
            "total_pop": total_pop,
            "total_n": total_n,
            "dims": [],
        },
        "cells": {chave: [peso, n]},
    }


def test_juntar_cores_soma_raw_sem_arredondar_prematuramente():
    # Pesos escolhidos para trair arredondamento prematuro: 0.04 + 0.04
    # arredondados individualmente para 1 casa viram 0.0 + 0.0 = 0.0, mas a
    # soma RAW correta é 0.08 -> arredonda para 0.1. _juntar_cores deve
    # operar sobre RAW e não arredondar internamente.
    a = _core_raw("1|1|2|2|2|1|0|0", 0.04, 1, 0.04, 1)
    b = _core_raw("1|1|2|2|2|1|0|0", 0.04, 1, 0.04, 1)
    juntado = _juntar_cores(a, b)

    # Sem arredondamento intermediário: valores RAW exatos preservados.
    assert juntado["cells"]["1|1|2|2|2|1|0|0"] == [0.08, 2]
    assert juntado["meta"]["total_pop"] == 0.08
    assert juntado["meta"]["total_n"] == 2

    # Só ao serializar (arredondamento final) o drift desapareceria: 0.1,
    # não 0.0 (que seria o resultado de arredondar cada parcial antes).
    final = _arredondar_core(juntado)
    assert final["cells"]["1|1|2|2|2|1|0|0"] == [0.1, 2]
    assert final["meta"]["total_pop"] == 0.1


def test_juntar_cores_chave_sobreposta_soma_peso_e_n():
    a = _core_raw("1|1|2|2|2|1|0|0", 150.25, 2, 150.25, 2)
    b = _core_raw("1|1|2|2|2|1|0|0", 29.85, 1, 29.85, 1)
    juntado = _juntar_cores(a, b)

    assert juntado["cells"]["1|1|2|2|2|1|0|0"] == [180.10, 3]
    assert juntado["meta"]["total_pop"] == 180.10
    assert juntado["meta"]["total_n"] == 3

    final = _arredondar_core(juntado)
    assert final["cells"]["1|1|2|2|2|1|0|0"] == [180.1, 3]
    assert final["meta"]["total_pop"] == 180.1
