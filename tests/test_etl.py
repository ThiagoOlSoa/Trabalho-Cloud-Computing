"""Casos pequenos e sintéticos. Nenhum teste conecta a um banco."""

import ast
import csv
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

from src.extract import extract
from src.transform import CENSO_COLUMNS, ENADE_COLUMNS, GEOGRAPHY, SHIFTS, transform


ROOT = Path(__file__).resolve().parents[1]


def censo(**changes):
    row = dict.fromkeys(CENSO_COLUMNS, "0")
    row.update(dict.fromkeys(GEOGRAPHY, "."))
    row.update(NU_ANO_CENSO="2024", CO_CURSO="011", CO_IES="1", NO_CURSO="Matemática",
               CO_CINE_AREA_GERAL="05", CO_CINE_AREA_ESPECIFICA="054",
               CO_CINE_AREA_DETALHADA="0541", CO_CINE_ROTULO='"0541M01"',
               TP_NIVEL_ACADEMICO="1", TP_GRAU_ACADEMICO="1",
               TP_DIMENSAO="3", TP_MODALIDADE_ENSINO="2")
    row.update(dict.fromkeys(SHIFTS, "."))
    row.update(changes)
    return row


def enade(**changes):
    row = dict.fromkeys(ENADE_COLUMNS, "0")
    row.update(NU_ANO="2023", CO_CURSO="011", CO_IES="9", CO_GRUPO="5902",
               QT_PARTICIPANTES="1", QT_NOTAS_VALIDAS="1", QT_SEXO_F="1",
               QT_RACA_SEM_RESPOSTA="1", MEDIA_NT_GER="0", MEDIA_NT_FG="100",
               MEDIA_NT_CE="12,5")
    row.update(changes)
    return row


def write_csv(path, columns, records, *, encoding="utf-8", delimiter=";"):
    with path.open("w", encoding=encoding, newline="") as stream:
        writer = csv.DictWriter(stream, columns, delimiter=delimiter)
        writer.writeheader()
        writer.writerows(records)


def literal_assignments(path, names):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        node.targets[0].id: ast.literal_eval(node.value)
        for node in tree.body
        if isinstance(node, ast.Assign)
        and isinstance(node.targets[0], ast.Name)
        and node.targets[0].id in names
    }


