# RF23 - Dados de conexao expostos como saidas sensiveis.
# Para ver um valor: terraform output -raw pg_uri

output "pg_host" {
  description = "Host do PostgreSQL."
  value       = aiven_pg.caged.service_host
  sensitive   = true
}

output "pg_port" {
  description = "Porta do PostgreSQL."
  value       = aiven_pg.caged.service_port
  sensitive   = true
}

output "pg_uri" {
  description = "URI de conexao (contem a senha, conexao com SSL - RNF12)."
  value       = aiven_pg.caged.service_uri
  sensitive   = true
}
