# RNF09 - O token NAO fica no codigo. Ele e lido da variavel de ambiente
# TF_VAR_aiven_api_token, definida apenas na maquina de quem executa.
provider "aiven" {
  api_token = var.aiven_api_token
}
