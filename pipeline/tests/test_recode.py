import pytest
from quizbr import recode as r


def test_sexo():
    assert r.sexo(1) == 0  # homem
    assert r.sexo(2) == 1  # mulher
    assert r.sexo(9) is None


def test_faixa_etaria():
    assert r.faixa_etaria(18) == 0
    assert r.faixa_etaria(24) == 0
    assert r.faixa_etaria(25) == 1
    assert r.faixa_etaria(34) == 1
    assert r.faixa_etaria(44) == 2
    assert r.faixa_etaria(54) == 3
    assert r.faixa_etaria(64) == 4
    assert r.faixa_etaria(65) == 5
    assert r.faixa_etaria(99) == 5
    assert r.faixa_etaria(17) is None  # menor de idade


def test_regiao():
    assert r.regiao(11) == 0  # Rondônia -> Norte
    assert r.regiao(29) == 1  # Bahia -> Nordeste
    assert r.regiao(35) == 2  # São Paulo -> Sudeste
    assert r.regiao(43) == 3  # RS -> Sul
    assert r.regiao(53) == 4  # DF -> Centro-Oeste


def test_cor():
    assert r.cor(1) == 0  # branca
    assert r.cor(2) == 1  # preta
    assert r.cor(4) == 2  # parda
    assert r.cor(3) == 3  # amarela
    assert r.cor(5) == 4  # indígena
    assert r.cor(9) is None  # ignorado


def test_escolaridade():
    # VD3004: 1-2 -> 0; 3-4 -> 1; 5 -> 2; 6 -> 3; 7 -> 4
    assert r.escolaridade(1) == 0
    assert r.escolaridade(2) == 0
    assert r.escolaridade(3) == 1
    assert r.escolaridade(4) == 1
    assert r.escolaridade(5) == 2
    assert r.escolaridade(6) == 3
    assert r.escolaridade(7) == 4
    assert r.escolaridade(None) is None


def test_renda():
    sm = 1412.0
    assert r.renda(0.0, sm) == 0
    assert r.renda(0.5 * sm, sm) == 0
    assert r.renda(0.51 * sm, sm) == 1
    assert r.renda(1.0 * sm, sm) == 1
    assert r.renda(2.0 * sm, sm) == 2
    assert r.renda(5.0 * sm, sm) == 3
    assert r.renda(5.01 * sm, sm) == 4
    assert r.renda(None, sm) is None


def test_trabalho():
    # fora da força
    assert r.trabalho(vd4001=2, vd4002=None, vd4009=None) == 4
    # desocupado
    assert r.trabalho(vd4001=1, vd4002=2, vd4009=None) == 3
    # formal: VD4009 em {1,3,5,6}
    for v in (1, 3, 5, 6):
        assert r.trabalho(1, 1, v) == 0
    # informal: VD4009 em {2,4,9}
    for v in (2, 4, 9):
        assert r.trabalho(1, 1, v) == 1
    # conta própria/empregador: {7,8}
    for v in (7, 8):
        assert r.trabalho(1, 1, v) == 2


def test_internet():
    assert r.internet(1) == 0  # sim
    assert r.internet(2) == 1  # não
    assert r.internet(None) is None


def test_recodificar_linha_completa():
    linha = dict(V2007=2, V2009=30, UF=35, V2010=4, VD3004=5,
                 RDPC=1412.0, VD4001=1, VD4002=1, VD4009=1, INTERNET=1)
    assert r.recodificar_linha(linha, sm=1412.0) == (1, 1, 2, 2, 2, 1, 0, 0)


def test_recodificar_linha_invalida_vira_none():
    linha = dict(V2007=2, V2009=15, UF=35, V2010=4, VD3004=5,
                 RDPC=1412.0, VD4001=1, VD4002=1, VD4009=1, INTERNET=1)
    assert r.recodificar_linha(linha, sm=1412.0) is None
