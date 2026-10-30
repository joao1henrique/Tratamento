variable "aiven_api_token" {
  description = "Token de API do Aiven. Informar via variavel de ambiente TF_VAR_aiven_api_token."
  type        = string
  sensitive   = true
}

variable "aiven_project" {
  description = "Nome do projeto no Aiven onde o servico PostgreSQL fica."
  type        = string
}

variable "service_name" {
  description = "Nome do servico PostgreSQL no Aiven."
  type        = string
}

variable "plan" {
  description = "Plano do servico no Aiven (ex.: plano gratuito). Deve ser igual ao do console."
  type        = string
}

variable "cloud_name" {
  description = "Nuvem/regiao do servico no Aiven. Deve ser igual a do console."
  type        = string
}
