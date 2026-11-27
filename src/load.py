"""Valida e carrega o Censo 2024 em uma única transação PostgreSQL."""

import argparse
import csv
import gzip
import os
import zlib
from contextlib import closing
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from psycopg2.extras import execute_values

if __package__:
    from .extract import rows
    from .transform import CENSO_COLUMNS, normalize_censo
else:
    from extract import rows
    from transform import CENSO_COLUMNS, normalize_censo

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "processed" / "censo_2024_area1.csv"
BATCH_SIZE = 500

COLUNAS_IES = [
    "CO_IES",
    "TP_REDE",
    "TP_ORGANIZACAO_ACADEMICA",
    "TP_CATEGORIA_ADMINISTRATIVA",
    "IN_COMUNITARIA",
    "IN_CONFESSIONAL"
]

COLUNAS_CURSO = [
    "CO_CURSO",
    "CO_IES",
    "NO_CURSO",
    "TP_GRAU_ACADEMICO",
    "TP_MODALIDADE_ENSINO",
    "TP_NIVEL_ACADEMICO",
    "IN_GRATUITO"
]

COLUNAS_CINE = [
    "CO_CINE_ROTULO",
    "NO_CINE_ROTULO",
    "CO_CINE_AREA_DETALHADA",
    "NO_CINE_AREA_DETALHADA",
    "CO_CINE_AREA_ESPECIFICA",
    "NO_CINE_AREA_ESPECIFICA",
    "CO_CINE_AREA_GERAL",
    "NO_CINE_AREA_GERAL"
]

COLUNAS_LOCALIZACAO = [
    "CO_MUNICIPIO",
    "NO_MUNICIPIO",
    "CO_UF",
    "SG_UF",
    "NO_UF",
    "CO_REGIAO",
    "NO_REGIAO",
    "IN_CAPITAL"
]

COLUNAS_FATO = [
    "NU_ANO_CENSO", "CO_IES", "CO_CURSO", "CO_CINE_ROTULO", "ID_LOCALIZACAO", "TP_DIMENSAO",
    "QT_ING", "QT_ING_FEM", "QT_ING_MASC", "QT_ING_BRANCA", "QT_ING_PRETA", "QT_ING_PARDA",
    "QT_ING_AMARELA", "QT_ING_INDIGENA", "QT_ING_CORND",
    "QT_MAT", "QT_MAT_FEM", "QT_MAT_MASC", "QT_MAT_BRANCA", "QT_MAT_PRETA", "QT_MAT_PARDA",
    "QT_MAT_AMARELA", "QT_MAT_INDIGENA", "QT_MAT_CORND",
    "QT_CONC", "QT_CONC_FEM", "QT_CONC_MASC", "QT_CONC_BRANCA", "QT_CONC_PRETA", "QT_CONC_PARDA",
    "QT_CONC_AMARELA", "QT_CONC_INDIGENA", "QT_CONC_CORND",
    "QT_SIT_TRANCADA", "QT_SIT_DESVINCULADO", "QT_SIT_TRANSFERIDO", "QT_SIT_FALECIDO",
    "QT_ING_DIURNO", "QT_ING_NOTURNO", "QT_MAT_DIURNO", "QT_MAT_NOTURNO", "QT_CONC_DIURNO", "QT_CONC_NOTURNO"
]

GRAO_FATO = ["NU_ANO_CENSO", "CO_CURSO", "TP_DIMENSAO", "ID_LOCALIZACAO"]

DIMENSOES = {
    "dim_ies": COLUNAS_IES,
    "dim_curso": COLUNAS_CURSO,
    "dim_cine": COLUNAS_CINE,
    "dim_localizacao": COLUNAS_LOCALIZACAO,
}
GRAO_CSV = ["NU_ANO_CENSO", "CO_CURSO", "TP_DIMENSAO", "CO_MUNICIPIO"]


def ler_normalizado(path, encoding, columns, normalize, key):
    seen = set()
    if path.suffix.lower() == ".gz":
        entrada = gzip.open(path, mode="rt", encoding=encoding, newline="")
    else:
        entrada = path.open(encoding=encoding, newline="")
    with entrada as stream:
        _, records = rows(stream, ";", columns)
        for line, record in records:
            try:
                cleaned = normalize(record)
                if cleaned is None:
                    raise ValueError("Registro fora do recorte esperado para a carga.")
                if any(isinstance(value, str) and "\x00" in value for value in cleaned.values()):
                    raise ValueError("Texto contém byte nulo.")
                identity = tuple(cleaned[name] for name in key)
                if identity in seen:
                    raise ValueError(f"Chave duplicada após normalização: {identity}.")
                seen.add(identity)
            except ValueError as error:
                raise ValueError(f"Linha {line}: {error}") from error
            yield cleaned
    if not seen:
        raise ValueError("O CSV não contém registros.")


