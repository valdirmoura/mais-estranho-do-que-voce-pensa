import re
import pandas as pd

_PADRAO = re.compile(r"@(\d+)\s+(\w+)\s+\$?(\d+)\.")


def parse_input_sas(texto):
    pos = {}
    for m in _PADRAO.finditer(texto):
        inicio = int(m.group(1)) - 1
        pos[m.group(2)] = (inicio, inicio + int(m.group(3)))
    return pos


def validar_variaveis(posicoes, obrigatorias):
    faltantes = [v for v in obrigatorias if v not in posicoes]
    if faltantes:
        sugestoes = {
            f: [k for k in posicoes if f[:4] in k or k in f]
            for f in faltantes
        }
        raise ValueError(
            f"Variáveis ausentes no dicionário: {faltantes}. "
            f"Candidatas parecidas: {sugestoes}. "
            "Confira o input SAS do IBGE — o layout pode ter mudado."
        )


def ler_microdados(caminho_txt, posicoes, variaveis):
    validar_variaveis(posicoes, variaveis)
    colspecs = [posicoes[v] for v in variaveis]
    df = pd.read_fwf(caminho_txt, colspecs=colspecs, names=variaveis,
                     header=None, dtype=str)
    for c in variaveis:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    return df


def ler_microdados_em_pedacos(caminho_txt, posicoes, variaveis,
                               chunksize=200_000):
    """Como ler_microdados, mas em pedaços (generator de DataFrames) para
    não carregar arquivos de microdados muito grandes (~1.5GB+) de uma vez
    na memória. Mesma validação e mesma conversão numérica por coluna."""
    validar_variaveis(posicoes, variaveis)
    colspecs = [posicoes[v] for v in variaveis]
    for pedaco in pd.read_fwf(caminho_txt, colspecs=colspecs, names=variaveis,
                               header=None, dtype=str, chunksize=chunksize):
        for c in variaveis:
            pedaco[c] = pd.to_numeric(pedaco[c], errors="coerce")
        yield pedaco
