# Quiz "Você é mais estranho do que pensa" — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Quiz web em pt-BR que mostra quantos brasileiros adultos compartilham exatamente a combinação de 8 características do usuário (PNAD Contínua), com bônus opcional de religião/política (ESEB 2022), site estático + contador anônimo, deploy Vercel.

**Architecture:** Pipeline Python offline transforma microdados públicos em duas tabelas JSON esparsas pré-computadas (`core.json` conjunta ponderada; `bonus.json` condicional com recuo). Site Astro com ilha React faz lookup 100% client-side. Único código de servidor: função `/api/contador` (Upstash Redis REST) que conta conclusões sem payload.

**Tech Stack:** Python 3.11+ (pandas, requests, pyreadstat, pytest) · Astro 4 + React 18 + Tailwind 4 + vitest · Vercel (static + serverless function) · Upstash Redis (REST).

**Spec:** `docs/superpowers/specs/2026-07-02-quiz-mais-estranho-que-voce-pensa-design.md`

## Global Constraints

- Idioma de toda UI e artigo: pt-BR. Código (nomes de função/variável): pt-BR sem acentos.
- Público: somente 18+ (filtrar `V2009 >= 18`).
- 8 dimensões do núcleo, NESTA ordem fixa (índices de célula dependem dela):
  `sexo(2), faixa_etaria(6), regiao(5), cor(5), escolaridade(5), renda(5), trabalho(5), internet(2)` — espaço de 75.000 células.
- Chave de célula: índices inteiros unidos por `|`, ex. `"0|2|3|2|4|1|0|1"`.
- Nunca exibir "0 pessoas": célula ausente → piso "menos de 1 em ~total_n".
- Nenhuma resposta do usuário sai do navegador; ping de conclusão sem payload.
- Microdados brutos NÃO são commitados (`.gitignore`); JSONs derivados SÃO commitados.
- Commits frequentes, Conventional Commits, mensagens em pt-BR.
- Rodapé de commit: `Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>`.
- Sanidade do pipeline: falha ruidosa (exceção com mensagem acionável), nunca silenciosa.

---

### Task 1: Scaffold do pipeline Python

**Files:**
- Create: `pipeline/requirements.txt`, `pipeline/pyproject.toml`, `pipeline/src/quizbr/__init__.py`, `pipeline/tests/__init__.py`, `.gitignore`

**Interfaces:**
- Produces: pacote `quizbr` importável nos testes (`pip install -e pipeline`), diretórios `pipeline/raw/` (ignorado) e `pipeline/out/`.

- [ ] **Step 1: Criar estrutura e arquivos**

`.gitignore` (raiz):
```gitignore
.venv/
__pycache__/
*.egg-info/
pipeline/raw/
node_modules/
dist/
.astro/
.vercel/
```

`pipeline/requirements.txt`:
```
pandas>=2.0
requests>=2.31
pyreadstat>=1.2
pytest>=8.0
```

`pipeline/pyproject.toml`:
```toml
[project]
name = "quizbr"
version = "0.1.0"
requires-python = ">=3.11"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
```

`pipeline/src/quizbr/__init__.py` e `pipeline/tests/__init__.py`: vazios.

- [ ] **Step 2: Criar venv, instalar, smoke test**

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r pipeline\requirements.txt
.\.venv\Scripts\pip install -e pipeline
.\.venv\Scripts\python -c "import quizbr; print('ok')"
```
Expected: `ok`

- [ ] **Step 3: Criar `pipeline/raw/.gitkeep` e `pipeline/out/.gitkeep`, commit**

```bash
git add -A
git commit -m "chore: scaffold do pipeline python"
```

---

### Task 2: Funções de recodificação (TDD)

**Files:**
- Create: `pipeline/src/quizbr/recode.py`
- Test: `pipeline/tests/test_recode.py`

**Interfaces:**
- Produces:
  - `DIMENSOES: list[tuple[str, list[str]]]` — ordem fixa das 8 dimensões com rótulos pt-BR.
  - `def recodificar_linha(v: dict) -> tuple[int, ...] | None` — recebe dict com chaves `V2007, V2009, UF, V2010, VD3004, RDPC, VD4001, VD4002, VD4009, INTERNET`; retorna tupla de 8 índices ou `None` (linha inválida/ignorada).
  - Funções puras: `sexo, faixa_etaria, regiao, cor, escolaridade, renda, trabalho, internet` — cada uma retorna `int | None`.

- [ ] **Step 1: Escrever testes**

`pipeline/tests/test_recode.py`:
```python
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
```

- [ ] **Step 2: Rodar, verificar falha**

```powershell
.\.venv\Scripts\python -m pytest pipeline\tests\test_recode.py -q
```
Expected: FAIL/ERROR (`recode` sem funções).

- [ ] **Step 3: Implementar**

`pipeline/src/quizbr/recode.py`:
```python
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
```

- [ ] **Step 4: Rodar testes, verificar PASS**

```powershell
.\.venv\Scripts\python -m pytest pipeline\tests\test_recode.py -q
```
Expected: todos PASS.

- [ ] **Step 5: Commit**

```bash
git add pipeline
git commit -m "feat: recodificação das 8 dimensões do núcleo (PNAD)"
```

---

### Task 3: Parser de dicionário SAS + leitor fixed-width (TDD)

**Files:**
- Create: `pipeline/src/quizbr/leitor.py`
- Test: `pipeline/tests/test_leitor.py`

**Interfaces:**
- Consumes: nada de tasks anteriores.
- Produces:
  - `def parse_input_sas(texto: str) -> dict[str, tuple[int, int]]` — nome da variável → (início 0-based, fim exclusivo), a partir do arquivo de input SAS do IBGE (linhas `@0001 Ano $4.` / `@0016 V2009 3.`).
  - `def ler_microdados(caminho_txt, posicoes, variaveis: list[str]) -> pandas.DataFrame` — lê só as colunas pedidas, numéricas (`errors="coerce"` → NaN vira None a jusante).
  - `def validar_variaveis(posicoes, obrigatorias: list[str]) -> None` — levanta `ValueError` listando faltantes E candidatas parecidas (substring), para falha ruidosa quando o layout do IBGE mudar.

- [ ] **Step 1: Escrever testes com fixture sintética**

`pipeline/tests/test_leitor.py`:
```python
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
```

- [ ] **Step 2: Rodar, verificar falha** — `pytest pipeline\tests\test_leitor.py -q` → FAIL.

- [ ] **Step 3: Implementar**

`pipeline/src/quizbr/leitor.py`:
```python
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
```

- [ ] **Step 4: Rodar testes** → PASS.

- [ ] **Step 5: Commit** — `git commit -m "feat: parser de dicionário SAS e leitor fixed-width"`

---

### Task 4: Configuração de fontes + script de download PNAD

**Files:**
- Create: `pipeline/src/quizbr/config.py`, `pipeline/src/quizbr/baixar.py`
- Create: `pipeline/README.md`

**Interfaces:**
- Produces:
  - `config.PNAD_ZIP_URL, config.PNAD_INPUT_URL, config.SALARIO_MINIMO, config.ANO, config.PESO, config.VAR_INTERNET, config.VAR_RDPC, config.POPULACAO_ADULTA_ESPERADA`
  - `python -m quizbr.baixar` — baixa e extrai microdados para `pipeline/raw/`.
  - `baixar.listar_ftp(url)` — imprime links de um diretório do FTP do IBGE (ajuda a corrigir URLs).

**Nota de realidade:** os nomes exatos de arquivo no FTP do IBGE mudam por ano/visita, e a variável de internet pertence ao módulo TIC anual. O executor DEVE: (1) rodar `listar_ftp` nos diretórios abaixo; (2) escolher o microdado ANUAL mais recente que contenha o módulo TIC (tema "Acesso à Internet e à televisão…"); (3) abrir o input SAS e confirmar `VAR_INTERNET` (variável "utilizou Internet nos últimos 3 meses", código sim=1/não=2) e `VAR_RDPC` (rendimento domiciliar per capita, ex. `VD5008`; se ausente, ver fallback na Task 5). A validação da Task 5 falha ruidosamente se os nomes estiverem errados — esse é o mecanismo de segurança.

- [ ] **Step 1: Implementar config**

`pipeline/src/quizbr/config.py`:
```python
from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "raw"
OUT = Path(__file__).resolve().parents[2] / "out"

