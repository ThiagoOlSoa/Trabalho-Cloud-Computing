"""Valida e carrega o ENADE 2023 em uma única transação PostgreSQL."""

import argparse
from decimal import Decimal
from pathlib import Path

if __package__:
    from .load import ROOT, executar_carga, ler_normalizado, upsert
    from .transform import ENADE_GRADES, integer, normalize_enade
else:
    from load import ROOT, executar_carga, ler_normalizado, upsert
    from transform import ENADE_GRADES, integer, normalize_enade

CSV_PATH = ROOT / "data" / "processed" / "enade_2023_area1.csv"

COLUNAS = {
    "NU_ANO": "nu_ano",
    "CO_CURSO": "co_curso",
    "CO_IES": "co_ies_enade",
    "CO_GRUPO": "co_grupo",
    "CO_MODALIDADE": "co_modalidade",
    "CO_UF_CURSO": "co_uf_curso",
    "CO_MUNIC_CURSO": "co_munic_curso",
    "CO_REGIAO_CURSO": "co_regiao_curso",
    "QT_PARTICIPANTES": "qt_participantes",
    "QT_NOTAS_VALIDAS": "qt_notas_validas",
    "MEDIA_NT_GER": "media_nt_ger",
    "MEDIA_NT_FG": "media_nt_fg",
    "MEDIA_NT_CE": "media_nt_ce",
    "QT_SEXO_F": "qt_sexo_f",
    "QT_SEXO_M": "qt_sexo_m",
    "QT_RACA_BRANCA": "qt_raca_branca",
    "QT_RACA_PRETA": "qt_raca_preta",
    "QT_RACA_PARDA": "qt_raca_parda",
    "QT_RACA_AMARELA": "qt_raca_amarela",
    "QT_RACA_INDIGENA": "qt_raca_indigena",
    "QT_RACA_NAO_DECLARA": "qt_raca_nao_declara",
    "QT_RACA_SEM_RESPOSTA": "qt_raca_sem_resposta",
}


def normalizar_registro(record):
    course = integer(record, "CO_CURSO", minimum=1)
    cleaned = normalize_enade(record, {course})
    if cleaned is None:
        return None
    for name in ENADE_GRADES:
        value = cleaned[name]
        cleaned[name] = Decimal(value) if value is not None else None
    ies = cleaned["CO_IES"]
    cleaned["CO_IES"] = str(ies) if ies is not None else None
    return cleaned


def carregar_csv(path=CSV_PATH):
    key = ["NU_ANO", "CO_CURSO"]
    try:
        records = list(ler_normalizado(path, "utf-8-sig", COLUNAS, normalizar_registro, key))
    except UnicodeDecodeError:
        records = list(ler_normalizado(path, "cp1252", COLUNAS, normalizar_registro, key))
    return sorted((tuple(record[name] for name in COLUNAS) for record in records),
                  key=lambda row: row[:2])


def gravar_enade(conn, dados):
    courses = {row[1] for row in dados}
    with conn, conn.cursor() as cursor:
        cursor.execute("""
            SELECT co_curso FROM public.dim_curso WHERE co_curso = ANY(%s)
            FOR KEY SHARE
        """, (sorted(courses),))
        missing = courses - {row[0] for row in cursor.fetchall()}
        if missing:
            sample = ", ".join(map(str, sorted(missing)[:10]))
            raise ValueError(f"{len(missing)} cursos do ENADE ausentes do Censo. Exemplos: {sample}.")
        upsert(cursor, "fato_enade_curso", list(COLUNAS.values()), ["nu_ano", "co_curso"], dados)
    return len(dados)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--csv", type=Path, default=CSV_PATH)
    executar_carga("ENADE", parser.parse_args().csv, carregar_csv, gravar_enade)


if __name__ == "__main__":
    main()
