"""Leitura local de CSVs em fluxo, inclusive membros de ZIPs do INEP."""

import argparse
import csv
import io
from contextlib import contextmanager
from pathlib import Path
from tempfile import NamedTemporaryFile
from zipfile import BadZipFile, ZipFile


@contextmanager
def open_csv(path, encoding, member=None):
    if member is not None:
        with ZipFile(path) as archive, archive.open(member) as binary:
            with io.TextIOWrapper(binary, encoding=encoding, newline="") as stream:
                yield stream
    else:
        if path.suffix.lower() == ".zip":
            raise ValueError("Informe --membro com o caminho do CSV dentro do ZIP.")
        with path.open(encoding=encoding, newline="") as stream:
            yield stream


def rows(stream, delimiter, required=(), limit=None):
    if len(delimiter) != 1:
        raise ValueError("O separador deve ter exatamente um caractere.")
    if limit is not None and limit <= 0:
        raise ValueError("O limite deve ser positivo.")
    reader = csv.reader(stream, delimiter=delimiter, strict=True)
    header = [name.lstrip("\ufeff").strip() for name in next(reader, [])]
    if not header or "" in header or len(set(header)) != len(header):
        raise ValueError("Cabeçalho vazio, inválido ou com colunas duplicadas.")
    missing = sorted(set(required) - set(header))
    if missing:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(missing))
    positions = [(name, header.index(name)) for name in (required or header)]

    def records():
        count = 0
        while limit is None or count < limit:
            values = next(reader, None)
            if values is None:
                break
            if not values:
                continue
            if len(values) != len(header):
                raise ValueError(f"Linha {reader.line_num}: quantidade incorreta de campos.")
            count += 1
            yield reader.line_num, {name: values[index] for name, index in positions}

    return header, records()


@contextmanager
def csv_output(path, columns, encoding):
    """Publica o CSV completo de forma atômica e recusa destinos existentes."""
    if path.exists():
        raise FileExistsError(f"Destino já existe: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
        pending = Path(temporary.name)
    try:
        with pending.open("w", encoding=encoding, newline="") as stream:
            writer = csv.DictWriter(stream, columns, delimiter=";", lineterminator="\r\n")
            writer.writeheader()
            yield writer
        path.hardlink_to(pending)
    finally:
        pending.unlink()


def csv_arguments(parser):
    parser.add_argument("--entrada", required=True, type=Path)
    parser.add_argument("--saida", required=True, type=Path)
    parser.add_argument("--membro", help="Caminho exato do CSV dentro do ZIP local.")
    parser.add_argument("--encoding", help="Codificação da entrada.")
    parser.add_argument("--separador", default=";")
    parser.add_argument("--limite", type=int, help="Máximo de registros de entrada para amostra.")


def extract(source, destination, *, encoding="utf-8-sig", delimiter=";", member=None, limit=None):
    with open_csv(source, encoding, member) as stream:
        header, records = rows(stream, delimiter, limit=limit)
        with csv_output(destination, header, "utf-8") as output:
            for _, record in records:
                output.writerow(record)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    csv_arguments(parser)
    options = parser.parse_args()
    try:
        extract(options.entrada, options.saida, encoding=options.encoding or "utf-8-sig",
                delimiter=options.separador, member=options.membro, limit=options.limite)
    except (ValueError, OSError, LookupError, csv.Error, BadZipFile) as error:
        parser.exit(2, f"Erro de extração: {error}\n")


if __name__ == "__main__":
    main()