ANO = 2024            # ajustar para o ano do microdado TIC mais recente
SALARIO_MINIMO = 1412.0  # SM vigente no ano de referência (2024)
PESO = "V1032"        # peso com pós-estratificação (arquivos anuais de visita)

# CONFIRMAR no input SAS (ver README) — validação falha ruidosamente se errado:
VAR_INTERNET = "S01029"   # usou internet nos últimos 3 meses (módulo TIC)
VAR_RDPC = "VD5008"       # rendimento domiciliar per capita habitual

FTP_BASE = ("https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
            "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/"
            "Microdados/Visita")
PNAD_ZIP_URL = ""    # preencher após listar_ftp (ex.: .../Visita_5/Dados/PNADC_2024_visita5.zip)
PNAD_INPUT_URL = ""  # preencher (ex.: .../Visita_5/Documentacao/input_PNADC_2024_visita5.txt)

# Faixa de sanidade: população adulta (18+) do Brasil, em milhões
POPULACAO_ADULTA_ESPERADA = (150_000_000, 175_000_000)

VARIAVEIS_NUCLEO = ["V2007", "V2009", "UF", "V2010", "VD3004",
                    "VD4001", "VD4002", "VD4009"]
```

- [ ] **Step 2: Implementar download**

`pipeline/src/quizbr/baixar.py`:
```python
import re
import sys
import zipfile
import requests
from quizbr import config


def listar_ftp(url):
    html = requests.get(url, timeout=60).text
    for link in re.findall(r'href="([^"]+)"', html):
        print(link)


def baixar(url, destino):
    destino.parent.mkdir(parents=True, exist_ok=True)
    print(f"Baixando {url} -> {destino}")
    with requests.get(url, stream=True, timeout=120) as r:
        r.raise_for_status()
        with open(destino, "wb") as f:
            for parte in r.iter_content(chunk_size=1 << 20):
                f.write(parte)


def main():
    if not config.PNAD_ZIP_URL or not config.PNAD_INPUT_URL:
        sys.exit("Preencha PNAD_ZIP_URL e PNAD_INPUT_URL em config.py. "
                 f"Use listar_ftp('{config.FTP_BASE}/...') para achar os arquivos.")
    zip_path = config.RAW / "pnad.zip"
    baixar(config.PNAD_ZIP_URL, zip_path)
    baixar(config.PNAD_INPUT_URL, config.RAW / "input_pnad.txt")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(config.RAW / "pnad")
    print("OK. Conteúdo extraído em", config.RAW / "pnad")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Escrever `pipeline/README.md`** documentando: como listar o FTP, escolher visita/ano com módulo TIC, confirmar `VAR_INTERNET`/`VAR_RDPC` no input SAS, e onde obter o ESEB 2022 (CESOP/UNICAMP — cadastro gratuito, baixar o `.sav` para `pipeline/raw/eseb2022.sav`).

- [ ] **Step 4: Executar de verdade** — rodar `listar_ftp`, preencher URLs, rodar `python -m quizbr.baixar`, confirmar variáveis no input baixado. Expected: arquivos em `pipeline/raw/pnad/`.

- [ ] **Step 5: Commit** (sem dados brutos) — `git commit -m "feat: download e configuração de fontes PNAD"`

---

### Task 5: Agregação → `core.json` + checagens de sanidade

**Files:**
- Create: `pipeline/src/quizbr/agregar.py`, `pipeline/src/quizbr/sanidade.py`
- Test: `pipeline/tests/test_agregar.py`, `pipeline/tests/test_sanidade.py`

