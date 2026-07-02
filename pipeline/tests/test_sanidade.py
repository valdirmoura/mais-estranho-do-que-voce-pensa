import pytest
from quizbr.sanidade import checar_sanidade, MARGENS_ESPERADAS

def _core_ok():
    # 52% mulheres etc. — construir dict mínimo consistente com as faixas
    cells = {"0|1|2|2|2|1|0|0": [76_800_000.0, 100_000],
             "1|1|2|2|2|1|0|0": [83_200_000.0, 110_000]}
    return {"meta": {"total_pop": 160_000_000.0, "total_n": 210_000},
            "cells": cells}

def test_total_fora_da_faixa_estoura():
    core = _core_ok()
    core["meta"]["total_pop"] = 10_000.0
    with pytest.raises(AssertionError, match="população"):
        checar_sanidade(core, checar_margens=False)

def test_margem_sexo():
    core = _core_ok()
    checar_sanidade(core, checar_margens=["sexo"])  # 52% mulheres: dentro
    core["cells"]["1|1|2|2|2|1|0|0"][0] = 1.0       # quase 0% mulheres
    with pytest.raises(AssertionError, match="sexo"):
        checar_sanidade(core, checar_margens=["sexo"])
