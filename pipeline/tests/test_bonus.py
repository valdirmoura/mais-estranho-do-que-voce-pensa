from quizbr.bonus import (
    fe3, es3, politica_de_escala, montar_niveis,
    recodificar_escolaridade, recodificar_regiao, recodificar_respondente,
    MAPA_CSES
)

def test_grupos():
    assert [fe3(i) for i in range(6)] == [0, 0, 1, 1, 2, 2]
    assert [es3(i) for i in range(5)] == [0, 0, 1, 2, 2]

def test_politica():
    assert politica_de_escala(0) == 0
    assert politica_de_escala(3) == 0
    assert politica_de_escala(5) == 1
    assert politica_de_escala(7) == 2
    assert politica_de_escala(10) == 2
    assert politica_de_escala(None) == 3

def test_recuo_para_nivel_com_n_suficiente():
    # 40 respondentes idênticos: nível 0 tem n>=30, usa nível 0
    resp = [dict(regiao=2, sexo=1, f3=0, e3=1, rel=1, pol=2)] * 40
    dist = montar_niveis(resp, n_minimo=30)
    assert dist["0"]["2|1|0|1"]["1|2"] == 1.0
    # célula inexistente não aparece no nível 0
    assert "0|0|0|0" not in dist["0"]
    # nível global sempre existe
    assert dist["3"][""]["1|2"] == 1.0

def test_regiao_cses_para_ordem_do_nucleo():
    # F2018: 1=Sudeste, 2=Nordeste, 3=Centro-Oeste, 4=Norte, 5=Sul ->
    # ordem do núcleo (Norte0, Nordeste1, Sudeste2, Sul3, Centro-Oeste4).
    assert [recodificar_regiao(c) for c in (1, 2, 3, 4, 5)] == [2, 1, 4, 0, 3]
    assert recodificar_regiao(None) is None

def _linha_valida(**over):
    linha = {
        MAPA_CSES["regiao"]: 1,
        MAPA_CSES["sexo"]: 0,
        MAPA_CSES["idade"]: 30,
        MAPA_CSES["escolaridade"]: 4,   # ISCED 3 -> médio
        MAPA_CSES["religiao"]: 1101,    # Católica
        MAPA_CSES["escala_lr"]: 5,
    }
    linha.update(over)
    return linha

def test_escolaridade_unmapped_drops_respondent():
    # Código de escolaridade não mapeado (97 = recusou) retorna None,
    # respondente é descartado, não miscategorizado.
    assert recodificar_respondente(_linha_valida(**{MAPA_CSES["escolaridade"]: 97})) is None

def test_respondente_cses_valido():
    # idade 30 -> faixa6=1 -> fe3=0; ISCED 3 -> escol5=2 -> es3=1.
    r = recodificar_respondente(_linha_valida())
    assert r == dict(regiao=2, sexo=0, f3=0, e3=1, rel=0, pol=1)

def test_escala_lr_nao_posicionada_nao_descarta():
    # F3020_R = 98 (não sabe onde se colocar) -> política 3, sem descartar.
    r = recodificar_respondente(_linha_valida(**{MAPA_CSES["escala_lr"]: 98}))
    assert r is not None and r["pol"] == 3
