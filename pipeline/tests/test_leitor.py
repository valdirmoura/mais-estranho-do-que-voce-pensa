import pytest
from quizbr import leitor

INPUT_SAS = """
/* dicionário de exemplo */
@0001 Ano $4.
@0005 UF 2.
@0007 V2007 1.
@0008 V2009 3.
"""

# Ano=2024, UF=35, V2007=2, V2009=030  -> largura total 10
LINHA = "2024352030"


def test_parse_input_sas():
    pos = leitor.parse_input_sas(INPUT_SAS)
    assert pos["Ano"] == (0, 4)
    assert pos["UF"] == (4, 6)
    assert pos["V2007"] == (6, 7)
    assert pos["V2009"] == (7, 10)


def test_ler_microdados(tmp_path):
    txt = tmp_path / "dados.txt"
    txt.write_text(LINHA + "\n" + LINHA + "\n", encoding="utf-8")
    pos = leitor.parse_input_sas(INPUT_SAS)
    df = leitor.ler_microdados(txt, pos, ["UF", "V2009"])
    assert list(df.columns) == ["UF", "V2009"]
    assert df["UF"].tolist() == [35, 35]
    assert df["V2009"].tolist() == [30, 30]


def test_validar_variaveis_falha_ruidosa():
    pos = {"V2007": (0, 1), "S01029A": (1, 2)}
    with pytest.raises(ValueError) as exc:
        leitor.validar_variaveis(pos, ["V2007", "S01029"])
    assert "S01029" in str(exc.value)
    assert "S01029A" in str(exc.value)  # candidata sugerida