**Interfaces:**
- Consumes: `recode.recodificar_linha`, `recode.DIMENSOES`, `leitor.*`, `config.*`.
- Produces:
  - `def agregar(df, peso_col, sm) -> dict` — retorna estrutura do `core.json`:
    ```json
    {
      "meta": {
        "fonte": "PNAD Contínua 2024 (IBGE)",
        "ano": 2024,
        "salario_minimo": 1412.0,
        "total_pop": 158000000.0,
        "total_n": 380000,
        "dims": [["sexo", ["Homem","Mulher"]], ...]
      },
      "cells": {"0|1|2|2|2|1|0|0": [123456.7, 87], ...}
    }
    ```
    `cells[k] = [soma_de_pesos, n_amostral]`, somente células com n ≥ 1.
  - `def checar_sanidade(core) -> None` — levanta `AssertionError` com mensagem acionável se: total fora de `POPULACAO_ADULTA_ESPERADA`; margem de qualquer dimensão fora das faixas em `MARGENS_ESPERADAS`; algum peso ≤ 0.
  - `python -m quizbr.agregar` — pipeline completo PNAD → `pipeline/out/core.json`.
  - Fallback RDPC: se `VAR_RDPC` ausente do dicionário, computar per capita = soma de `VD4020` por domicílio (`UPA`+`V1008`+`V1014`) ÷ nº de moradores (`V2001`).

- [ ] **Step 1: Testes de agregação com DataFrame sintético**

`pipeline/tests/test_agregar.py`:
```python
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
```

`pipeline/tests/test_sanidade.py`:
```python
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
```

- [ ] **Step 2: Rodar → FAIL.**

- [ ] **Step 3: Implementar `agregar.py`**

```python
import json
import sys
from collections import defaultdict
import pandas as pd
from quizbr import config, leitor
from quizbr.recode import DIMENSOES, recodificar_linha


def agregar(df, peso_col, sm):
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
    return {
        "meta": {
            "fonte": f"PNAD Contínua {config.ANO} (IBGE)",
            "ano": config.ANO,
            "salario_minimo": sm,
            "total_pop": round(total_pop, 1),
            "total_n": total_n,
            "dims": [[nome, labels] for nome, labels in DIMENSOES],
        },
        "cells": {k: [round(p, 1), n] for k, (p, n) in cells.items()},
    }


def _rdpc_fallback(df):
    dom = ["UPA", "V1008", "V1014"]
    renda_dom = df.groupby(dom)["VD4020"].transform(
        lambda s: s.fillna(0).sum())
    return renda_dom / df["V2001"]


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
    df = leitor.ler_microdados(txts[0], posicoes, variaveis)
    df["RDPC"] = df[config.VAR_RDPC] if tem_rdpc else _rdpc_fallback(df)
    df["INTERNET"] = df[config.VAR_INTERNET]
    core = agregar(df, peso_col=config.PESO, sm=config.SALARIO_MINIMO)
    from quizbr.sanidade import checar_sanidade
    checar_sanidade(core)
    destino = config.OUT / "core.json"
    destino.write_text(json.dumps(core, ensure_ascii=False), encoding="utf-8")
    print(f"OK: {destino} ({len(core['cells'])} células, "
          f"n={core['meta']['total_n']}, pop={core['meta']['total_pop']:,.0f})")


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Implementar `sanidade.py`**

```python
from quizbr import config
from quizbr.recode import DIMENSOES

# Faixas amplas de participação esperada por categoria (fração da população
# adulta). Conferidas contra tabelas públicas do IBGE; propositalmente largas —
# pegam catástrofe de parsing, não flutuação amostral.
MARGENS_ESPERADAS = {
    "sexo": [(0.44, 0.52), (0.48, 0.56)],
    "regiao": [(0.05, 0.12), (0.22, 0.32), (0.38, 0.48),
               (0.11, 0.18), (0.06, 0.11)],
    "internet": [(0.75, 0.97), (0.03, 0.25)],
}


def _margem(core, dim_nome):
    nomes = [n for n, _ in DIMENSOES]
    d = nomes.index(dim_nome)
    tam = len(DIMENSOES[d][1])
    somas = [0.0] * tam
    for chave, (peso, _n) in core["cells"].items():
        somas[int(chave.split("|")[d])] += peso
    total = core["meta"]["total_pop"]
    return [s / total for s in somas]


def checar_sanidade(core, checar_margens=None):
    total = core["meta"]["total_pop"]
    lo, hi = config.POPULACAO_ADULTA_ESPERADA
    assert lo <= total <= hi, (
        f"população adulta ponderada = {total:,.0f}, fora de [{lo:,}–{hi:,}]. "
        "Peso errado ou filtro de idade quebrado?")
    for peso, n in core["cells"].values():
        assert peso > 0 and n > 0, "célula com peso/n não positivo"
    dims = (MARGENS_ESPERADAS.keys() if checar_margens is None
            else checar_margens)
    if checar_margens is False:
        dims = []
    for nome in dims:
        obtido = _margem(core, nome)
        for i, (mn, mx) in enumerate(MARGENS_ESPERADAS[nome]):
            assert mn <= obtido[i] <= mx, (
                f"margem de {nome}[{i}] = {obtido[i]:.3f}, "
                f"esperado [{mn}–{mx}]. Recodificação ou layout errados?")
