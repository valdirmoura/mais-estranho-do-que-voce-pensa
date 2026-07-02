# pipeline

Pipeline de dados para o quiz — combina microdados da PNAD Contínua Anual
(IBGE) com o ESEB 2022 (CESOP/UNICAMP).

## Fontes de dados

### PNAD Contínua Anual (módulo TIC)

O IBGE publica os microdados anuais da PNAD Contínua em "visitas" (Visita_1 a
Visita_5). Cada visita cobre um subconjunto de temas suplementares, e **os
nomes de arquivo mudam a cada ano/revisão** — nunca hardcode uma URL sem
confirmar antes.

O módulo TIC (tema "Acesso à Internet e à televisão e posse de telefone móvel
celular para uso pessoal") já esteve na Visita_5 (anos 2016–2019) e, a
partir de 2022, passou para a Visita_1. **Confirme sempre em qual visita o
módulo está no ano desejado** — não assuma que continua na mesma visita do
ano anterior.

#### 1. Listar o FTP

```python
from quizbr.baixar import listar_ftp
from quizbr import config

# lista as visitas disponíveis
listar_ftp(config.FTP_BASE + "/")

# lista anos disponíveis dentro de uma visita
listar_ftp(config.FTP_BASE + "/Visita_1/Dados/")
listar_ftp(config.FTP_BASE + "/Visita_1/Documentacao/")
```

Repita para `Visita_2` .. `Visita_5` se precisar confirmar onde está o
módulo TIC em um ano específico.

#### 2. Escolher o ano/visita mais recente com o módulo TIC

Baixe (ou apenas faça `GET`) o `input_PNADC_<ano>_visita<n>_<data>.txt`
(pasta `Documentacao/`) do candidato mais recente e procure por variáveis
`S01xxx` (bloco de características do domicílio, onde mora o módulo TIC) e
pela linha cujo comentário contenha "Internet". Exemplo confirmado em
2026-07-02, arquivo `input_PNADC_2025_visita1_20260508.txt`:

```
@0058 V1032   15.   /* Peso COM calibração */
@0510 S01028   $1.   /* Tem microcomputador (considere inclusive os portáteis) */
@0511 S01029   $1.   /* Acessa à Internet por meio de microcomputador, tablet, celular, televisão ou outro equipamento? */
@0667 VD5008   8.   /* Rend habitual domiciliar per capita */
```

Isso confirma três coisas ao mesmo tempo:
- `VAR_INTERNET = "S01029"` — pergunta de uso de internet do módulo TIC
  (códigos padrão IBGE: sim=1, não=2).
- `VAR_RDPC = "VD5008"` — rendimento domiciliar per capita habitual (variável
  derivada, presente nesse arquivo; não é necessário fallback).
- `PESO = "V1032"` — peso com pós-estratificação/calibração.

Se `VD5008` não existir no ano escolhido, use como fallback `VD5011` (rend.
habitual domiciliar per capita, série alternativa) ou `VD5005`/`VD5002`
(rendimento **efetivo** em vez de habitual) — documente a escolha no
`config.py` e ajuste a Task 5 de acordo.

**As posições de coluna (`@NNNN`) mudam a cada ano** porque o número de
réplicas de peso e outras variáveis varia. Por isso `leitor.parse_input_sas`
sempre reprocessa o dicionário do ano baixado — nunca hardcode offsets.

#### 3. Preencher `config.py`

Depois de confirmar ano/visita/variáveis, edite `pipeline/src/quizbr/config.py`:

```python
ANO = 2025
SALARIO_MINIMO = 1518.0   # SM vigente no ano de referência
PNAD_ZIP_URL = FTP_BASE + "/Visita_1/Dados/PNADC_2025_visita1_20260508.zip"
PNAD_INPUT_URL = FTP_BASE + "/Visita_1/Documentacao/input_PNADC_2025_visita1_20260508.txt"
VAR_INTERNET = "S01029"
VAR_RDPC = "VD5008"
```

#### 4. Baixar

```bash
python -m quizbr.baixar
```

Isso baixa `pipeline/raw/pnad.zip` (~180 MB) e `pipeline/raw/input_pnad.txt`,
depois extrai o zip em `pipeline/raw/pnad/` (um único `.txt` de microdados,
formato largura fixa). O download pode levar vários minutos.

#### 5. Validar

Depois de baixar, confirme que o dicionário aponta corretamente para as
variáveis usadas pela Task 5:

```python
from pathlib import Path
from quizbr import config
from quizbr.leitor import parse_input_sas, validar_variaveis

texto = (config.RAW / "input_pnad.txt").read_text(encoding="latin-1")
posicoes = parse_input_sas(texto)
validar_variaveis(posicoes, config.VARIAVEIS_NUCLEO + [config.PESO, config.VAR_INTERNET])
print("VAR_RDPC presente:", config.VAR_RDPC in posicoes)
```

Se `validar_variaveis` lançar `ValueError`, o layout do IBGE mudou — volte ao
passo 2 e confirme os novos nomes antes de rodar a Task 5.

### ESEB 2022 (CESOP/UNICAMP)

O ESEB (Estudo Eleitoral Brasileiro) 2022 é distribuído pelo CESOP/UNICAMP
mediante cadastro gratuito:

1. Acesse o banco de dados do CESOP: https://cesop.unicamp.br/
2. Localize o "ESEB 2022" (Estudo Eleitoral Brasileiro, pós-eleitoral 2022)
   no catálogo de pesquisas.
3. Crie uma conta gratuita (ou faça login) — o CESOP exige cadastro para
   liberar o download de microdados.
4. Baixe o arquivo em formato SPSS (`.sav`).
5. Salve como `pipeline/raw/eseb2022.sav`.

## Dados brutos ficam fora do git

Nenhum dado bruto (PNAD ou ESEB) deve ser versionado — apenas o código de
processamento. `pipeline/raw/` e `pipeline/out/` contêm apenas `.gitkeep`.
