"""Mede as consultas exportadas do Grafana no PostgreSQL descartável."""
import os
import re
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from statistics import median
from time import perf_counter

import psycopg2

from grafana.gerar_dashboard import VARIABLES, dashboard, options_query

VARIABLE = re.compile(r"\$\{([a-z]+):sqlstring\}")


def medir_visitante(opcoes):
    inicio = perf_counter()
    resultados = []
    with closing(psycopg2.connect("", options="-c statement_timeout=15000")) as connection:
        connection.set_session(readonly=True)
        with connection.cursor() as cur:
            def medir(nome, query):
                cur.execute("EXPLAIN (ANALYZE, BUFFERS, TIMING OFF, FORMAT JSON) " + query)
                plano = cur.fetchone()[0][0]
                resultados.append((nome, plano["Execution Time"],
                                   plano["Plan"].get("Shared Hit Blocks", 0),
                                   plano["Plan"].get("Shared Read Blocks", 0)))

            for _, nome, coluna in VARIABLES:
                medir(nome, options_query(coluna))

            def interpolar(match):
                return ", ".join(cur.mogrify("%s", (v,)).decode() for v in opcoes[match[1]])

            for painel in dashboard()["panels"]:
                for target in painel.get("targets", ()):
                    medir(painel["title"], VARIABLE.sub(interpolar, target["rawSql"]))
    return (perf_counter() - inicio) * 1000, resultados


def main():
    if not os.environ.get("PGHOST", "").startswith("/") or os.environ.get("PGHOSTADDR"):
        raise SystemExit("Use o socket Unix de um PostgreSQL local e descartável.")
    opcoes = {"enade": ["Todos"]}
    with closing(psycopg2.connect("", options="-c statement_timeout=15000")) as connection:
        connection.set_session(readonly=True)
        with connection.cursor() as cur:
            for chave, _, coluna in VARIABLES:
                cur.execute(options_query(coluna))
                opcoes[chave] = [row[0] for row in cur.fetchall()]
    tempo, medicao = medir_visitante(opcoes)
    for nome, ms, hits, reads in medicao:
        print(f"{nome} | {ms:.1f} ms | shared hit {hits} | shared read {reads}")
    print(f"Mediana por consulta, um visitante: {median(row[1] for row in medicao):.1f} ms")
    print(f"Sequência local, um visitante: {tempo:.0f} ms")
    with ThreadPoolExecutor(max_workers=3) as pool:
        simultaneos = list(pool.map(lambda _: medir_visitante(opcoes), range(3)))
    print("Três visitantes, sequência por visitante: "
          + ", ".join(f"{tempo:.0f} ms" for tempo, _ in simultaneos))
    print(f"Mediana por consulta, três visitantes: "
          f"{median(row[1] for _, rows in simultaneos for row in rows):.1f} ms")


if __name__ == "__main__":
    main()
