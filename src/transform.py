"""Prepara o cadastro de cursos Censo 2024 e o agregado ENADE 2023."""

import argparse
import csv
import re
from decimal import Decimal
from pathlib import Path
from zipfile import BadZipFile

if __package__:
    from .extract import csv_arguments, csv_output, open_csv, rows
else:
    from extract import csv_arguments, csv_output, open_csv, rows


AREA_1 = {"05", "06", "07"}
GEOGRAPHY = "CO_REGIAO NO_REGIAO NO_UF SG_UF CO_UF NO_MUNICIPIO CO_MUNICIPIO IN_CAPITAL".split()
CINE = {
    "CO_CINE_AREA_GERAL": 2, "CO_CINE_AREA_ESPECIFICA": 3,
    "CO_CINE_AREA_DETALHADA": 4, "CO_CINE_ROTULO": 7,
}
CENSO_RACE = "BRANCA PRETA PARDA AMARELA INDIGENA CORND".split()
CENSO_TOTALS = ["QT_ING", "QT_MAT", "QT_CONC"]
CENSO_COUNTS = [
    column
    for total in CENSO_TOTALS
    for column in [total, *(f"{total}_{suffix}" for suffix in ["FEM", "MASC", *CENSO_RACE])]
]
SITUATIONS = "QT_SIT_TRANCADA QT_SIT_DESVINCULADO QT_SIT_TRANSFERIDO QT_SIT_FALECIDO".split()
SHIFTS = [f"{total}_{suffix}" for total in CENSO_TOTALS for suffix in ("DIURNO", "NOTURNO")]
CENSO_COLUMNS = [
    *"""NU_ANO_CENSO CO_IES CO_CURSO NO_CURSO CO_CINE_AREA_GERAL NO_CINE_AREA_GERAL
        CO_CINE_AREA_ESPECIFICA NO_CINE_AREA_ESPECIFICA CO_CINE_ROTULO NO_CINE_ROTULO""".split(),
    *GEOGRAPHY[:7],
    *"""TP_ORGANIZACAO_ACADEMICA TP_REDE TP_CATEGORIA_ADMINISTRATIVA IN_COMUNITARIA
        IN_CONFESSIONAL TP_GRAU_ACADEMICO TP_MODALIDADE_ENSINO TP_NIVEL_ACADEMICO""".split(),
    *CENSO_COUNTS, *SITUATIONS, "CO_CINE_AREA_DETALHADA", "NO_CINE_AREA_DETALHADA",
    "IN_CAPITAL", "TP_DIMENSAO", "IN_GRATUITO", *SHIFTS,
]
ENADE_META = """NU_ANO CO_CURSO CO_IES CO_GRUPO CO_MODALIDADE CO_UF_CURSO
                CO_MUNIC_CURSO CO_REGIAO_CURSO""".split()
ENADE_GRADES = "MEDIA_NT_GER MEDIA_NT_FG MEDIA_NT_CE".split()
ENADE_SEX = ["QT_SEXO_F", "QT_SEXO_M"]
ENADE_RACE = [f"QT_RACA_{name}" for name in [
    *CENSO_RACE[:-1], "NAO_DECLARA", "SEM_RESPOSTA",
]]
ENADE_COUNTS = ["QT_PARTICIPANTES", "QT_NOTAS_VALIDAS", *ENADE_SEX, *ENADE_RACE]
ENADE_COLUMNS = [*ENADE_META, *ENADE_COUNTS[:2], *ENADE_GRADES, *ENADE_COUNTS[2:]]


def integer(record, field, *, optional=False, minimum=0):
    value = record[field].strip()
    if optional and value in ("", "."):
        return None
    if not re.fullmatch(r"[0-9]+", value):
        raise ValueError(f"{field} deve ser um inteiro, recebido {value!r}.")
    number = int(value)
    if not minimum <= number <= 2_147_483_647:
        raise ValueError(f"{field} fora do intervalo permitido.")
    return number


def cine_code(record, field):
    value = record[field].strip().strip('"').strip()
    width = CINE[field]
    if field == "CO_CINE_ROTULO":
        valid = len(value) == width and re.fullmatch(r"[0-9A-Z]+", value)
    else:
        valid = 1 <= len(value) <= width and re.fullmatch(r"[0-9]+", value)
    if not valid:
        raise ValueError(f"{field} tem código Cine inválido: {value!r}.")
    return value.zfill(width)


def normalize_censo(record):
    year = integer(record, "NU_ANO_CENSO")
    if year != 2024:
        return None
    if record["CO_CINE_AREA_GERAL"].strip() in ("", "."):
        return None
    area = cine_code(record, "CO_CINE_AREA_GERAL")
    if area not in AREA_1 or integer(record, "TP_NIVEL_ACADEMICO") != 1:
        return None

    cleaned = {}
    for name, value in record.items():
        if name in CINE:
            cleaned[name] = cine_code(record, name)
        elif name.startswith("NO_") or name == "SG_UF":
            label = value.strip()
            cleaned[name] = None if name in GEOGRAPHY and label in ("", ".") else label
        elif name in SHIFTS and record["TP_MODALIDADE_ENSINO"].strip() == "2" and value.strip() == ".":
            cleaned[name] = 0
        else:
            cleaned[name] = integer(
                record, name, optional=name in GEOGRAPHY or name == "TP_GRAU_ACADEMICO",
                minimum=1 if name in ("CO_CURSO", "CO_IES", "CO_MUNICIPIO") else 0,
            )

    if cleaned["TP_DIMENSAO"] not in (1, 2, 3, 4):
        raise ValueError("TP_DIMENSAO deve estar entre 1 e 4.")
    if cleaned["TP_MODALIDADE_ENSINO"] not in (1, 2):
        raise ValueError("TP_MODALIDADE_ENSINO deve ser 1 ou 2.")
    for total in CENSO_TOTALS:
        for group in (("FEM", "MASC"), CENSO_RACE):
            if sum(cleaned[f"{total}_{suffix}"] for suffix in group) != cleaned[total]:
                raise ValueError(f"As contagens de {total} não reconciliam com o total.")
    return cleaned


