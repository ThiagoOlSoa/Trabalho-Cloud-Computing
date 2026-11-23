# Saidas de identificacao somente. Nunca expor service_uri,
# service_password ou segredos do banco em terraform output.
output "aiven_project" {
  description = "Projeto Aiven alvo."
  value       = aiven_pg.observatorio.project
}

output "postgres_service_name" {
  description = "Nome do servico PostgreSQL alvo."
  value       = aiven_pg.observatorio.service_name
}

output "postgres_plan" {
  description = "Plano declarado no Terraform (deve permanecer gratuito)."
  value       = aiven_pg.observatorio.plan
}