```

- [ ] **Step 5: Rodar testes** → PASS. Depois rodar de verdade: `python -m quizbr.agregar`. Expected: `OK: ...core.json` com sanidade passando; se falhar, corrigir config/variáveis (falha ruidosa é o comportamento desenhado).

- [ ] **Step 6: Commitar código + `pipeline/out/core.json`**

```bash
git add pipeline
git commit -m "feat: agregação ponderada PNAD -> core.json com sanidade"
```

---

### Task 6: Bônus ESEB 2022 → `bonus.json`

**Files:**
- Create: `pipeline/src/quizbr/bonus.py`
- Test: `pipeline/tests/test_bonus.py`

**Interfaces:**
- Consumes: `pipeline/raw/eseb2022.sav` (download manual documentado no README — CESOP/UNICAMP).
- Produces: `pipeline/out/bonus.json`:
  ```json
  {
    "meta": {
      "fonte": "ESEB 2022 (CESOP/UNICAMP)", "n": 2000,
      "religiao": ["Católica","Evangélica","Outras religiões","Sem religião"],
      "politica": ["Esquerda","Centro","Direita","Não se posiciona"],
      "niveis": ["regiao|sexo|faixa3|escol3", "regiao|escol3", "escol3", "global"]
    },
    "dist": {
      "0": {"2|1|0|1": {"0|2": 0.18, ...}},
      "1": {"2|1": {...}}, "2": {"1": {...}}, "3": {"": {...}}
    }
  }
  ```
  - Chave interna `"r|p"` = índice religião | índice política; valores = probabilidade condicional (somam ~1 por célula).
  - Regra de recuo: nível usado é o primeiro com n ≥ 30 respondentes.
  - `def fe3(faixa6: int) -> int` — [0,0,1,1,2,2]; `def es3(escol5: int) -> int` — [0,0,1,2,2]. Exportadas para espelhar no TypeScript (Task 8).
  - Mapeamento de variáveis do ESEB em `MAPA_ESEB` (config no topo de `bonus.py`): religião, escala esquerda-direita 0–10 (recode: 0–3 esquerda, 4–6 centro, 7–10 direita, NS/NR não se posiciona), UF/região, sexo, idade, escolaridade. Os nomes exatos vêm do codebook do ESEB 2022; `validar_variaveis`-style check falha ruidosamente listando colunas do .sav que contenham "reli", "esquerda", "escala" etc.

- [ ] **Step 1: Testes da lógica pura (recuo + recodificação política)**

`pipeline/tests/test_bonus.py`:
```python
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
```

- [ ] **Step 2: Rodar → FAIL.**

- [ ] **Step 3: Implementar `bonus.py`** — funções puras + `main()` que: lê o .sav com `pyreadstat.read_sav`, valida `MAPA_ESEB` contra as colunas (falha ruidosa com candidatas), recodifica cada respondente para `dict(regiao, sexo, f3, e3, rel, pol)`, chama `montar_niveis`, grava `bonus.json`.

```python
import json
from collections import Counter, defaultdict
import pyreadstat
from quizbr import config

RELIGIOES = ["Católica", "Evangélica", "Outras religiões", "Sem religião"]
POLITICAS = ["Esquerda", "Centro", "Direita", "Não se posiciona"]

# CONFIRMAR nomes no codebook do ESEB 2022 (CESOP). A validação abaixo
# falha ruidosamente listando colunas candidatas se algum nome estiver errado.
MAPA_ESEB = {"religiao": "D10", "escala_lr": "Q19",
             "uf": "UF", "sexo": "D2_SEXO", "idade": "D1A_IDADE",
             "escolaridade": "D3_ESCOLA"}


def fe3(faixa6):
    return [0, 0, 1, 1, 2, 2][faixa6]


def es3(escol5):
    return [0, 0, 1, 2, 2][escol5]


def politica_de_escala(v):
    if v is None or not (0 <= v <= 10):
        return 3
    if v <= 3:
        return 0
    if v <= 6:
        return 1
    return 2


def montar_niveis(respondentes, n_minimo=30):
    chaves = [
        lambda r: f"{r['regiao']}|{r['sexo']}|{r['f3']}|{r['e3']}",
        lambda r: f"{r['regiao']}|{r['e3']}",
        lambda r: f"{r['e3']}",
        lambda r: "",
    ]
    dist = {}
    for nivel, chave_fn in enumerate(chaves):
        grupos = defaultdict(Counter)
        tamanhos = Counter()
        for r in respondentes:
            k = chave_fn(r)
            grupos[k][f"{r['rel']}|{r['pol']}"] += 1
            tamanhos[k] += 1
        dist[str(nivel)] = {
            k: {rp: c / tamanhos[k] for rp, c in cnt.items()}
            for k, cnt in grupos.items()
            if tamanhos[k] >= (n_minimo if nivel < 3 else 1)
        }
    return dist
```
(`main()` completa a leitura do .sav, recodifica religião conforme codebook — católica/evangélica/outras/sem religião —, idade→faixa6→fe3, escolaridade→escol5→es3, UF→região, e grava JSON com `meta` incluindo `n`.)

- [ ] **Step 4: Rodar testes** → PASS. Rodar `python -m quizbr.bonus` com o .sav real → `pipeline/out/bonus.json`. Conferir margem de religião contra tabela do Censo 2022 (divulgada em 2025: ~56% católica, ~27% evangélica) — divergência > 10 p.p. → investigar recodificação antes de seguir.

- [ ] **Step 5: Commit** — `git commit -m "feat: distribuições condicionais ESEB -> bonus.json"`

---

### Task 7: Scaffold do site (Astro + React + Tailwind + vitest)

**Files:**
- Create: `site/` (projeto Astro), `site/src/lib/`, `site/public/data/`
- Create: `site/vitest.config.ts`

**Interfaces:**
- Produces: `npm run dev` funcional em `site/`; `core.json` e `bonus.json` copiados para `site/public/data/`; `npx vitest run` verde (0 testes).

- [ ] **Step 1: Criar projeto**

```powershell
cd site  # criar via:
npm create astro@latest site -- --template minimal --no-git --typescript strict --yes
cd site
npx astro add react tailwind --yes
npm i -D vitest
```

- [ ] **Step 2: `site/vitest.config.ts`**

```ts
import { defineConfig } from "vitest/config";
export default defineConfig({ test: { environment: "node" } });
```
Adicionar em `package.json`: `"test": "vitest run"`.

- [ ] **Step 3: Copiar dados** — `pipeline/out/core.json` e `bonus.json` → `site/public/data/`. Criar script npm `"dados": "node scripts/copiar-dados.mjs"` que faz a cópia (5 linhas, `fs.copyFileSync`).

- [ ] **Step 4: Verificar** — `npm run dev` sobe; `npm test` verde. Commit: `chore: scaffold do site astro+react+tailwind`.

---

### Task 8: Bibliotecas de lookup e share (TDD, TypeScript puro)

**Files:**
- Create: `site/src/lib/tipos.ts`, `site/src/lib/lookup.ts`, `site/src/lib/share.ts`
- Test: `site/src/lib/lookup.test.ts`, `site/src/lib/share.test.ts`

**Interfaces:**
- Consumes: esquemas de `core.json`/`bonus.json` (Tasks 5–6).
- Produces:
  ```ts
  // tipos.ts
  export interface CoreMeta { fonte: string; ano: number; salario_minimo: number;
    total_pop: number; total_n: number; dims: [string, string[]][]; }
  export interface Core { meta: CoreMeta; cells: Record<string, [number, number]>; }
  export interface Bonus { meta: { fonte: string; n: number;
    religiao: string[]; politica: string[]; niveis: string[] };
    dist: Record<string, Record<string, Record<string, number>>>; }
  export type Resultado =
    | { tipo: "exato"; umEmX: number; pessoas: number; nAmostral: number }
    | { tipo: "piso"; limiteUmEm: number };

  // lookup.ts
  export function buscar(core: Core, indices: number[]): Resultado;
  export function buscarBonus(core: Core, bonus: Bonus, indices: number[],
    rel: number, pol: number): Resultado;   // aplica recuo por nível
  export function fe3(f6: number): number;  // espelha bonus.py
  export function es3(e5: number): number;

  // share.ts
  export function codificar(indices: number[]): string;          // "0.1.2.2.2.1.0.0"
  export function decodificar(s: string, dims: [string, string[]][]): number[] | null;
  ```

- [ ] **Step 1: Testes**

`site/src/lib/lookup.test.ts`:
```ts
import { describe, it, expect } from "vitest";
import { buscar, buscarBonus, fe3, es3 } from "./lookup";
import type { Core, Bonus } from "./tipos";

