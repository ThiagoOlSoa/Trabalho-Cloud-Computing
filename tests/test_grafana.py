"""Valida o dashboard gerado e, opcionalmente, todas as consultas num banco local."""
import json
import os
import re
import unittest
from pathlib import Path

from grafana import gerar_dashboard as grafana

VARIABLE = re.compile(r"\$\{([a-z]+):sqlstring\}")
SOCKET = os.getenv("ETL_TEST_PG_SOCKET")
DATABASE = os.getenv("GRAFANA_TEST_LEGACY_DB_NAME")
BASELINE_DB = os.getenv("ETL_TEST_DB_NAME")
LEGACY_USER = os.getenv("GRAFANA_TEST_LEGACY_USER")
BASELINE_SQL = Path(__file__).with_name("fixtures") / "grafana_referencia_7a.sql"
TABLES = {"fato_censo_curso", "fato_enade_curso", "dim_curso", "dim_ies",
          "dim_cine", "dim_localizacao"}
REFERENCE = (7078, 1269093, 673375, 153760, 1665, 23.5, 20.2, 41.2, 21.7, 41.8)
FILTERS = {name for name, _, _ in grafana.VARIABLES} | {"enade"}


class GrafanaJsonTest(unittest.TestCase):
    def test_export_matches_sql_and_plugin(self):
        dashboard = json.loads(grafana.OUTPUT.read_text(encoding="utf-8"))
        self.assertEqual(dashboard, grafana.dashboard())
        self.assertEqual(dashboard["__inputs"][0]["pluginId"], "grafana-postgresql-datasource")
        self.assertEqual({variable["name"] for variable in dashboard["templating"]["list"]}, FILTERS)
        self.assertEqual(len({panel["id"] for panel in dashboard["panels"]}), len(dashboard["panels"]))
        self.assertEqual(dashboard["refresh"], "")

    def test_all_panels_and_query_variables_use_only_tables(self):
        dashboard = grafana.dashboard()
        sources = [target["rawSql"] for panel in dashboard["panels"]
                   for target in panel.get("targets", [])]
        sources.extend(variable["query"] for variable in dashboard["templating"]["list"]
                       if variable["type"] == "query")
        for query in sources:
            self.assertEqual(set(re.findall(r"\bpublic\.(\w+)", query)), TABLES)
            self.assertNotIn("vw_observatorio_censo_enade", query)

    def test_read_only_queries_and_fixed_interpolation_format(self):
        for panel in grafana.dashboard()["panels"]:
            for target in panel.get("targets", []):
                with self.subTest(panel=panel["title"]):
                    sql = target["rawSql"]
                    self.assertEqual(set(VARIABLE.findall(sql)), FILTERS)
                    self.assertNotIn('${', VARIABLE.sub("", sql))
                    self.assertNotRegex(sql, r";|(?i:\b(?:insert|update|delete|truncate|drop|alter|grant)\b)")
                    self.assertTrue(sql.startswith("WITH censo_curso AS ("))
                    self.assertEqual(target["datasource"], grafana.DATASOURCE)


@unittest.skipUnless(SOCKET and Path(SOCKET).is_dir() and DATABASE,
                     "Requer socket Unix e banco legado local e descartável com os CSVs completos")
class GrafanaPostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg2
        cls.db = psycopg2.connect(host=SOCKET, dbname=DATABASE,
                                  user=LEGACY_USER or os.getenv("ETL_TEST_PG_USER", "agent"), sslmode="disable")
        cls.db.set_session(readonly=True)
        with cls.db.cursor() as cur:
            cur.execute("SHOW standard_conforming_strings")
            if cur.fetchone()[0] != "on":
                raise AssertionError("O PostgreSQL precisa tratar barras como literais em strings SQL.")
            cls.options = {"enade": ["Todos"]}
            for name, _, column in grafana.VARIABLES:
                cur.execute(grafana.options_query(column))
                cls.options[name] = [row[0] for row in cur.fetchall()]

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def query(self, sql, connection=None, **selections):
        # Espelha :sqlstring do Grafana. O servidor usa standard_conforming_strings=on.
        values = self.options | selections
        rendered = VARIABLE.sub(
            lambda match: ", ".join("'" + value.replace("'", "''") + "'"
                                    for value in values[match[1]]),
            sql,
        )
        with (connection or self.db).cursor() as cur:
            cur.execute(rendered)
            return cur.fetchall()

    def test_contrato_do_legado_e_granularidade_direta(self):
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT table_name, data_type FROM information_schema.columns
                WHERE table_schema = 'public' AND column_name = 'co_curso'
                  AND table_name IN ('fato_censo_curso', 'fato_enade_curso')
            """)
            self.assertEqual(dict(cur.fetchall()), {
                "fato_censo_curso": "integer", "fato_enade_curso": "character varying",
            })
            cur.execute(grafana.scope(False) + """
                SELECT count(*), count(DISTINCT co_curso),
                       count(*) FILTER (WHERE possui_enade_2023),
                       count(*) FILTER (WHERE possui_enade_2023 IS FALSE)
                FROM cursos
            """)
            self.assertEqual(cur.fetchone(), (7078, 7078, 1665, 5413))
            cur.execute(grafana.scope(False) + """
                SELECT pg_typeof(grau_academico)::text, pg_typeof(modalidade_ensino)::text,
                       pg_typeof(rede_ensino)::text, pg_typeof(uf_oferta::text)::text,
                       pg_typeof(area_cine::text)::text, pg_typeof(possui_enade_2023)::text,
                       pg_typeof(media_nt_ger)::text
                FROM cursos LIMIT 1
            """)
            self.assertEqual(cur.fetchone(), ("text",) * 5 + ("boolean", "numeric"))

    @unittest.skipUnless(LEGACY_USER, "Requer usuário de leitura da fixture local")
    def test_permissoes_minimas(self):
        with self.db.cursor() as cur:
            cur.execute("""
                SELECT has_table_privilege('public.vw_observatorio_censo_enade', 'SELECT'),
                       has_table_privilege('public.fato_censo_curso', 'INSERT'),
                       has_column_privilege('public.fato_censo_curso', 'qt_mat', 'SELECT'),
                       has_column_privilege('public.fato_censo_curso', 'qt_mat_masc', 'SELECT')
            """)
            self.assertEqual(cur.fetchone(), (False, False, True, False))
        self.assertEqual(self.query(grafana.query("indicadores"))[0][0], 7078)

    @unittest.skipUnless(BASELINE_DB, "Requer banco local de referência da Etapa 7A")
    def test_paridade_com_7a_em_paineis_e_listas(self):
        import psycopg2
        db = psycopg2.connect(host=SOCKET, dbname=BASELINE_DB,
                              user=os.getenv("ETL_TEST_PG_USER", "agent"), sslmode="disable")
        try:
            db.set_session(readonly=True)
            old_sql = BASELINE_SQL.read_text(encoding="utf-8").strip()
            for panel in grafana.dashboard()["panels"]:
                for target in panel.get("targets", []):
                    sql = target["rawSql"]
                    with self.subTest(panel=panel["title"]):
                        for filters in ({}, {"modalidade": ["EaD"], "enade": ["Com registro"]}):
                            self.assertEqual(
                                self.query(sql, **filters),
                                self.query(sql.replace(grafana.scope(False), old_sql, 1), connection=db, **filters),
                            )
            for name, _, column in grafana.VARIABLES:
                sql = grafana.options_query(column).replace(grafana.scope(False), old_sql, 1)
                self.assertEqual([row[0] for row in self.query(sql, connection=db)], self.options[name])
        finally:
            db.close()

    def test_referencia_integral(self):
        row, = self.query(grafana.query("indicadores"))
        self.assertEqual(tuple(map(float, row)), REFERENCE)
        main = grafana.dashboard()["panels"][2]["targets"][0]["rawSql"]
        self.assertEqual(self.query(main), [("41,2%", "21,7%", "41,8")])

    def test_filtros_individuais_combinados_e_geografia(self):
        counts = {}
        for name, values in {
            "grau": ["Tecnológico"], "modalidade": ["EaD"], "rede": ["Pública"],
            "uf": ["EaD · UF não atribuída"], "cine": self.options["cine"][:1],
            "enade": ["Com registro"],
        }.items():
            with self.subTest(name=name):
                row, = self.query(grafana.query("indicadores"), **{name: values})
                self.assertTrue(0 < row[0] < REFERENCE[0])
                counts[name] = row[0]
                if name == "enade":
                    self.assertEqual((row[0], row[4], row[5]), (1665, 1665, 100))
        self.assertEqual(counts["modalidade"], counts["uf"])
        state_count, = self.query(grafana.query("comparacoes", "por_modalidade"), uf=["SP"])
        self.assertEqual(state_count[0], "Presencial")
        self.assertEqual(
            self.query(grafana.query("indicadores"), modalidade=["Presencial"],
                       uf=["EaD · UF não atribuída"]),
            [(0, None, None, None, 0, None, None, None, None, None)],
        )
        self.assertEqual(self.query(grafana.query("indicadores"), cine=["Curso d'Água"])[0][0], 0)
        self.assertEqual(self.query(grafana.query("indicadores"), cine=[])[0][0], 0)

    def test_paineis_e_filtros_mesmo_recorte(self):
        for panel in grafana.dashboard()["panels"]:
            for target in panel.get("targets", []):
                with self.subTest(panel=panel["title"]):
                    self.assertTrue(self.query(target["rawSql"]))
                    self.query(target["rawSql"], grau=["Tecnológico"], modalidade=["EaD"],
                               rede=["Privada"], uf=["EaD · UF não atribuída"], enade=["Com registro"])
        populations = self.query(grafana.query("populacoes"))
        self.assertEqual([row[1] for row in populations], [673375, 1269093, 153760])
        self.assertEqual(tuple(map(float, populations[1][2:])), (20.2, 41.2))

    def test_ponderacao_lacunas_e_nota_zero_com_fixture_sintetica(self):
        # Sem escrita: substitui a view por dois cursos sintéticos em uma subconsulta.
        fields = {
            "grau_academico": "'Tecnológico'", "modalidade_ensino": "'EaD'", "rede_ensino": "'Privada'",
            "area_cine": "'Fixture'", "uf_oferta": "'EaD · UF não atribuída'", "possui_enade_2023": "true",
            "qt_mat": "10 * n", "qt_ing": "0", "qt_conc": "0",
            "qt_mat_fem_censo": "CASE WHEN n = 1 THEN 10 ELSE 0 END",
            "qt_mat_preta_censo": "0", "qt_mat_parda_censo": "0", "qt_mat_cornd_censo": "10 * n",
            "total_situacoes": "10 * n", "qt_sit_desvinculado": "0",
            "media_nt_ger": "(CASE WHEN n = 1 THEN 0 ELSE 100 END)::numeric",
            "peso_nota": "n",
        }

        def fixture(**changes):
            columns = ", ".join(f"{expr} AS {name}" for name, expr in (fields | changes).items())
            sql = grafana.query("indicadores").replace(
                grafana.scope(False), f"WITH cursos AS (SELECT {columns} FROM (VALUES (1), (2)) t(n))",
                1,
            )
            return self.query(sql, cine=["Fixture"])[0]

        row = fixture()
        self.assertEqual(row[:6], (2, 30, 0, 0, 2, 100))
        self.assertEqual(float(row[6]), 33.3)
        self.assertIsNone(row[7])
        self.assertEqual(row[8], 0)
        self.assertEqual(float(row[9]), 66.7)
        self.assertEqual(fixture(peso_nota="0")[4], 2)
        self.assertIsNone(fixture(peso_nota="0")[9])
        self.assertIsNone(fixture(qt_mat_fem_censo="CASE WHEN n = 1 THEN NULL ELSE 0 END")[6])
