"""Confere o contrato analítico e o acesso somente leitura no legado local."""
import os
import re
import unittest
from pathlib import Path

import psycopg2

from scripts.validar_indicadores import REFERENCIAS, SQL_DIR, consulta_indicadores

SOCKET = os.getenv("ETL_TEST_PG_SOCKET")
DATABASE = os.getenv("ETL_TEST_LEGACY_DB_NAME")
LEGACY_USER = os.getenv("ETL_TEST_LEGACY_USER")
CURSOS = (SQL_DIR / "cursos.sql").read_text(encoding="utf-8")
TABLES = {"fato_censo_curso", "fato_enade_curso", "dim_curso", "dim_ies",
          "dim_cine", "dim_localizacao"}


class ConsultaTest(unittest.TestCase):
    def test_consulta_direta_e_somente_leitura(self):
        consulta = consulta_indicadores()
        self.assertEqual(set(re.findall(r"\bpublic\.(\w+)", consulta)), TABLES)
        self.assertNotIn("vw_observatorio_censo_enade", consulta)
        self.assertNotRegex(consulta, r";|(?i:\b(?:insert|update|delete|truncate|drop|alter|grant)\b)")


@unittest.skipUnless(SOCKET and Path(SOCKET).is_dir() and DATABASE,
                     "Requer PostgreSQL legado local e descartável")
class ConsultaPostgresTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = psycopg2.connect(
            host=SOCKET, dbname=DATABASE, sslmode="disable",
            user=LEGACY_USER or os.getenv("ETL_TEST_PG_USER", "agent"),
        )
        cls.addClassCleanup(cls.db.close)
        cls.db.set_session(readonly=True)

    def query(self, consulta):
        with self.db.cursor() as cur:
            cur.execute(consulta)
            return cur.fetchall()

    def test_dez_indicadores_sem_filtros(self):
        with self.db.cursor() as cur:
            cur.execute(consulta_indicadores())
            row = cur.fetchone()
            self.assertEqual(dict(zip((col.name for col in cur.description), row, strict=True)),
                             REFERENCIAS | {"chaves_invalidas": 0})

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
            cur.execute(CURSOS + """
                SELECT count(*), count(DISTINCT co_curso),
                       count(*) FILTER (WHERE possui_enade_2023),
                       count(*) FILTER (WHERE possui_enade_2023 IS FALSE)
                FROM cursos
            """)
            self.assertEqual(cur.fetchone(), (7078, 7078, 1665, 5413))
            cur.execute(CURSOS + """
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
        self.assertEqual(self.query(consulta_indicadores())[0][0], 7078)

    @unittest.skipUnless(LEGACY_USER, "Requer usuário de leitura da fixture local")
    def test_preflight_cobre_colunas_da_consulta(self):
        metadados, chaves = (SQL_DIR / "preflight_painel.sql").read_text(encoding="utf-8").split(";", 1)
        linhas = self.query(metadados)

        # Alias e escopo dos acessos físicos. O alias e do JOIN final referencia a CTE.
        censo, enade, final = re.split(r", (?:enade_normalizado|cursos) AS ", CURSOS)
        esperadas = set()
        for trecho, aliases in (
            (censo, {"f": "fato_censo_curso"}),
            (enade, {"e": "fato_enade_curso"}),
            (final, {"dc": "dim_curso", "ies": "dim_ies", "cine": "dim_cine", "loc": "dim_localizacao"}),
        ):
            esperadas.update((aliases[alias], coluna) for alias, coluna in
                             re.findall(r"\b(\w+)\.(\w+)", trecho) if alias in aliases)
        self.assertEqual({(tabela, coluna) for tabela, coluna, *_ in linhas}, esperadas)
        self.assertEqual(len(linhas), len(esperadas))
        self.assertTrue(all(tipo_ok and pode_ler and not pode_escrever
                            for _, _, _, tipo_ok, pode_ler, pode_escrever in linhas))
        self.assertEqual(self.query(chaves), [(1665, 1665, 1665)])

    def test_ponderacao_lacunas_e_nota_zero_com_fixture_sintetica(self):
        # Sem escrita: substitui a consulta por dois cursos sintéticos em uma subconsulta.
        fields = {
            "co_curso": "n",
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
            sql = consulta_indicadores().replace(
                CURSOS, f"WITH cursos AS (SELECT {columns} FROM (VALUES (1), (2)) t(n))",
                1,
            )
            return self.query(sql)[0]

        row = fixture()
        self.assertEqual(row[:6], (2, 30, 0, 0, 2, 100))
        self.assertEqual(float(row[6]), 33.3)
        self.assertIsNone(row[7])
        self.assertEqual(row[8], 0)
        self.assertEqual(float(row[9]), 66.7)
        self.assertEqual(fixture(peso_nota="0")[4], 2)
        self.assertIsNone(fixture(peso_nota="0")[9])
        self.assertIsNone(fixture(qt_mat_fem_censo="CASE WHEN n = 1 THEN NULL ELSE 0 END")[6])
        self.assertEqual(fixture(co_curso="1")[-1], 1)
        self.assertEqual(fixture(co_curso="NULL")[-1], 2)
