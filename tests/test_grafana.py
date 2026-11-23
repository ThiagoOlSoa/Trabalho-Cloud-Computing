"""Valida o dashboard gerado e, opcionalmente, todas as consultas num banco local."""
import json
import os
import re
import unittest
from pathlib import Path

from grafana import gerar_dashboard as grafana

VARIABLE = re.compile(r"\$\{([a-z]+):sqlstring\}")
SOCKET = os.getenv("ETL_TEST_PG_SOCKET")
DATABASE = os.getenv("ETL_TEST_DB_NAME")
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

    def test_read_only_queries_and_fixed_interpolation_format(self):
        for panel in grafana.dashboard()["panels"]:
            for target in panel.get("targets", []):
                with self.subTest(panel=panel["title"]):
                    sql = target["rawSql"]
                    self.assertEqual(set(VARIABLE.findall(sql)), FILTERS)
                    self.assertNotIn('${', VARIABLE.sub("", sql))
                    self.assertNotRegex(sql, r";|(?i:\b(?:insert|update|delete|truncate|drop|alter|grant)\b)")
                    self.assertTrue(sql.startswith("WITH cursos AS ("))
                    self.assertEqual(target["datasource"], grafana.DATASOURCE)


@unittest.skipUnless(SOCKET and Path(SOCKET).is_dir() and DATABASE,
                     "Requer socket Unix e banco PostgreSQL descartável com os CSVs completos")
class GrafanaPostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        import psycopg2
        cls.db = psycopg2.connect(host=SOCKET, dbname=DATABASE,
                                  user=os.getenv("ETL_TEST_PG_USER", "agent"), sslmode="disable")
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

    def query(self, sql, **selections):
        # Espelha :sqlstring do Grafana. O servidor usa standard_conforming_strings=on.
        values = self.options | selections
        rendered = VARIABLE.sub(
            lambda match: ", ".join("'" + value.replace("'", "''") + "'"
                                    for value in values[match[1]]),
            sql,
        )
        with self.db.cursor() as cur:
            cur.execute(rendered)
            return cur.fetchall()

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
            "no_cine_rotulo": "'Fixture'", "tp_modalidade_ensino": "2",
            "co_modalidade": "0", "sg_uf": "'SP'", "possui_enade_2023": "true",
            "qt_mat": "10 * n", "qt_ing": "0", "qt_conc": "0",
            "qt_mat_fem_censo": "CASE WHEN n = 1 THEN 10 ELSE 0 END",
            "qt_mat_preta_censo": "0", "qt_mat_parda_censo": "0", "qt_mat_cornd_censo": "10 * n",
            "qt_sit_trancada": "0", "qt_sit_desvinculado": "0", "qt_sit_transferido": "0",
            "qt_sit_falecido": "0", "media_nt_ger": "(CASE WHEN n = 1 THEN 0 ELSE 100 END)::numeric",
            "qt_notas_validas": "n",
        }
        def fixture(**changes):
            columns = ", ".join(f"{expr} AS {name}" for name, expr in (fields | changes).items())
            sql = grafana.query("indicadores").replace(
                "public.vw_observatorio_censo_enade", f"(SELECT {columns} FROM (VALUES (1), (2)) t(n))",
            )
            return self.query(sql, cine=["Fixture"])[0]

        row = fixture()
        self.assertEqual(row[:6], (2, 30, 0, 0, 2, 100))
        self.assertEqual(float(row[6]), 33.3)
        self.assertIsNone(row[7])
        self.assertEqual(row[8], 0)
        self.assertEqual(float(row[9]), 66.7)
        self.assertEqual(fixture(qt_notas_validas="0")[4], 2)
        self.assertIsNone(fixture(qt_notas_validas="0")[9])
        self.assertIsNone(fixture(qt_mat_fem_censo="CASE WHEN n = 1 THEN NULL ELSE 0 END")[6])