class TestETL(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.censo_in = self.root / "entrada_censo.csv"
        self.censo_out = self.root / "censo_2024_area1.csv"
        self.enade_in = self.root / "entrada_enade.csv"
        self.enade_out = self.root / "enade_2023_area1.csv"

    def prepare_censo(self, records):
        write_csv(self.censo_in, CENSO_COLUMNS, records, encoding="cp1252")
        return transform("censo", self.censo_in, self.censo_out)

    def prepare_enade(self, records):
        write_csv(self.enade_in, ENADE_COLUMNS, records)
        return transform("enade", self.enade_in, self.enade_out, censo_reference=self.censo_out)

    def test_extracao_zip_codificacao_separador_e_amostra(self):
        write_csv(self.censo_in, ["NOME"], [{"NOME": "Matemática"}, {"NOME": "Outra"}],
                  encoding="cp1252", delimiter="|")
        archive = self.root / "entrada.zip"
        with ZipFile(archive, "w") as z:
            z.write(self.censo_in, "dados/curso.csv")
        extract(archive, self.censo_out, encoding="cp1252", delimiter="|",
                member="dados/curso.csv", limit=1)
        self.assertEqual(self.censo_out.read_text(), "NOME\nMatemática\n")

    def test_censo_recorte_chaves_e_contrato_de_carga(self):
        count = self.prepare_censo([
            censo(), censo(CO_MUNICIPIO="3550308", TP_DIMENSAO="2"),
            censo(CO_CURSO="12", CO_CINE_AREA_GERAL="03"),
            censo(CO_CURSO="13", TP_NIVEL_ACADEMICO="2"),
            censo(CO_CURSO="14", NU_ANO_CENSO="2023"),
        ])
        self.assertEqual(count, 2)
        names = {"COLUNAS_IES", "COLUNAS_CURSO", "COLUNAS_CINE",
                 "COLUNAS_LOCALIZACAO", "COLUNAS_FATO"}
        expected = literal_assignments(ROOT / "src/load.py", names)
        self.assertEqual(set(expected), names)
        df = pd.read_csv(self.censo_out, sep=";", encoding="cp1252")
        self.assertEqual(set(df), set().union(*expected.values()) - {"ID_LOCALIZACAO"})
        self.assertEqual(df.CO_CURSO.tolist(), [11, 11])
        self.assertEqual(df.CO_CINE_ROTULO.tolist(), ["0541M01"] * 2)
        self.assertEqual(df.QT_ING_DIURNO.tolist(), [0, 0])
        self.assertTrue(pd.isna(df.CO_MUNICIPIO.iloc[0]))

    def test_enade_recorte_notas_e_contrato_de_carga(self):
        self.prepare_censo([censo()])
        count = self.prepare_enade([
            enade(), enade(CO_CURSO="12"), enade(NU_ANO="2022"),
        ])
        self.assertEqual(count, 1)
        expected = literal_assignments(ROOT / "src/load_enade.py", {"COLUNAS"})["COLUNAS"]
        df = pd.read_csv(self.enade_out, sep=";", encoding="utf-8-sig",
                         dtype={"CO_CURSO": "string", "CO_IES": "string"})
        self.assertEqual(list(df), list(expected))
        row = df.iloc[0]
        self.assertEqual((row.CO_CURSO, row.CO_IES), ("11", "9"))
        self.assertEqual((row.MEDIA_NT_GER, row.MEDIA_NT_FG, row.MEDIA_NT_CE), (0, 100, 12.5))
        self.assertEqual(row.QT_RACA_SEM_RESPOSTA, 1)

    def test_censo_campos_invalidos_e_coluna_ausente(self):
        for change in ({"QT_ING": "-1"}, {"QT_MAT": "1.5"}, {"QT_CONC": ""},
                       {"CO_CURSO": ""}, {"QT_MAT_FEM": "1"}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.prepare_censo([censo(**change)])
            self.assertFalse(self.censo_out.exists())
        write_csv(self.censo_in, ["CO_CURSO"], [{"CO_CURSO": "1"}])
        with self.assertRaisesRegex(ValueError, "Colunas obrigatórias"):
            transform("censo", self.censo_in, self.censo_out)

    def test_enade_notas_incompletas_ou_invalidas_e_totais(self):
        self.prepare_censo([censo()])
        for change in ({"MEDIA_NT_GER": "NaN"}, {"MEDIA_NT_GER": "101"},
                       {"MEDIA_NT_GER": ""}, {"QT_NOTAS_VALIDAS": "2"},
                       {"QT_SEXO_F": "0"}, {"QT_RACA_SEM_RESPOSTA": ""}):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.prepare_enade([enade(**change)])
            self.assertFalse(self.enade_out.exists())
        self.assertEqual(self.prepare_enade([enade(
            QT_NOTAS_VALIDAS="0", MEDIA_NT_GER="", MEDIA_NT_FG=".", MEDIA_NT_CE="",
        )]), 1)
        self.assertTrue(pd.isna(pd.read_csv(self.enade_out, sep=";").MEDIA_NT_GER.iloc[0]))

    def test_duplicatas_normalizadas_abortam_publicacao(self):
        with self.assertRaisesRegex(ValueError, "Chave duplicada"):
            self.prepare_censo([censo(), censo(CO_CURSO="11", CO_MUNICIPIO="")])
        self.assertFalse(self.censo_out.exists())
        self.prepare_censo([censo()])
        with self.assertRaisesRegex(ValueError, "Chave duplicada"):
            self.prepare_enade([enade(), enade(CO_CURSO="11")])
        self.assertFalse(self.enade_out.exists())

    def test_processamento_reproduzivel_e_sem_sobrescrita(self):
        self.prepare_censo([censo()])
        other = self.root / "outro.csv"
        transform("censo", self.censo_in, other)
        self.assertEqual(other.read_bytes(), self.censo_out.read_bytes())
        with self.assertRaises(FileExistsError):
            transform("censo", self.censo_in, other)
        self.assertEqual(other.read_bytes(), self.censo_out.read_bytes())


if __name__ == "__main__":
    unittest.main()
