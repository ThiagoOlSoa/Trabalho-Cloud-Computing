"""Configuração de publicação testada com valores fictícios e callbacks locais."""

import logging
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

import psycopg2
from streamlit.testing.v1 import AppTest

from test_etl import censo, enade, write_csv
from test_indicadores import APP
from src.transform import CENSO_COLUMNS, ENADE_COLUMNS


CONFIG_ENV = (
    "APP_DATA_MODE", "DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD",
    "DB_SSLMODE", "DB_SSLROOTCERT", "DB_SSL_CA_PEM",
)
SECRET_TESTE = {
    "APP_DATA_MODE": "postgres",
    "DB_HOST": "postgres.exemplo.invalid",
    "DB_PORT": 5432,
    "DB_NAME": "teste",
    "DB_USER": "leitora",
    "DB_PASSWORD": "valor-ficticio",
}


class TestPublicacao(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        (self.root / "app").mkdir()
        self.app_path = self.root / "app/app.py"
        self.app_path.write_bytes(APP.read_bytes())
        env = patch.dict(os.environ, {k: v for k, v in os.environ.items() if k not in CONFIG_ENV}, clear=True)
        env.start()
        self.addCleanup(env.stop)

    def dados_locais(self):
        data = self.root / "data/processed"
        data.mkdir(parents=True)
        write_csv(data / "censo_2024_area1.csv", CENSO_COLUMNS,
                  [censo(TP_DIMENSAO="2")], encoding="cp1252")
        write_csv(data / "enade_2023_area1.csv", ENADE_COLUMNS, [enade()])

    def test_sem_credenciais_e_sem_csv(self):
        app = AppTest.from_file(str(self.app_path))
        with patch("psycopg2.connect") as connect:
            app.run()
        connect.assert_not_called()
        self.assertFalse(app.exception)
        self.assertIn("Nenhuma fonte de dados", app.error[0].value)

    def test_sem_credenciais_com_csv(self):
        self.dados_locais()
        app = AppTest.from_file(str(self.app_path)).run()
        self.assertFalse(app.exception)
        self.assertIn("CSVs Locais", app.sidebar.caption[0].value)
        self.assertEqual(len(app.metric), 6)
        self.assertEqual(app.metric[5].value, "0,0")

    def test_publicacao_configuracao_incompleta_nao_tenta_conectar(self):
        self.dados_locais()
        app = AppTest.from_file(str(self.app_path))
        app.secrets["observatorio"] = {"APP_DATA_MODE": "postgres", "DB_HOST": "postgres.exemplo.invalid"}
        with patch("psycopg2.connect") as connect:
            app.run()
        connect.assert_not_called()
        self.assertFalse(app.exception)
        self.assertIn("modo de publicação", app.error[0].value)
        self.assertFalse(app.sidebar.checkbox)

    def test_falha_postgres_segrega_modos_e_oculta_detalhes(self):
        self.dados_locais()
        for modo in ("auto", "postgres"):
            with self.subTest(modo=modo):
                app = AppTest.from_file(str(self.app_path))
                app.secrets["observatorio"] = {**SECRET_TESTE, "APP_DATA_MODE": modo}
                with (
                    patch("psycopg2.connect", side_effect=psycopg2.OperationalError("detalhe-ficticio")),
                    self.assertLogs(logging.getLogger("__main__"), level="WARNING") as logs,
                ):
                    app.run()
                self.assertFalse(app.exception)
                self.assertTrue(logs.output)
                self.assertNotIn("detalhe-ficticio", str(logs.output) + str(app))
                if modo == "auto":
                    self.assertIn("CSVs Locais", app.sidebar.caption[0].value)
                else:
                    self.assertIn("modo de publicação", app.error[0].value)
                    self.assertFalse(app.metric)

    def test_ca_pem_temporaria_ssl_e_precedencia_env(self):
        app = AppTest.from_file(str(self.app_path))
        app.secrets["observatorio"] = {
            **SECRET_TESTE, "DB_SSLMODE": "verify-full", "DB_SSL_CA_PEM": "CA fictícia para o teste",
        }
        captured = []

        def conectar_falso(**params):
            self.assertEqual(params["host"], "substituicao.exemplo.invalid")
            self.assertEqual(params["sslmode"], "verify-full")
            self.assertIn("default_transaction_read_only=on", params["options"])
            cert = Path(params["sslrootcert"])
            self.assertEqual(cert.read_text(encoding="utf-8"), "CA fictícia para o teste")
            captured.append(cert)
            conn = MagicMock()
            conn.cursor.return_value.__enter__.side_effect = psycopg2.OperationalError("erro fictício")
            return conn

        with patch.dict(os.environ, {"DB_HOST": "substituicao.exemplo.invalid"}):
            with patch("psycopg2.connect", side_effect=conectar_falso) as connect:
                app.run()
        connect.assert_called_once()
        self.assertTrue(captured)
        self.assertFalse(captured[0].exists())
        self.assertFalse(app.exception)


if __name__ == "__main__":
    unittest.main()
