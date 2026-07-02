"""Recodificação PNAD Contínua -> categorias do quiz. Índices são posicionais
na ordem fixa de DIMENSOES; a chave de célula depende dessa ordem."""

DIMENSOES = [
    ("sexo", ["Homem", "Mulher"]),
    ("faixa_etaria", ["18–24", "25–34", "35–44", "45–54", "55–64", "65+"]),
    ("regiao", ["Norte", "Nordeste", "Sudeste", "Sul", "Centro-Oeste"]),
    ("cor", ["Branca", "Preta", "Parda", "Amarela", "Indígena"]),
    ("escolaridade", [
        "Sem instrução / fundamental incompleto",
        "Fundamental completo / médio incompleto",
        "Médio completo",
        "Superior incompleto",
        "Superior completo",
    ]),
    ("renda", [
        "Até ½ salário mínimo por pessoa",
        "½ a 1 SM", "1 a 2 SM", "2 a 5 SM", "Mais de 5 SM",
    ]),
    ("trabalho", [
        "Empregado formal", "Empregado informal",
        "Conta própria / empregador", "Desempregado", "Fora da força de trabalho",
    ]),
    ("internet", ["Usa internet", "Não usa internet"]),
]


def sexo(v2007):
    return {1: 0, 2: 1}.get(v2007)


def faixa_etaria(v2009):
    if v2009 is None or v2009 < 18:
        return None
    for i, teto in enumerate((24, 34, 44, 54, 64)):
        if v2009 <= teto:
            return i
    return 5


def regiao(uf):
    if uf is None:
        return None
    return {1: 0, 2: 1, 3: 2, 4: 3, 5: 4}.get(uf // 10)


def cor(v2010):
    return {1: 0, 2: 1, 4: 2, 3: 3, 5: 4}.get(v2010)


def escolaridade(vd3004):
    return {1: 0, 2: 0, 3: 1, 4: 1, 5: 2, 6: 3, 7: 4}.get(vd3004)


def renda(rdpc, sm):
    if rdpc is None:
        return None
    x = rdpc / sm
    if x <= 0.5:
        return 0
    if x <= 1:
        return 1
    if x <= 2:
        return 2
    if x <= 5:
        return 3
    return 4


def trabalho(vd4001, vd4002, vd4009):
    if vd4001 == 2:
        return 4
    if vd4002 == 2:
        return 3
    if vd4009 in (1, 3, 5, 6):
        return 0
    if vd4009 in (2, 4, 9):
        return 1
    if vd4009 in (7, 8):
        return 2
    return None


def internet(v):
    return {1: 0, 2: 1}.get(v)


def recodificar_linha(v, sm):
    indices = (
        sexo(v.get("V2007")),
        faixa_etaria(v.get("V2009")),
        regiao(v.get("UF")),
        cor(v.get("V2010")),
        escolaridade(v.get("VD3004")),
        renda(v.get("RDPC"), sm),
        trabalho(v.get("VD4001"), v.get("VD4002"), v.get("VD4009")),
        internet(v.get("INTERNET")),
    )
    if any(i is None for i in indices):
        return None
    return indices