const core: Core = {
  meta: { fonte: "t", ano: 2024, salario_minimo: 1412,
    total_pop: 160_000_000, total_n: 400_000,
    dims: [["sexo", ["H", "M"]], ["faixa_etaria", ["a","b","c","d","e","f"]],
           ["regiao", ["N","NE","SE","S","CO"]], ["cor", ["b","p","pa","am","i"]],
           ["escolaridade", ["1","2","3","4","5"]], ["renda", ["1","2","3","4","5"]],
           ["trabalho", ["1","2","3","4","5"]], ["internet", ["s","n"]]] },
  cells: { "0|1|2|2|2|1|0|0": [16_000_000, 40_000] },
};

const bonus: Bonus = {
  meta: { fonte: "t", n: 2000, religiao: ["Cat","Ev","Out","Sem"],
    politica: ["Esq","Cen","Dir","NP"],
    niveis: ["regiao|sexo|faixa3|escol3","regiao|escol3","escol3","global"] },
  dist: { "0": { "2|0|0|1": { "1|2": 0.25 } },
          "1": {}, "2": {}, "3": { "": { "1|2": 0.2 } } },
};

it("célula existente: 1 em 10", () => {
  const r = buscar(core, [0, 1, 2, 2, 2, 1, 0, 0]);
  expect(r).toEqual({ tipo: "exato", umEmX: 10,
    pessoas: 16_000_000, nAmostral: 40_000 });
});

it("célula ausente: piso = total_n", () => {
  const r = buscar(core, [1, 1, 2, 2, 2, 1, 0, 0]);
  expect(r).toEqual({ tipo: "piso", limiteUmEm: 400_000 });
});

it("bônus usa nível 0 quando disponível", () => {
  // indices: sexo=0, faixa=1 (fe3->0), regiao=2, escol=2 (es3->1)
  const r = buscarBonus(core, bonus, [0, 1, 2, 2, 2, 1, 0, 0], 1, 2);
  // 1/10 * 0.25 = 1/40
  expect(r).toEqual(expect.objectContaining({ tipo: "exato", umEmX: 40 }));
});

it("bônus recua até o global", () => {
  const b2: Bonus = { ...bonus, dist: { "0": {}, "1": {}, "2": {},
    "3": { "": { "1|2": 0.2 } } } };
  const r = buscarBonus(core, b2, [0, 1, 2, 2, 2, 1, 0, 0], 1, 2);
  expect(r).toEqual(expect.objectContaining({ umEmX: 50 })); // 1/10 * 0.2
});

it("grupos espelham o python", () => {
  expect([0,1,2,3,4,5].map(fe3)).toEqual([0,0,1,1,2,2]);
  expect([0,1,2,3,4].map(es3)).toEqual([0,0,1,2,2]);
});
```

`site/src/lib/share.test.ts`:
```ts
import { it, expect } from "vitest";
import { codificar, decodificar } from "./share";

const dims: [string, string[]][] = [
  ["sexo", ["H","M"]], ["faixa_etaria", ["a","b","c","d","e","f"]],
  ["regiao", ["N","NE","SE","S","CO"]], ["cor", ["b","p","pa","am","i"]],
  ["escolaridade", ["1","2","3","4","5"]], ["renda", ["1","2","3","4","5"]],
  ["trabalho", ["1","2","3","4","5"]], ["internet", ["s","n"]],
];

it("ida e volta", () => {
  const idx = [1, 5, 4, 2, 0, 3, 2, 1];
  expect(decodificar(codificar(idx), dims)).toEqual(idx);
});

it("rejeita fora do domínio e lixo", () => {
  expect(decodificar("9.0.0.0.0.0.0.0", dims)).toBeNull();
  expect(decodificar("abc", dims)).toBeNull();
  expect(decodificar("1.1.1", dims)).toBeNull();
});
```

- [ ] **Step 2: Rodar → FAIL.** `cd site; npx vitest run`

- [ ] **Step 3: Implementar**

`site/src/lib/lookup.ts`:
```ts
import type { Core, Bonus, Resultado } from "./tipos";

export const fe3 = (f6: number) => [0, 0, 1, 1, 2, 2][f6];
export const es3 = (e5: number) => [0, 0, 1, 2, 2][e5];

export function buscar(core: Core, indices: number[]): Resultado {
  const cell = core.cells[indices.join("|")];
  if (!cell) return { tipo: "piso", limiteUmEm: core.meta.total_n };
  const [peso, n] = cell;
  return {
    tipo: "exato",
    umEmX: Math.round(core.meta.total_pop / peso),
    pessoas: Math.round(peso),
    nAmostral: n,
  };
}

