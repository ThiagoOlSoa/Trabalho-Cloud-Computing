"""Testes do Streamlit com CSVs sintéticos e comparação opcional com PostgreSQL local."""

import json
import os
import tempfile
import unittest
from contextlib import closing
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import streamlit as st
from streamlit.testing.v1 import AppTest

from src.transform import CENSO_COLUMNS, ENADE_COLUMNS
from test_etl import ROOT, censo, enade, write_csv


APP = ROOT / "app/app.py"
CAPTURE = """
st.session_state["indicadores_teste"] = kpis
st.session_state["dados_teste"] = df_f
st.session_state["agrupamentos_teste"] = (grau_df, df_funil, transp)
st.session_state["matriz_teste"] = exibir_matriz if not perfil.empty else None
"""


def app_de_teste(root):
    st.cache_data.clear()
    path = root / "app/app.py"
    path.parent.mkdir()
    path.write_text(APP.read_text(encoding="utf-8") + CAPTURE, encoding="utf-8")
    return AppTest.from_file(str(path), default_timeout=45)


def selecionar(app, label, values):
    next(widget for widget in app.sidebar.multiselect if widget.label == label).set_value(values)


class TestIndicadores(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        root = Path(tmp.name)
        data = root / "data/processed"
        data.mkdir(parents=True)
        write_csv(data / "censo_2024_area1.csv", CENSO_COLUMNS, [
            censo(CO_CURSO="11", TP_DIMENSAO="1", TP_MODALIDADE_ENSINO="1",
                  SG_UF="SP", TP_REDE="1", QT_MAT="10", QT_MAT_FEM="10", QT_MAT_PRETA="10",
                  QT_SIT_DESVINCULADO="5", QT_ING="2", QT_ING_FEM="2", QT_ING_PRETA="2",
                  QT_CONC="1", QT_CONC_FEM="1", QT_CONC_PRETA="1", NO_CINE_ROTULO="Exatas"),
            censo(CO_CURSO="12", TP_DIMENSAO="2", SG_UF="SP", TP_REDE="2",
                  QT_MAT="40", QT_MAT_FEM="20", QT_MAT_PRETA="10", QT_MAT_CORND="10",
                  NO_CINE_ROTULO="Exatas"),
            censo(CO_CURSO="12", TP_DIMENSAO="2", SG_UF="BA", TP_REDE="2",
                  QT_MAT="50", QT_MAT_FEM="25", QT_MAT_PARDA="15", QT_MAT_CORND="10",
                  NO_CINE_ROTULO="Exatas"),
            censo(CO_CURSO="13", TP_DIMENSAO="2", TP_REDE="2", TP_GRAU_ACADEMICO="3",
                  NO_CINE_ROTULO="Base zero"),
            censo(CO_CURSO="14", TP_DIMENSAO="1", TP_MODALIDADE_ENSINO="1",
                  TP_REDE="1", SG_UF="BA", NO_CINE_ROTULO="Incompleto", QT_MAT=""),
        ], encoding="cp1252")
        write_csv(data / "enade_2023_area1.csv", ENADE_COLUMNS, [
            enade(CO_CURSO="11", CO_MODALIDADE="1", QT_NOTAS_VALIDAS="2", MEDIA_NT_GER="80"),
            enade(CO_CURSO="12", CO_UF_CURSO="35", QT_NOTAS_VALIDAS="8", MEDIA_NT_GER="20"),
            enade(CO_CURSO="13", CO_UF_CURSO="29", QT_NOTAS_VALIDAS="50", MEDIA_NT_GER=""),
        ])
        env = patch.dict(os.environ, {"DB_HOST": ""})
        env.start()
        self.addCleanup(env.stop)
        self.app = app_de_teste(root).run()
        self.assertFalse(self.app.exception, self.app.exception)

    def test_metricas_na_selecao_e_ponderacao(self):
        selecionar(self.app, "Área CINE", ["Exatas", "Base zero"])
        self.app.run()
        self.assertFalse(self.app.exception, self.app.exception)
        kpis = self.app.session_state["indicadores_teste"]
        self.assertEqual(len(self.app.metric), 6)
        self.assertEqual(kpis["cursos"], 3)
        self.assertEqual(kpis["matriculas"], 100)
        self.assertEqual(kpis["feminino"], 55)
        self.assertAlmostEqual(kpis["preta_parda"], 100 * 35 / 80)
        self.assertAlmostEqual(kpis["desvinculacao"], 100 * 5 / 105)
        self.assertEqual(kpis["media_enade"], 32)
        self.assertEqual(kpis["cobertura"], 100)
        _, composicao, _ = self.app.session_state["agrupamentos_teste"]
        self.assertEqual(list(composicao["Total"]), [2, 100, 1])
        matriz = self.app.session_state["matriz_teste"]
        self.assertEqual(list(matriz["Cursos"]), [1])
        self.assertEqual(list(matriz["Nota ENADE Média"]), [20])

    def test_ausencia_e_zero_com_filtros(self):
        self.assertTrue(pd.isna(self.app.session_state["indicadores_teste"]["matriculas"]))
        selecionar(self.app, "Área CINE", ["Base zero"])
        self.app.run()
        self.assertFalse(self.app.exception, self.app.exception)
        kpis = self.app.session_state["indicadores_teste"]
        self.assertEqual(kpis["matriculas"], 0)
        for metric in ("feminino", "preta_parda", "desvinculacao", "media_enade"):
            self.assertTrue(pd.isna(kpis[metric]), metric)
        self.assertEqual(self.app.metric[2].value, "—")
        self.assertEqual(self.app.metric[1].value, "0")
        self.assertEqual(self.app.metric[5].value, "—")
        self.assertIn("Sem notas válidas", [item.value for item in self.app.caption])
        selecionar(self.app, "Área CINE", [])
        self.app.run()
        self.assertIn("Nenhum curso", self.app.warning[0].value)

    def test_uf_modalidade_rede_grau_cine_e_cobertura(self):
        selecionar(self.app, "UF de oferta (presencial)", ["SP"])
        self.app.run()
        self.assertEqual(list(self.app.session_state["dados_teste"].co_curso), [11])
        selecionar(self.app, "UF de oferta (presencial)", ["EaD · UF não atribuída"])
        selecionar(self.app, "Modalidade", ["EaD"])
        selecionar(self.app, "Rede de Ensino", ["Privada"])
        selecionar(self.app, "Grau Acadêmico", ["Bacharelado"])
        selecionar(self.app, "Área CINE", ["Exatas"])
        self.app.sidebar.checkbox[1].check().run()
        self.assertFalse(self.app.exception, self.app.exception)
        self.assertEqual(list(self.app.session_state["dados_teste"].co_curso), [12])
        self.assertEqual(self.app.session_state["indicadores_teste"]["matriculas"], 90)
        self.assertTrue(any("EaD · UF não atribuída" in item.value and "Somente cursos" in item.value
                            for item in self.app.caption))


    def test_cartoes_ajuda_e_orientacao_metodologica(self):
        self.assertEqual(len(self.app.metric), 6)
        self.assertTrue(all(metric.proto.help for metric in self.app.metric))
        self.assertEqual([tab.label for tab in self.app.tabs], [
            "Panorama", "Perfis dos cursos", "Qualidade",
        ])
        chart = json.loads(self.app.get("plotly_chart")[0].proto.spec)
        self.assertEqual([series["name"] for series in chart["data"]], [
            "Feminino", "Preta/parda · declaradas", "Raça/cor não informada",
        ])
        self.assertTrue(any("Cobertura ENADE 2023" in item.value for item in self.app.caption))
        self.assertTrue(any("Como interpretar os indicadores" == item.label
                            for item in self.app.expander))


CSV_DIR = os.getenv("ETL_TEST_CSV_DIR")
SOCKET = os.getenv("ETL_TEST_PG_SOCKET")
DB_NAME = os.getenv("ETL_TEST_DB_NAME")


@unittest.skipUnless(CSV_DIR and SOCKET and Path(SOCKET).is_dir() and DB_NAME,
                     "Requer os CSVs completos e um PostgreSQL descartável com a Etapa 4B carregada.")
class TestParidadePostgres(unittest.TestCase):
    def test_paridade_fontes_filtros_agrupamentos_e_sql(self):
        import psycopg2

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "data/processed").symlink_to(Path(CSV_DIR).resolve(), target_is_directory=True)
            postgres_env = {"DB_HOST": SOCKET, "DB_PORT": "5432", "DB_NAME": DB_NAME,
                            "DB_USER": os.getenv("ETL_TEST_PG_USER", "agent"),
                            "DB_PASSWORD": "", "DB_SSLMODE": "disable"}
            runs = []
            for host in ("", SOCKET):
                st.cache_data.clear()
                with patch.dict(os.environ, {**postgres_env, "DB_HOST": host}):
                    app = app_de_teste(root) if not runs else AppTest.from_file(
                        str(root / "app/app.py"), default_timeout=45
                    )
                    app.run()
                    self.assertFalse(app.exception, app.exception)
                    self.assertIn("PostgreSQL" if host else "CSVs", app.sidebar.caption[0].value)
                    full = tuple(app.session_state[name] for name in (
                        "indicadores_teste", "agrupamentos_teste", "matriz_teste", "dados_teste",
                    ))
                    options = [list(widget.options) for widget in app.sidebar.multiselect]
                    filters = {"Modalidade": ["EaD"], "UF de oferta (presencial)": ["EaD · UF não atribuída"],
                               "Grau Acadêmico": ["Bacharelado"], "Rede de Ensino": ["Privada"]}
                    for label, values in filters.items():
                        selecionar(app, label, values)
                    app.sidebar.checkbox[1].check().run()
                    self.assertFalse(app.exception, app.exception)
                    filtered = app.session_state["indicadores_teste"]
                    runs.append((full, options, filtered))
            csv_result, pg_result = runs
            self.assertEqual(csv_result[1], pg_result[1])
            for csv_kpis, pg_kpis in ((csv_result[0][0], pg_result[0][0]), (csv_result[2], pg_result[2])):
                # A soma ponderada em float pode variar com a ordem das linhas.
                self.assertEqual(
                    {k: v for k, v in csv_kpis.items() if k != "media_enade"},
                    {k: v for k, v in pg_kpis.items() if k != "media_enade"},
                )
                self.assertAlmostEqual(csv_kpis["media_enade"], pg_kpis["media_enade"], delta=1e-12)
            self.assertEqual(pg_result[0][0]["cursos"], 7078)
            self.assertEqual(pg_result[0][0]["cursos_enade"], 1665)
            for first, second in zip(csv_result[0][1], pg_result[0][1], strict=True):
                pd.testing.assert_frame_equal(first, second, check_dtype=False)
            pd.testing.assert_frame_equal(csv_result[0][2], pg_result[0][2], check_dtype=False)
            columns = ["co_curso", "grau_academico", "modalidade_ensino", "rede_ensino",
                       "uf_final", "no_cine_rotulo", "possui_enade_2023"]
            first, second = csv_result[0][3], pg_result[0][3]
            pd.testing.assert_frame_equal(
                first[columns].sort_values("co_curso").reset_index(drop=True),
                second[columns].sort_values("co_curso").reset_index(drop=True),
                check_dtype=False,
            )
            with closing(psycopg2.connect(host=SOCKET, dbname=DB_NAME, user=postgres_env["DB_USER"],
                                          sslmode="disable", password="")) as conn, conn.cursor() as cur:
                for statement in (ROOT / "sql/interseccionalidade.sql").read_text().split(";"):
                    if not statement.strip():
                        continue
                    cur.execute(statement)
                    if cur.description and cur.description[0].name == "etapa":
                        composition = pg_result[0][1][1]
                        self.assertEqual(
                            [tuple(row[1:]) for row in composition.itertuples(index=False, name=None)],
                            [tuple(float(value) for value in row[1:]) for row in cur.fetchall()],
                        )
                    if cur.description and cur.description[0].name == "modalidade":
                        sql_rows = cur.fetchall()
                        matrix = pg_result[0][2].sort_values(list(pg_result[0][2].columns[:3]))
                        self.assertEqual([row[3] for row in sql_rows], list(matrix["Cursos"]))
                        for column, index in (("Matrículas", 4), ("Concluintes", 5),
                                              ("% Desvinculado", 6), ("% Trancada", 7)):
                            self.assertEqual([float(row[index]) for row in sql_rows], list(matrix[column]))
                        for row, py_note in zip(sql_rows, matrix["Nota ENADE Média"], strict=True):
                            if row[-1] is None:
                                self.assertTrue(pd.isna(py_note))
                            else:
                                self.assertEqual(float(row[-1]), py_note)


if __name__ == "__main__":
    unittest.main()
