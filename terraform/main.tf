# Autenticacao exclusivamente por AIVEN_TOKEN no ambiente.
# Nunca armazenar tokens nos arquivos .tf/.tfvars ou no repositorio.
provider "aiven" {}

# Gerencia SOMENTE o PostgreSQL do observatorio. O projeto Aiven ja existe:
# ele nao e criado nem gerenciado por este Terraform.
resource "aiven_pg" "observatorio" {
  project      = var.aiven_project
  service_name = var.postgres_service_name

  # Plano gratuito de 1 GB confirmado no catálogo público da Aiven.
  # Confirme a disponibilidade na organização antes de operar.
  # Nao alterar para um tier pago.
  plan = "free-1-1gb"

  # Nao declarar cloud_name, VPC, IP estatico, disco extra, pooling ou integracoes:
  # a Aiven determina a localizacao do plano Free e ha restricoes no tier.
  lifecycle {
    # Impede destruicao/substituicao enquanto esta declaracao estiver presente.
    # NAO protege de exclusoes manuais na Console nem da remocao deste bloco.
    prevent_destroy = true
  }
}