export function buscarBonus(core: Core, bonus: Bonus, indices: number[],
                            rel: number, pol: number): Resultado {
  const base = buscar(core, indices);
  const [sexo, f6, regiao, , e5] = indices;
  const chaves = [
    `${regiao}|${sexo}|${fe3(f6)}|${es3(e5)}`,
    `${regiao}|${es3(e5)}`,
    `${es3(e5)}`,
    "",
  ];
  let p: number | undefined;
  for (let nivel = 0; nivel < 4; nivel++) {
    const grupo = bonus.dist[String(nivel)]?.[chaves[nivel]];
    if (grupo) { p = grupo[`${rel}|${pol}`] ?? 0; break; }
  }
  if (p === undefined || p <= 0) return { tipo: "piso", limiteUmEm: core.meta.total_n };
  if (base.tipo === "piso") return base;
  const share = 1 / base.umEmX * p;
  return { tipo: "exato", umEmX: Math.round(1 / share),
    pessoas: Math.round(core.meta.total_pop * share), nAmostral: base.nAmostral };
}
```

`site/src/lib/share.ts`:
```ts
export function codificar(indices: number[]): string {
  return indices.join(".");
}

export function decodificar(s: string, dims: [string, string[]][]): number[] | null {
  const partes = s.split(".");
  if (partes.length !== dims.length) return null;
  const idx = partes.map((p) => Number(p));
  const ok = idx.every((v, i) =>
    Number.isInteger(v) && v >= 0 && v < dims[i][1].length);
  return ok ? idx : null;
}
```

`site/src/lib/tipos.ts`: interfaces conforme bloco Interfaces acima.

- [ ] **Step 4: Rodar testes** → PASS.

- [ ] **Step 5: Commit** — `feat: lookup com piso honesto e share por URL`

---

### Task 9: Componentes do quiz (fluxo, resultado, piso)

**Files:**
- Create: `site/src/components/Quiz.tsx`, `site/src/components/Pergunta.tsx`, `site/src/components/Resultado.tsx`
- Modify: `site/src/pages/index.astro`

**Interfaces:**
- Consumes: `buscar`, `codificar`, `decodificar`, tipos (Task 8); `/data/core.json` via `fetch`.
- Produces: `<Quiz client:load />` funcional; URL `?r=1.5.4.2.0.3.2.1` abre direto no resultado.

- [ ] **Step 1: Implementar componentes**

`Pergunta.tsx` — pergunta única com botões de opção:
```tsx
interface Props {
  titulo: string;
  opcoes: string[];
  onResponder: (i: number) => void;
  numero: number;
  total: number;
}

const TITULOS: Record<string, string> = {
  sexo: "Qual seu sexo?",
  faixa_etaria: "Qual sua idade?",
  regiao: "Em que região do Brasil você mora?",
  cor: "Qual sua cor ou raça (categorias do IBGE)?",
  escolaridade: "Até onde você estudou?",
  renda: "Qual a renda da sua casa, por pessoa?",
  trabalho: "Qual sua situação de trabalho?",
  internet: "Você usou a internet nos últimos 3 meses?",
};

