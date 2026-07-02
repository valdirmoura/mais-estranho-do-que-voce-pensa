import pandas as pd
from quizbr.agregar import agregar

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
