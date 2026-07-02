from pathlib import Path

RAW = Path(__file__).resolve().parents[2] / "raw"
OUT = Path(__file__).resolve().parents[2] / "out"

ANO = 2025            # ano do microdado TIC mais recente (confirmado via listar_ftp em 2026-07-02)
SALARIO_MINIMO = 1518.0  # SM vigente no ano de referência (2025 — Decreto nº 12.342/2024)
PESO = "V1032"        # peso com pós-estratificação (arquivos anuais de visita)

# CONFIRMADO no input SAS de 2025/visita1 (ver README) — validação falha ruidosamente se errado:
VAR_INTERNET = "S01029"   # "Acessa à Internet por meio de microcomputador, tablet, celular, televisão ou outro equipamento?" (módulo TIC, sim=1/não=2)
VAR_RDPC = "VD5008"       # rendimento domiciliar per capita habitual

FTP_BASE = ("https://ftp.ibge.gov.br/Trabalho_e_Rendimento/"
            "Pesquisa_Nacional_por_Amostra_de_Domicilios_continua/Anual/"
            "Microdados/Visita")
PNAD_ZIP_URL = FTP_BASE + "/Visita_1/Dados/PNADC_2025_visita1_20260508.zip"
PNAD_INPUT_URL = FTP_BASE + "/Visita_1/Documentacao/input_PNADC_2025_visita1_20260508.txt"

# Faixa de sanidade: população adulta (18+) do Brasil, em milhões
POPULACAO_ADULTA_ESPERADA = (150_000_000, 175_000_000)

VARIAVEIS_NUCLEO = ["V2007", "V2009", "UF", "V2010", "VD3004",
                    "VD4001", "VD4002", "VD4009"]