def normalize_enade(record, courses):
    if integer(record, "NU_ANO") != 2023:
        return None
    course = integer(record, "CO_CURSO", minimum=1)
    if course not in courses:
        return None
    cleaned = {
        name: integer(record, name, optional=name in ENADE_META[2:],
                      minimum=1 if name in ("CO_CURSO", "CO_IES") else 0)
        for name in [*ENADE_META, *ENADE_COUNTS]
    }
    if cleaned["CO_MODALIDADE"] not in (None, 0, 1):
        raise ValueError("CO_MODALIDADE do ENADE deve ser 0 ou 1.")
    participants = cleaned["QT_PARTICIPANTES"]
    valid = cleaned["QT_NOTAS_VALIDAS"]
    if valid > participants or any(sum(cleaned[k] for k in g) != participants
                                   for g in (ENADE_SEX, ENADE_RACE)):
        raise ValueError("Contagens de notas, sexo ou raça/cor incompatíveis com QT_PARTICIPANTES.")
    for field in ENADE_GRADES:
        raw = record[field].strip()
        if not raw or raw == ".":
            if valid:
                raise ValueError(f"{field} ausente com QT_NOTAS_VALIDAS positivo.")
            cleaned[field] = None
            continue
        if not re.fullmatch(r"[0-9]+(?:[.,][0-9]+)?", raw):
            raise ValueError(f"{field} deve conter uma nota decimal entre 0 e 100.")
        grade = Decimal(raw.replace(",", "."))
        if not valid or not 0 <= grade <= 100:
            raise ValueError(f"{field} incompatível com o intervalo ou a contagem de notas válidas.")
        cleaned[field] = format(grade, "f")
    return cleaned


def censo_courses(path):
    fields = ["NU_ANO_CENSO", "CO_CURSO", "CO_CINE_AREA_GERAL", "TP_NIVEL_ACADEMICO"]
    with path.open(encoding="cp1252", newline="") as stream:
        _, records = rows(stream, ";", fields)
        courses = {
            integer(record, "CO_CURSO", minimum=1)
            for _, record in records
            if integer(record, "NU_ANO_CENSO") == 2024
            and cine_code(record, "CO_CINE_AREA_GERAL") in AREA_1
            and integer(record, "TP_NIVEL_ACADEMICO") == 1
        }
    if not courses:
        raise ValueError("O Censo de referência não contém cursos de graduação da Área 1 em 2024.")
    return courses


def transform(dataset, source, destination, *, censo_reference=None, encoding=None,
              delimiter=";", member=None, limit=None):
    if dataset == "censo":
        columns = CENSO_COLUMNS
        output_encoding = "cp1252"
        key = ["NU_ANO_CENSO", "CO_CURSO", "TP_DIMENSAO", "CO_MUNICIPIO"]
        normalize = normalize_censo
    elif dataset == "enade":
        if censo_reference is None:
            raise ValueError("Informe o CSV Censo transformado para selecionar os cursos do ENADE.")
        columns = ENADE_COLUMNS
        output_encoding = "utf-8"
        key = ["NU_ANO", "CO_CURSO"]
        courses = censo_courses(censo_reference)

        def normalize(record):
            return normalize_enade(record, courses)
    else:
        raise ValueError(f"Base desconhecida: {dataset}")

    seen = set()
    with open_csv(source, encoding or ("cp1252" if dataset == "censo" else "utf-8-sig"),
                  member) as stream:
        _, records = rows(stream, delimiter, columns, limit)
        with csv_output(destination, columns, output_encoding) as output:
            for line, record in records:
                try:
                    cleaned = normalize(record)
                    if cleaned is None:
                        continue
                    identity = tuple(cleaned[name] for name in key)
                    if identity in seen:
                        raise ValueError(f"Chave duplicada {identity} para {', '.join(key)}.")
                    seen.add(identity)
                    output.writerow(cleaned)
                except ValueError as error:
                    raise ValueError(f"Linha {line}: {error}") from error
            if not seen:
                raise ValueError("Nenhum registro atende ao recorte. Nenhum CSV foi publicado.")
    return len(seen)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="dataset", required=True)
    csv_arguments(subparsers.add_parser("censo"))
    enade = subparsers.add_parser("enade", help="Recebe o ENADE já agregado por ano e curso.")
    csv_arguments(enade)
    enade.add_argument("--censo-processado", required=True, type=Path)
    args = parser.parse_args()
    try:
        count = transform(
            args.dataset, args.entrada, args.saida, censo_reference=getattr(args, "censo_processado", None),
            encoding=args.encoding, delimiter=args.separador, member=args.membro, limit=args.limite,
        )
    except (ValueError, OSError, LookupError, csv.Error, BadZipFile) as error:
        parser.exit(2, f"Erro de transformação: {error}\n")
    print(f"{count} registros gravados em {args.saida}")


if __name__ == "__main__":
    main()
