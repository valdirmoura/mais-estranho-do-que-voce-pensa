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
