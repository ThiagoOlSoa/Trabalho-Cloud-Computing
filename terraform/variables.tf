variable "aiven_project" {
  description = "Nome exato do projeto ja existente na Aiven (nao cria projeto)."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.aiven_project)) > 0
    error_message = "Informe o nome nao vazio do projeto Aiven."
  }
}

variable "postgres_service_name" {
  description = "Nome exato do servico PostgreSQL existente ou aprovado pela equipe."
  type        = string
  nullable    = false

  validation {
    condition     = length(trimspace(var.postgres_service_name)) > 0
    error_message = "Informe o nome nao vazio do servico PostgreSQL."
  }
}
