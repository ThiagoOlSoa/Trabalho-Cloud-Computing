"""Gera ou confere os hashes de todos os arquivos versionados, exceto o manifesto."""
import argparse
import hashlib
import subprocess
from pathlib import Path

from scripts.verificar_arquivos_ci import blocked

MANIFESTO = Path("MANIFESTO_SHA256.txt")


def conteudo():
    caminhos = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    linhas = []
    for nome in sorted(set(caminhos) - {"", str(MANIFESTO)}):
        if blocked(nome):
            raise SystemExit(f"Arquivo protegido no índice: {nome}")
        caminho = Path(nome)
        if not caminho.is_file() or caminho.is_symlink():
            raise SystemExit(f"Arquivo ausente ou inesperado: {nome}")
        with caminho.open("rb") as arquivo:
            digest = hashlib.file_digest(arquivo, "sha256").hexdigest()
        linhas.append(f"{digest}  {nome}\n")
    return "".join(linhas)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    esperado = conteudo()
    if args.check:
        if not MANIFESTO.is_file() or MANIFESTO.read_text(encoding="utf-8") != esperado:
            raise SystemExit("Manifesto divergente. Revise os arquivos e gere novamente.")
        print(f"Manifesto SHA-256 verificado: {len(esperado.splitlines())} arquivos.")
    else:
        MANIFESTO.write_text(esperado, encoding="utf-8")


if __name__ == "__main__":
    main()
