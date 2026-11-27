import io
import unittest
from contextlib import redirect_stdout

from scripts.validar_indicadores import REFERENCIAS, comparar
from scripts.verificar_arquivos_ci import blocked


class QualidadeTest(unittest.TestCase):
    def test_arquivos_protegidos_e_excecoes_publicas(self):
        for path in ("app/.env", ".streamlit/secrets.toml", "terraform/a.tfstate.backup",
                     "terraform/.terraform/provider", "data/raw/.env.example", "data/raw/inep.zip",
                     "data/processed/outro.csv.gz", "certificados/servidor.key"):
            with self.subTest(path=path):
                self.assertTrue(blocked(path))
        for path in (".env.example", "terraform/terraform.tfvars.example",
                     "data/processed/enade_2023_area1.csv.gz", "data/raw/README.md"):
            with self.subTest(path=path):
                self.assertFalse(blocked(path))

    def test_comparacao_indica_diferenca_e_valor_ausente(self):
        output = io.StringIO()
        with redirect_stdout(output):
            self.assertEqual(comparar(REFERENCIAS), 0)
            self.assertEqual(comparar(REFERENCIAS | {"media_enade": None}), 1)
        self.assertIn("0 divergências", output.getvalue())
        self.assertIn("DIVERGÊNCIA | media_enade | esperado 41.8 | encontrado None", output.getvalue())
