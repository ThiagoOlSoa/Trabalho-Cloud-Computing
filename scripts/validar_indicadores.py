"""Confere os indicadores do Observatório sem filtros, usando parâmetros PG* do libpq."""
import os
import sys
from decimal import Decimal
from pathlib import Path

import psycopg2

SQL_DIR = Path(__file__).resolve().parents[1] / "sql"


def consulta_indicadores():
    cursos = (SQL_DIR / "cursos.sql").read_text(encoding="utf-8")
    indicadores = (SQL_DIR / "indicadores_painel.sql").read_text(encoding="utf-8")
    return cursos + "\n" + indicadores

REFERENCIAS = {
    "cursos": 7078,
    "matriculas": 1269093,
    "ingressantes": 673375,
    "concluintes": 153760,
    "cursos_enade": 1665,
    "cobertura": Decimal("23.5"),
    "feminino": Decimal("20.2"),
    "preta_parda": Decimal("41.2"),
    "desvinculacao": Decimal("21.7"),
    "media_enade": Decimal("41.8"),
}


def comparar(resultados):
    divergencias = 0
    for nome, esperado in REFERENCIAS.items():
        encontrado = resultados[nome]
        igual = encontrado == esperado
        divergencias += not igual
        status = "OK" if igual else "DIVERGÊNCIA"
        print(f"{status} | {nome} | esperado {esperado} | encontrado {encontrado}")
    print(f"{len(REFERENCIAS)} indicadores conferidos, {divergencias} divergências.")
    return int(divergencias > 0)


def main():
    host = os.environ.get("PGHOST")
    database = os.environ.get("PGDATABASE")
    if not host or not database:
        print("Defina PGHOST e PGDATABASE de forma explícita.", file=sys.stderr)
        return 2
    local_socket = host.startswith("/") and "," not in host and not os.environ.get("PGHOSTADDR")
    if not local_socket and os.environ.get("PGSSLMODE") != "verify-full":
        print("Para um host de rede, configure PGSSLMODE=verify-full e a CA.", file=sys.stderr)
        return 2

    try:
        connection = psycopg2.connect(
            host=host, dbname=database, sslmode="disable" if local_socket else "verify-full",
            connect_timeout=10, options="-c statement_timeout=15000",
        )
        try:
            connection.set_session(readonly=True)
            with connection.cursor() as cursor:
                cursor.execute(consulta_indicadores())
                row = cursor.fetchone()
                results = dict(zip((column.name for column in cursor.description), row, strict=True))
        finally:
            connection.close()
    except psycopg2.Error as exc:
        code = f" | SQLSTATE {exc.pgcode}" if exc.pgcode else ""
        print(f"Falha na conexão ou consulta | {type(exc).__name__}{code}", file=sys.stderr)
        return 2
    if results.pop("chaves_invalidas"):
        print("Recorte PostgreSQL com chaves de curso nulas ou repetidas.", file=sys.stderr)
        return 2
    return comparar(results)


if __name__ == "__main__":
    sys.exit(main())
