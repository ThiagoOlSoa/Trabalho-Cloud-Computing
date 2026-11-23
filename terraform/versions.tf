# Terraform >= 1.5 permite revisar importacoes de recursos existentes.
# O limite < 5 acompanha a faixa de compatibilidade documentada pela Aiven.
terraform {
  required_version = ">= 1.5.0, < 2.0.0"

  required_providers {
    aiven = {
      source  = "aiven/aiven"
      version = ">= 4.0.0, < 5.0.0"
    }
  }
}
