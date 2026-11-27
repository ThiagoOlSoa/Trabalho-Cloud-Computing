"""Testes de carga com registros sintéticos e PostgreSQL local opcional."""

import gzip
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import psycopg2
from psycopg2 import sql

from src import load, load_enade
from src.transform import CENSO_COLUMNS, ENADE_COLUMNS
from test_etl import ROOT, censo, enade, write_csv


class TestValidacaoCarga(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.csv = Path(temp.name) / "carga.csv"

    def rejeita(self, loader, columns, records, message, encoding="utf-8"):
        write_csv(self.csv, columns, records, encoding=encoding)
        with self.assertRaisesRegex(ValueError, message):
            loader(self.csv)

    def test_censo_chaves_tipos_e_totais(self):
        for changes, error in (
            ({"CO_CURSO": ""}, "CO_CURSO"),
            ({"QT_MAT": "-1"}, "QT_MAT"),
            ({"QT_MAT_FEM": "1"}, "não reconciliam"),
            ({"QT_ING": "1.5"}, "inteiro"),
        ):
            with self.subTest(changes=changes):
                self.rejeita(load.carregar_csv, CENSO_COLUMNS, [censo(**changes)], error, "cp1252")
        self.rejeita(load.carregar_csv, CENSO_COLUMNS, [censo(), censo(CO_CURSO="11")],
                     "Chave duplicada", "cp1252")
        self.rejeita(load.carregar_csv, CENSO_COLUMNS,
                     [censo(), censo(TP_DIMENSAO="2", NO_CURSO="Física")], "divergentes", "cp1252")

    def test_enade_chaves_tipos_e_totais(self):
        for changes, error in (
            ({"CO_CURSO": ""}, "CO_CURSO"),
            ({"MEDIA_NT_GER": "nan"}, "decimal"),
            ({"MEDIA_NT_GER": ""}, "ausente"),
            ({"QT_NOTAS_VALIDAS": "2"}, "incompatíveis"),
            ({"QT_SEXO_F": "0"}, "incompatíveis"),
            ({"QT_RACA_SEM_RESPOSTA": "-1"}, "inteiro"),
        ):
            with self.subTest(changes=changes):
                self.rejeita(load_enade.carregar_csv, ENADE_COLUMNS, [enade(**changes)], error)
        self.rejeita(load_enade.carregar_csv, ENADE_COLUMNS, [enade(), enade(CO_CURSO="11")],
                     "Chave duplicada")


    def test_gzip_e_csv_retorna_os_mesmos_tipos_e_valores(self):
        for loader, columns, record, encoding in (
            (load, CENSO_COLUMNS, censo(), "cp1252"),
            (load_enade, ENADE_COLUMNS, enade(), "utf-8-sig"),
        ):
            with self.subTest(loader=loader.__name__):
                write_csv(self.csv, columns, [record], encoding=encoding)
                compressed = self.csv.with_suffix(".csv.gz")
                compressed.write_bytes(gzip.compress(self.csv.read_bytes(), mtime=0))
                self.assertEqual(loader.carregar_csv(compressed), loader.carregar_csv(self.csv))

    def test_gzip_com_duplicata_normalizada_falha_antes_da_conexao(self):
        for loader, columns, records, encoding in (
            (load, CENSO_COLUMNS, [censo(), censo(CO_CURSO="11")], "cp1252"),
            (load_enade, ENADE_COLUMNS, [enade(), enade(CO_CURSO="11")], "utf-8"),
        ):
            with self.subTest(loader=loader.__name__):
                write_csv(self.csv, columns, records, encoding=encoding)
                compressed = self.csv.with_suffix(".csv.gz")
                compressed.write_bytes(gzip.compress(self.csv.read_bytes(), mtime=0))
                with patch.object(load, "conectar") as conectar, patch.object(load, "upsert") as upsert:
                    with self.assertRaisesRegex(SystemExit, "duplicada"):
                        load.executar_carga("Teste", compressed, loader.carregar_csv, upsert)
                    conectar.assert_not_called()
                    upsert.assert_not_called()

    def test_gzip_corrompido_ou_truncado_falha_antes_da_conexao(self):
        for loader, columns, record, encoding in (
            (load, CENSO_COLUMNS, censo(), "cp1252"),
            (load_enade, ENADE_COLUMNS, enade(), "utf-8"),
        ):
            write_csv(self.csv, columns, [record], encoding=encoding)
            valid = gzip.compress(self.csv.read_bytes(), mtime=0)
            crc_invalid = valid[:-8] + bytes([valid[-8] ^ 0xff]) + valid[-7:]
            for content in (b"nao-gzip", valid[:-1], crc_invalid):
                with self.subTest(loader=loader.__name__), patch.object(load, "conectar") as conectar:
                    compressed = self.csv.with_suffix(".csv.gz")
                    compressed.write_bytes(content)
                    with self.assertRaisesRegex(SystemExit, "gzip inválido"):
                        load.executar_carga("Teste", compressed, loader.carregar_csv, None)
                    conectar.assert_not_called()


SOCKET = os.getenv("ETL_TEST_PG_SOCKET")
PSQL = os.getenv("ETL_TEST_PSQL") or shutil.which("psql")


@unittest.skipUnless(SOCKET and Path(SOCKET).is_dir() and PSQL,
                     "Requer socket de um PostgreSQL local descartável e psql.")
class TestPostgres(unittest.TestCase):
    def setUp(self):
        name = "etl_test_" + uuid4().hex
        self.params = {"host": SOCKET, "user": os.environ.get("ETL_TEST_PG_USER", "agent"),
                       "sslmode": "disable", "password": "", "connect_timeout": 3}
        admin = psycopg2.connect(dbname="postgres", **self.params)
        self.addCleanup(admin.close)
        admin.autocommit = True
        drop = sql.SQL("DROP DATABASE {}").format(sql.Identifier(name))
        with admin.cursor() as cur:
            cur.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
        self.addCleanup(lambda: self.drop(admin, drop))
        self.name = name
        self.conn = psycopg2.connect(dbname=name, **self.params)
        self.addCleanup(self.conn.close)
        self.exec_sql((ROOT / "sql/schema.sql").read_text(encoding="utf-8"))
        self.exec_sql((ROOT / "sql/views.sql").read_text(encoding="utf-8"))
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.directory = Path(temp.name)

    @staticmethod
    def drop(conn, query):
        with conn.cursor() as cur:
            cur.execute(query)

    def exec_sql(self, statement):
        with self.conn, self.conn.cursor() as cur:
            cur.execute(statement)
            return cur.fetchall() if cur.description else None

    def censo_dados(self, records):
        p = self.directory / "censo.csv"
        write_csv(p, CENSO_COLUMNS, records, encoding="cp1252")
        return load.carregar_csv(p)

    def enade_dados(self, records):
        p = self.directory / "enade.csv"
        write_csv(p, ENADE_COLUMNS, records)
        return load_enade.carregar_csv(p)

    def run_sql_file(self, file):
        return subprocess.run(
            [PSQL, "-X", "-v", "ON_ERROR_STOP=1", "-h", SOCKET, "-U", self.params["user"],
             "-d", self.name, "-f", str(file)],
            capture_output=True, text=True, check=False,
            env={**os.environ, "PGSSLMODE": "disable", "PGPASSWORD": ""},
        )

    def test_primeira_carga_reexecucao_e_view(self):
        censo_data = self.censo_dados([
            censo(TP_DIMENSAO="2", QT_MAT="2", QT_MAT_FEM="2", QT_MAT_PRETA="2"),
            censo(CO_CURSO="12", TP_DIMENSAO="2"),
            censo(CO_CURSO="13"),
        ])
        self.assertEqual(load.gravar_censo(self.conn, censo_data), 3)
        data = self.enade_dados([enade()])
        self.assertEqual(load_enade.gravar_enade(self.conn, data), 1)
        load.gravar_censo(self.conn, censo_data)
        load_enade.gravar_enade(self.conn, data)
        self.assertEqual(self.exec_sql("SELECT count(*) FROM fato_censo_curso"), [(3,)])
        self.assertEqual(self.exec_sql("SELECT count(*) FROM fato_enade_curso"), [(1,)])
        self.assertEqual(self.exec_sql("""
            SELECT co_curso, possui_enade_2023, qt_mat, qt_participantes
            FROM vw_observatorio_censo_enade ORDER BY co_curso
        """), [(11, True, 2, 1), (12, False, 0, 0)])
        for file in ("queries.sql", "interseccionalidade.sql", "auditoria_carga.sql"):
            result = self.run_sql_file(ROOT / "sql" / file)
            self.assertEqual(result.returncode, 0, result.stderr)

    def test_rollback_censo_apos_dimensoes(self):
        self.exec_sql("ALTER TABLE fato_censo_curso ADD CHECK (co_curso <> 12)")
        with patch.object(load, "BATCH_SIZE", 1), self.assertRaises(psycopg2.errors.CheckViolation):
            load.gravar_censo(self.conn, self.censo_dados([censo(), censo(CO_CURSO="12")]))
        self.assertEqual(self.exec_sql("SELECT count(*) FROM dim_curso"), [(0,)])
        self.assertEqual(self.exec_sql("SELECT count(*) FROM fato_censo_curso"), [(0,)])

    def test_enade_curso_ausente_e_rollback_de_lotes(self):
        load.gravar_censo(self.conn, self.censo_dados([censo(), censo(CO_CURSO="12")]))
        with self.assertRaisesRegex(ValueError, "ausentes"):
            load_enade.gravar_enade(self.conn, self.enade_dados([enade(CO_CURSO="13")]))
        self.exec_sql("ALTER TABLE fato_enade_curso ADD CHECK (co_curso <> 12)")
        with patch.object(load, "BATCH_SIZE", 1), self.assertRaises(psycopg2.errors.CheckViolation):
            load_enade.gravar_enade(self.conn, self.enade_dados([enade(), enade(CO_CURSO="12")]))
        self.assertEqual(self.exec_sql("SELECT count(*) FROM fato_enade_curso"), [(0,)])
        with self.assertRaises(psycopg2.errors.ForeignKeyViolation):
            self.exec_sql("""
                INSERT INTO fato_enade_curso
                (nu_ano, co_curso, qt_participantes, qt_notas_validas, qt_sexo_f, qt_sexo_m,
                 qt_raca_branca, qt_raca_preta, qt_raca_parda, qt_raca_amarela,
                 qt_raca_indigena, qt_raca_nao_declara, qt_raca_sem_resposta)
                VALUES (2023, 13, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
            """)

    def test_migracoes_reexecucao_esquema_atual(self):
        files = sorted((ROOT / "sql/migrations").glob("*.sql"))
        for _ in range(2):
            for migration in files:
                result = self.run_sql_file(migration)
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.exec_sql("""
          SELECT count(*) FROM pg_constraint WHERE conrelid = 'fato_enade_curso'::regclass AND contype='f'
        """), [(1,)])

    def test_migracao_002_detecta_divergencias_sem_remover(self):
        load.gravar_censo(self.conn, self.censo_dados([censo()]))
        self.exec_sql("""
            ALTER TABLE fato_censo_curso DROP CONSTRAINT ck_censo_sexo_mat;
            DROP INDEX ux_fato_censo_curso_grao;
            INSERT INTO fato_censo_curso (""" + ", ".join(load.COLUNAS_FATO) + """)
            SELECT """ + ", ".join("2" if c == "QT_SIT_TRANCADA" else c for c in load.COLUNAS_FATO) + """
            FROM fato_censo_curso;
        """)
        report = self.run_sql_file(ROOT / "sql/auditoria_carga.sql")
        self.assertEqual(report.returncode, 0, report.stderr)
        self.assertRegex(report.stdout, r"\{1,2\}[^\n]+\|\s+2")
        result = self.run_sql_file(ROOT / "sql/migrations/002_censo_idempotente.sql")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicatas", result.stderr)
        self.assertEqual(self.exec_sql("SELECT qt_sit_trancada FROM fato_censo_curso ORDER BY id_fato"),
                         [(0,), (2,)])

    def test_migracao_chave_legada_e_tipo_texto(self):
        load.gravar_censo(self.conn, self.censo_dados([censo(TP_DIMENSAO="2")]))
        load_enade.gravar_enade(self.conn, self.enade_dados([enade()]))
        self.exec_sql("""
            DROP VIEW vw_observatorio_censo_enade;
            ALTER TABLE fato_enade_curso DROP CONSTRAINT fato_enade_curso_co_curso_fkey;
            ALTER TABLE fato_enade_curso DROP CONSTRAINT fato_enade_curso_pkey;
            ALTER TABLE fato_enade_curso ALTER COLUMN co_curso TYPE TEXT;
            UPDATE fato_enade_curso SET co_curso = '011';
            ALTER TABLE fato_enade_curso ADD PRIMARY KEY (co_curso);
            CREATE VIEW vw_observatorio_censo_enade AS SELECT co_curso FROM fato_enade_curso;
        """)
        for file in ("001_enade_composite_key.sql", "003_integridade_e_tipos.sql"):
            result = self.run_sql_file(ROOT / "sql/migrations" / file)
            self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.exec_sql("""
            SELECT co_curso, possui_enade_2023 FROM vw_observatorio_censo_enade
        """), [(11, True)])
        self.assertEqual(self.exec_sql("""
            SELECT pg_get_constraintdef(oid)
            FROM pg_constraint WHERE conrelid = 'fato_enade_curso'::regclass AND contype = 'p'
        """), [("PRIMARY KEY (nu_ano, co_curso)",)])

    def test_migracao_003_rollback_se_view_falhar(self):
        self.exec_sql("""
            DROP VIEW vw_observatorio_censo_enade;
            ALTER TABLE fato_enade_curso DROP CONSTRAINT fato_enade_curso_co_curso_fkey;
            ALTER TABLE fato_enade_curso ALTER COLUMN co_curso TYPE TEXT;
            CREATE VIEW vw_observatorio_censo_enade AS SELECT co_curso FROM fato_enade_curso;
        """)
        migrations = self.directory / "migrations"
        migrations.mkdir()
        source = ROOT / "sql/migrations/003_integridade_e_tipos.sql"
        migration = migrations / source.name
        shutil.copyfile(source, migration)
        (self.directory / "views.sql").write_text("SELECT coluna_inexistente;\n")
        result = self.run_sql_file(migration)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("coluna_inexistente", result.stderr)
        self.assertEqual(self.exec_sql("""
            SELECT data_type FROM information_schema.columns
            WHERE table_name = 'fato_enade_curso' AND column_name = 'co_curso'
        """), [("text",)])
        self.assertEqual(self.exec_sql("SELECT * FROM vw_observatorio_censo_enade"), [])


if __name__ == "__main__":
    unittest.main()
