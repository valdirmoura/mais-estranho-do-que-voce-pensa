from quizbr.bonus import fe3, es3, politica_de_escala, montar_niveis

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
