# Infraestrutura (Terraform)

Esta pasta representa como código o banco de dados do projeto: um PostgreSQL gerenciado no Aiven, “no plano Developer (developer-1, 8 GB de armazenamento).

O serviço foi criado na fase anterior pelo console do Aiven. Nesta fase ele foi **importado** para o Terraform, sem recriar o banco e sem perder os dados.

## Arquivos

| Arquivo | O que faz | Requisito |
|---|---|---|
| `versions.tf` | Versão do Terraform e do provider do Aiven | RF22 |
| `providers.tf` | Conecta ao Aiven usando o token de variável de ambiente | RNF09 |
| `variables.tf` | Parâmetros do serviço (projeto, nome, plano, nuvem) | RF22 |
| `main.tf` | O serviço PostgreSQL (`aiven_pg`), protegido contra exclusão | RF22, RNF03, RNF13 |
| `outputs.tf` | Host, porta e URI de conexão, como valores sensíveis | RF23, RNF12 |
| `terraform.tfvars.example` | Modelo das variáveis, sem valores reais | RNF11 |
| `.gitignore` | Mantém estado, variáveis e plugins fora do git | RNF10 |

## Segurança

- O token do Aiven não fica em nenhum arquivo. Ele é informado pela variável de ambiente `TF_VAR_aiven_api_token`.
- O `terraform.tfvars` (valores reais) e o `terraform.tfstate` (que guarda a senha do banco) não são versionados.
- O `prevent_destroy` impede que o Terraform apague o banco populado.

## Como executar

Pré-requisito: Terraform 1.5 ou superior e um token de API do Aiven.

1. Definir o token (PowerShell):
   ```powershell
   $env:TF_VAR_aiven_api_token = "SEU_TOKEN"
   ```
2. Copiar `terraform.tfvars.example` para `terraform.tfvars` e preencher com os dados do serviço no console do Aiven.
3. Dentro desta pasta:
   ```powershell
   terraform init
   terraform import aiven_pg.caged NOME_DO_PROJETO/NOME_DO_SERVICO
   terraform plan
   ```
4. O `plan` deve mostrar **"No changes"**, ou seja, o código representa exatamente o serviço que já existe.

Para um ambiente novo, sem banco existente, basta pular o `import` e rodar `terraform apply` (nesse caso a criação das tabelas e a carga seguem o README principal).