def carregar_csv(path=CSV_PATH):
    dimensoes = {table: {} for table in DIMENSOES}
    fatos = []
    for record in ler_normalizado(path, "cp1252", CENSO_COLUMNS, normalize_censo, GRAO_CSV):
        uf = record["SG_UF"]
        if uf is not None and len(uf) > 2:
            raise ValueError("SG_UF deve ter no máximo dois caracteres.")
        for table, columns in DIMENSOES.items():
            values = tuple(record[col] for col in columns)
            key = values[0]
            if key is None:  # Município indisponível usa a localização reservada.
                continue
            old = dimensoes[table].setdefault(key, values)
            if old != values:
                raise ValueError(f"Valores divergentes para a chave {key!r} em {table}.")
        record["ID_LOCALIZACAO"] = record["CO_MUNICIPIO"]
        fatos.append(tuple(record[col] for col in COLUNAS_FATO))
    return dimensoes, fatos


def upsert(cursor, table, columns, key, records):
    if not records:
        return
    updates = ", ".join(f"{col} = EXCLUDED.{col}" for col in columns if col not in key)
    statement = (
        f"INSERT INTO public.{table} ({', '.join(columns)}) VALUES %s "
        f"ON CONFLICT ({', '.join(key)}) DO UPDATE SET {updates}"
    )
    execute_values(cursor, statement, records, page_size=BATCH_SIZE)


def gravar_censo(conn, dados):
    dimensoes, fatos = dados
    location_index = COLUNAS_FATO.index("ID_LOCALIZACAO")
    with conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT id_localizacao FROM public.dim_localizacao
            WHERE co_municipio IS NULL AND no_municipio = 'SEM MUNICÍPIO'
        """)
        sem_municipio = cursor.fetchall()
        if len(sem_municipio) != 1:
            raise ValueError("O esquema deve conter exatamente uma localização SEM MUNICÍPIO.")
        for table, columns in DIMENSOES.items():
            values = dimensoes[table]
            upsert(cursor, table, columns, columns[:1], [values[k] for k in sorted(values)])

        cursor.execute("""
            SELECT co_municipio, id_localizacao FROM public.dim_localizacao
            WHERE co_municipio = ANY(%s)
        """, (list(dimensoes["dim_localizacao"]),))
        locations = dict(cursor.fetchall())
        locations[None] = sem_municipio[0][0]
        rows_to_write = [
            row[:location_index] + (locations[row[location_index]],) + row[location_index + 1:]
            for row in fatos
        ]
        key_positions = [COLUNAS_FATO.index(col) for col in GRAO_FATO]
        rows_to_write.sort(key=lambda row: tuple(row[index] for index in key_positions))
        upsert(cursor, "fato_censo_curso", COLUNAS_FATO, GRAO_FATO, rows_to_write)
    return len(fatos)


def conectar():
    load_dotenv(ROOT / ".env")
    variables = ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"]
    missing = [name for name in variables if not os.getenv(name)]
    if missing:
        raise ValueError("Configure no ambiente: " + ", ".join(missing))
    return psycopg2.connect(
        host=os.environ["DB_HOST"], port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"], user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"], sslmode=os.getenv("DB_SSLMODE", "require"),
        connect_timeout=10,
    )


def executar_carga(label, path, preparar, gravar):
    try:
        dados = preparar(path)
        with closing(conectar()) as conn:
            total = gravar(conn, dados)
    except psycopg2.Error as error:
        # A mensagem do driver pode conter dados da conexão. Registre apenas o código.
        raise SystemExit(f"{label}: falha PostgreSQL ({type(error).__name__}, "
                         f"SQLSTATE {error.pgcode or 'indisponível'}). Carga não confirmada.") from None
    except (gzip.BadGzipFile, EOFError, zlib.error):
        raise SystemExit(f"{label}: arquivo gzip inválido, corrompido ou truncado.") from None
    except (ValueError, OSError, csv.Error) as error:
        raise SystemExit(f"{label}: {error}") from None
    print(f"{label}: {total} linhas processadas em transação confirmada.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=CSV_PATH, help="Arquivo processado .csv ou .csv.gz.")
    executar_carga("Censo", parser.parse_args().csv, carregar_csv, gravar_censo)


if __name__ == "__main__":
    main()
