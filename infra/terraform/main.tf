# RF22 - Servico PostgreSQL gerenciado no Aiven, representado como codigo.
# Guarda os dados tratados do Novo CAGED (banco defaultdb, schema public).
#
# O servico ja existia (criado na fase anterior) e foi trazido para o
# Terraform com:
#   terraform import aiven_pg.caged <projeto>/<nome-do-servico>
resource "aiven_pg" "caged" {
  project      = var.aiven_project
  service_name = var.service_name
  cloud_name   = var.cloud_name
  plan         = var.plan # RNF03 - plano Developer (8 GB de armazenamento)

  # RNF13 - O banco esta populado com a carga da fase anterior.
  # Impede que um "terraform destroy" ou uma recriacao apague os dados.
  lifecycle {
    prevent_destroy = true
  }
}