export default function Pergunta({ titulo, opcoes, onResponder, numero, total }: Props) {
  return (
    <div className="space-y-4">
      <p className="text-sm text-neutral-500">Pergunta {numero} de {total}</p>
      <h2 className="text-2xl font-bold">{TITULOS[titulo] ?? titulo}</h2>
      <div className="grid gap-2">
        {opcoes.map((o, i) => (
          <button key={i} onClick={() => onResponder(i)}
            className="rounded-xl border border-neutral-300 px-4 py-3 text-left
                       hover:border-emerald-600 hover:bg-emerald-50 transition">
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}
```

`Resultado.tsx` — número grande + comparação + share + piso:
```tsx
import type { Resultado as R, CoreMeta } from "../lib/tipos";

const COMPARACOES: [number, string][] = [
  [1_000, "menos gente que um show de bairro"],
  [10_000, "cabe num ginásio pequeno"],
  [100_000, "menos que a torcida de um Maracanã lotado (x1,3)"],
  [1_000_000, "menos que a população de Florianópolis região"],
];

function comparar(pessoas: number): string {
  for (const [teto, frase] of COMPARACOES) if (pessoas < teto) return frase;
  return "ainda assim, uma fatia minúscula do Brasil";
}

export default function Resultado({ r, meta, urlShare, aoRefazer }:
  { r: R; meta: CoreMeta; urlShare: string; aoRefazer: () => void }) {
  const compartilhar = async () => {
    const dados = { title: "Você é mais estranho do que pensa",
      text: "Descobri quão raro é meu perfil no Brasil. E o seu?", url: urlShare };
    if (navigator.share) await navigator.share(dados);
    else { await navigator.clipboard.writeText(urlShare); alert("Link copiado!"); }
  };
  return (
    <div className="space-y-6 text-center">
      {r.tipo === "exato" ? (
        <>
          <p className="text-lg">Sua combinação exata aparece em</p>
          <p className="text-6xl font-black text-emerald-700">
            1 em {r.umEmX.toLocaleString("pt-BR")}
          </p>
          <p className="text-lg">
            brasileiros adultos — cerca de {r.pessoas.toLocaleString("pt-BR")} pessoas.
            <br /><span className="text-neutral-500">({comparar(r.pessoas)})</span>
          </p>
          <details className="text-sm text-neutral-500">
            <summary>Como esse número foi calculado?</summary>
            <p className="mt-2 text-left">
              Fonte: {meta.fonte}, amostra de {meta.total_n.toLocaleString("pt-BR")}{" "}
              pessoas com pesos que projetam a população adulta
              ({Math.round(meta.total_pop / 1e6)} milhões). Sua combinação teve{" "}
              {r.nAmostral.toLocaleString("pt-BR")} respondentes na amostra.
              Nenhuma resposta sua saiu do seu aparelho.
            </p>
          </details>
        </>
      ) : (
        <>
          <p className="text-lg">Sua combinação é tão rara que</p>
          <p className="text-4xl font-black text-emerald-700">
            não apareceu nem uma vez
          </p>
          <p className="text-lg">
            entre {r.limiteUmEm.toLocaleString("pt-BR")} entrevistados do IBGE.
            Estimativa honesta: menos de 1 em {r.limiteUmEm.toLocaleString("pt-BR")}.
          </p>
        </>
      )}
      <div className="flex justify-center gap-3">
        <button onClick={compartilhar}
          className="rounded-xl bg-emerald-700 px-6 py-3 font-bold text-white">
          Compartilhar meu resultado
        </button>
        <button onClick={aoRefazer} className="rounded-xl border px-6 py-3">
          Refazer
        </button>
      </div>
    </div>
  );
}
```

`Quiz.tsx` — orquestração:
```tsx
import { useEffect, useState } from "react";
import type { Core } from "../lib/tipos";
import { buscar } from "../lib/lookup";
import { codificar, decodificar } from "../lib/share";
import Pergunta from "./Pergunta";
import Resultado from "./Resultado";

export default function Quiz() {
  const [core, setCore] = useState<Core | null>(null);
  const [erro, setErro] = useState(false);
  const [respostas, setRespostas] = useState<number[]>([]);

  useEffect(() => {
    fetch("/data/core.json")
      .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
      .then((c: Core) => {
        setCore(c);
        const r = new URLSearchParams(location.search).get("r");
        if (r) {
          const idx = decodificar(r, c.meta.dims);
          if (idx) setRespostas(idx);
        }
      })
      .catch(() => setErro(true));
  }, []);

  if (erro) return <p>Não foi possível carregar os dados. Recarregue a página.</p>;
  if (!core) return <p>Carregando…</p>;

  const dims = core.meta.dims;
  if (respostas.length < dims.length) {
    const i = respostas.length;
    return (
      <Pergunta titulo={dims[i][0]} opcoes={dims[i][1]}
        numero={i + 1} total={dims.length}
        onResponder={(op) => setRespostas([...respostas, op])} />
    );
  }

  const r = buscar(core, respostas);
  const urlShare = `${location.origin}${location.pathname}?r=${codificar(respostas)}`;
  return (
    <Resultado r={r} meta={core.meta} urlShare={urlShare}
      aoRefazer={() => { setRespostas([]); history.replaceState(null, "", location.pathname); }} />
  );
}
```

`index.astro` (mínimo por enquanto; artigo entra na Task 11):
```astro
---
import Quiz from "../components/Quiz";
---
<html lang="pt-BR">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width" />
    <title>Você é mais estranho do que pensa</title>
  </head>
  <body class="mx-auto max-w-2xl p-6 font-sans">
    <h1 class="mb-8 text-4xl font-black">Você é mais estranho do que pensa</h1>
    <Quiz client:load />
  </body>
</html>
```

- [ ] **Step 2: Verificar manualmente** — `npm run dev`, responder as 8 perguntas, ver resultado; abrir URL com `?r=...` e ver resultado direto; `?r=lixo` deve cair no quiz normal.

- [ ] **Step 3: `npm test` continua verde. Commit** — `feat: fluxo do quiz com resultado, piso e compartilhamento`

---

### Task 10: Bônus (religião + política) e contador anônimo

**Files:**
- Create: `site/src/components/Bonus.tsx`, `site/api/contador.ts`
- Modify: `site/src/components/Quiz.tsx`, `site/src/components/Resultado.tsx`

**Interfaces:**
- Consumes: `buscarBonus` (Task 8), `/data/bonus.json`, `bonus.meta.religiao/politica` como opções.
- Produces:
  - `Bonus.tsx`: 2 perguntas opcionais após o resultado; exibe resultado refinado + disclaimer expansível com o texto exato abaixo.
  - `POST /api/contador` → `{count}` (INCR); `GET /api/contador` → `{count}` (leitura). Sem body, sem cookies. Se env ausente → `{count:null}` (no-op gracioso).
  - `Quiz.tsx` faz `POST /api/contador` UMA vez ao exibir o resultado (guard com `useRef`), e `Resultado.tsx` mostra "X pessoas já fizeram o quiz" quando `count` não for null.

**Texto do disclaimer (verbatim):**
> As 8 perguntas principais vêm de uma única pesquisa (PNAD Contínua/IBGE), o que permite calcular sua combinação exata. Religião e política não existem na PNAD: usamos o ESEB 2022 (CESOP/UNICAMP, ~2 mil entrevistados) e estimamos a probabilidade condicionada ao seu perfil demográfico (região, sexo, idade, escolaridade). É uma aproximação honesta, não uma contagem exata — por isso o bônus é separado.

- [ ] **Step 1: Implementar `site/api/contador.ts`**

```ts
import type { VercelRequest, VercelResponse } from "@vercel/node";

export default async function handler(req: VercelRequest, res: VercelResponse) {
  const url = process.env.UPSTASH_REDIS_REST_URL;
  const token = process.env.UPSTASH_REDIS_REST_TOKEN;
  if (!url || !token) return res.status(200).json({ count: null });
  const cmd = req.method === "POST" ? "INCR" : "GET";
  const r = await fetch(`${url}/${cmd}/quiz:conclusoes`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const j = (await r.json()) as { result?: string | number };
  res.status(200).json({ count: Number(j.result ?? 0) });
}
```
`npm i -D @vercel/node` em `site/`.

- [ ] **Step 2: Implementar `Bonus.tsx`**

```tsx
import { useState } from "react";
import type { Core, Bonus as BonusDados, Resultado as R } from "../lib/tipos";
import { buscarBonus } from "../lib/lookup";

const DISCLAIMER = `As 8 perguntas principais vêm de uma única pesquisa \
(PNAD Contínua/IBGE), o que permite calcular sua combinação exata. Religião \
e política não existem na PNAD: usamos o ESEB 2022 (CESOP/UNICAMP, ~2 mil \
entrevistados) e estimamos a probabilidade condicionada ao seu perfil \
demográfico (região, sexo, idade, escolaridade). É uma aproximação honesta, \
não uma contagem exata — por isso o bônus é separado.`;

export default function Bonus({ core, indices }:
  { core: Core; indices: number[] }) {
  const [dados, setDados] = useState<BonusDados | null>(null);
  const [erro, setErro] = useState(false);
  const [aberto, setAberto] = useState(false);
  const [rel, setRel] = useState<number | null>(null);
  const [pol, setPol] = useState<number | null>(null);

  const abrir = () => {
    setAberto(true);
    if (!dados) {
      fetch("/data/bonus.json")
        .then((r) => { if (!r.ok) throw new Error(); return r.json(); })
        .then(setDados)
        .catch(() => setErro(true));
    }
  };

  if (!aberto) {
    return (
      <button onClick={abrir} className="rounded-xl border px-6 py-3">
        Bônus: e se contarmos religião e política?
      </button>
    );
  }
  if (erro) return <p>Não foi possível carregar o bônus.</p>;
  if (!dados) return <p>Carregando bônus…</p>;

  if (rel === null) {
    return <Escolha titulo="Qual sua religião?" opcoes={dados.meta.religiao}
      onEscolher={setRel} />;
  }
  if (pol === null) {
    return <Escolha titulo="Em política, como você se posiciona?"
      opcoes={dados.meta.politica} onEscolher={setPol} />;
  }

  const r: R = buscarBonus(core, dados, indices, rel, pol);
  return (
    <div className="space-y-4 text-center">
      {r.tipo === "exato" ? (
        <p className="text-2xl font-bold">
          Com religião e política: cerca de 1 em{" "}
          {r.umEmX.toLocaleString("pt-BR")} brasileiros adultos.
        </p>
      ) : (
        <p className="text-2xl font-bold">
          Combinação rara demais para estimar com segurança: menos de 1 em{" "}
          {r.limiteUmEm.toLocaleString("pt-BR")}.
        </p>
      )}
      <details className="text-sm text-neutral-500 text-left">
        <summary>Por que este número é uma estimativa?</summary>
        <p className="mt-2">{DISCLAIMER}</p>
      </details>
    </div>
  );
}

function Escolha({ titulo, opcoes, onEscolher }:
  { titulo: string; opcoes: string[]; onEscolher: (i: number) => void }) {
  return (
    <div className="space-y-3">
      <h3 className="text-xl font-bold">{titulo}</h3>
      <div className="grid gap-2">
        {opcoes.map((o, i) => (
          <button key={i} onClick={() => onEscolher(i)}
            className="rounded-xl border px-4 py-3 text-left hover:bg-emerald-50">
            {o}
          </button>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Integrar no fluxo** — `Resultado.tsx` ganha slot "Bônus: e religião e política?" abaixo do share; `Quiz.tsx` dispara o ping:

Regra: visita via link compartilhado (`?r=`) NÃO conta como conclusão — só
quem respondeu as perguntas nesta sessão. Marcar `veioDeUrl` ao decodificar.

```tsx
const pingou = useRef(false);
const veioDeUrl = useRef(false);   // setar true no useEffect que lê ?r=
const [contagem, setContagem] = useState<number | null>(null);

useEffect(() => {
  if (respostas.length === dims.length && !pingou.current) {
    pingou.current = true;
    const metodo = veioDeUrl.current ? "GET" : "POST"; // GET só lê o total
    fetch("/api/contador", { method: metodo })
      .then((r) => r.json()).then((j) => setContagem(j.count))
      .catch(() => {});
  }
}, [respostas]);
```

- [ ] **Step 4: Verificar** — dev local sem env: quiz funciona, contador invisível (`count:null`). `npm test` verde.

- [ ] **Step 5: Commit** — `feat: bônus religião/política e contador anônimo de conclusões`

---

### Task 11: Artigo, metodologia e deploy Vercel

**Files:**
- Modify: `site/src/pages/index.astro`
- Create: `site/vercel.json` (se necessário para a function), `README.md` (raiz)

**Interfaces:**
- Consumes: tudo anterior.
- Produces: site publicado na Vercel com Analytics ativo; README com instruções de re-geração dos dados.

- [ ] **Step 1: Escrever o artigo em `index.astro`** (rascunho para o usuário editar — estrutura obrigatória):
  1. Abertura: "Pense no brasileiro médio. Agora responda: você é ele?" — tese de que quase ninguém é.
  2. Por que isso importa perto da eleição de 2026: cada bolha acha que é o país.
  3. O quiz (ilha React).
  4. Seção "Metodologia" (após o quiz): PNAD, pesos, por que não multiplicamos probabilidades independentes, ESEB no bônus, link para o repositório.
  5. Crédito e link para o original de Uri (atvbt.com).

- [ ] **Step 2: Deploy**

```powershell
cd site
npx vercel --yes          # projeto novo
npx vercel --prod
```
Ativar Vercel Analytics no dashboard. Criar Upstash Redis (marketplace Vercel), setar `UPSTASH_REDIS_REST_URL`/`UPSTASH_REDIS_REST_TOKEN` nas env vars, redeploy.

- [ ] **Step 3: Verificação de produção** — quiz completo no celular (viewport mobile), share URL abre resultado, contador incrementa, `?r=` inválido não quebra.

- [ ] **Step 4: README raiz** — como rodar pipeline, como atualizar ano da PNAD, como rodar site, deploy.

- [ ] **Step 5: Commit + push** — `docs: artigo, metodologia e instruções de deploy`

---

## Riscos mapeados

1. **Layout/variáveis do IBGE** — mitigado: validação ruidosa com candidatas (Task 3/4), fallback de RDPC (Task 5).
2. **Nomes de variáveis do ESEB** — mitigado: `MAPA_ESEB` validado contra colunas do .sav com sugestões (Task 6); margem de religião conferida contra Censo 2022.
3. **Células vazias frequentes** (75 mil células, ~400 mil respondentes ponderados) — comportamento desenhado: piso honesto, nunca "0 pessoas".
4. **Contador sem Upstash configurado** — no-op gracioso, site funciona 100% sem ele.
