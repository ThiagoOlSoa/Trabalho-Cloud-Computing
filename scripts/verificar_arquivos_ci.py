"""Revisa caminhos do índice Git e valida sintaxe Python sem executar o código."""
import ast
import re
import subprocess
import sys
import tokenize
from pathlib import PurePosixPath

BLOCKED = re.compile(
    r"(?:^|/)(?:\.env(?:\.[^/]+)?|secrets\.toml|\.terraform|__pycache__|"
    r"\.venv|venv|\.pytest_cache)(?:/|$)|"
    r"\.(?:pem|key|p12|pfx|crt|cer|tfplan|tfvars|parquet|feather|pyc|pyo)$|"
    r"\.tfstate(?:\..*)?$|(?:^|/)crash(?:\..*)?\.log$", re.I
)
PUBLIC_DATA = {
    "data/raw/README.md", "data/processed/README.md",
    "data/processed/censo_2024_area1.csv.gz", "data/processed/enade_2023_area1.csv.gz",
}


def blocked(path):
    if path.startswith(("data/raw/", "data/processed/")):
        return path not in PUBLIC_DATA
    return PurePosixPath(path).name != ".env.example" and bool(BLOCKED.search(path))


def main():
    tracked = subprocess.check_output(["git", "ls-files", "-z"]).decode().split("\0")
    forbidden = [path for path in tracked if blocked(path)]
    for path in forbidden:
        print(f"Arquivo proibido no Git: {path}", file=sys.stderr)
    python_files = [path for path in tracked if path.endswith(".py")]
    invalid = 0
    for path in python_files:
        try:
            with tokenize.open(path) as source:
                ast.parse(source.read(), filename=path)
        except (SyntaxError, UnicodeError, OSError) as error:
            # Registra o local sem imprimir o conteúdo da linha.
            print(f"Python inválido: {path} | linha {getattr(error, 'lineno', '?')}", file=sys.stderr)
            invalid += 1
    print(f"{len(python_files)} arquivos Python, {invalid} inválidos, {len(forbidden)} caminhos proibidos.")
    return int(bool(forbidden or invalid))


if __name__ == "__main__":
    sys.exit(main())
