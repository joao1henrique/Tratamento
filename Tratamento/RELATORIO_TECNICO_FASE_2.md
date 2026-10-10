# Entrega Técnica — Fase 2
## Unificação, tratamento, modelagem e armazenamento dos dados do Novo CAGED

**Disciplina:** Big Data e Analytics  
**Projeto:** Dinâmica do emprego formal e turnover setorial, com recortes por sexo e raça/cor  
**Equipe:** [inserir integrantes]  
**Repositório GitHub:** [inserir URL]  
**Data da entrega:** [inserir]

> **Escopo da evidência:** As informações sobre o processo de tratamento e a modelagem foram extraídas dos scripts e do README fornecidos pela equipe. Os números de implantação e os testes abaixo são resultados informados a partir da execução no Aiven, ainda sujeitos à conferência final no painel do serviço e às consultas de auditoria anexas.

## 1. Base de dados tratada

### 1.1 Origem e versão dos dados

A fonte é a base pública de microdados do **Novo CAGED**, disponibilizada pelo Ministério do Trabalho e Emprego (MTE) por meio do PDET. O recorte adotado compreende competências de **janeiro de 2020 a dezembro de 2025**. A equipe utilizou os arquivos `CAGEDMOV` (movimentações declaradas no prazo), `CAGEDFOR` (declarações fora do prazo) e `CAGEDEXC` (exclusões), totalizando **212 arquivos originais**: 72 MOV, 71 FOR e 69 EXC. O conjunto bruto é descrito no README da equipe como aproximadamente **3,1 GB compactados** e **261.674.712 linhas lidas**.

O código de tratamento não modifica os arquivos originais. Os dados transformados foram salvos em **424 arquivos CSV** na pasta `saida/` (dois produtos analíticos para cada arquivo de origem). O conjunto desses arquivos ocupava aproximadamente **0,26 GiB** no computador utilizado para a carga.

### 1.2 Processo de preparação

- **Leitura incremental:** descompactação e processamento em blocos de até 500 mil linhas com `pandas.read_csv(chunksize=500000)`, restringindo a leitura às colunas necessárias.
- **Padronização:** nomes de atributos sem acentos e conversão explícita de competências para `DATE`, códigos para inteiros, salários e horas para dados numéricos.
- **Competência correta:** a agregação utiliza `competênciamov`, e não o mês do nome do arquivo, já que arquivos FOR e EXC podem alterar competências anteriores.
- **Unificação:** saldos e somatórios consolidados por **MOV + FOR − EXC**. As exclusões têm suas contribuições invertidas.
- **Duplicidade:** registros individuais iguais não foram eliminados por falta de identificador que permita afirmar tratar-se de duplicatas reais; em vez disso, foram agregados por dimensões analíticas.
- **Ausências e códigos inválidos:** representados em categorias de “Não identificado”, visando preservar as contagens de movimentação.
- **Faixa etária:** classes de 14–17, 18–24, 25–29, 30–39, 40–49, 50–64 e 65+; valores fora das faixas esperadas recebem classificação específica.
- **Salários:** todas as movimentações compõem as contagens, mas somas salariais utilizam somente valores entre 0,3 e 150 salários mínimos, segundo a regra documentada pela equipe. **Limitação:** a implementação descrita usa um salário mínimo por ano, sem representar todas as alterações intra-anuais, e não remove necessariamente contratos intermitentes do cálculo da média.
- **Agregação:** contagens de admissões/desligamentos, saldo, quantidade de salários válidos, soma de salários e de horas por chave analítica; não são enviados registros individuais ao banco.

O tratamento encontra-se nos arquivos `scripts/tratar_dados.py`, `scripts/config.py`, `scripts/main.py` e demais scripts do repositório. O processo de carga utilizado na nuvem é `importar_aiven.py`.

### 1.3 Justificativa da transformação

O objetivo analítico é comparar movimentos do mercado formal por competência, UF, setor, sexo, raça/cor e perfil etário, não consultar vínculos individuais. A agregação reduz significativamente o volume, conserva medidas aditivas importantes e permite implantar o banco em um serviço de recursos limitados. Há uma contrapartida explícita: **não é possível cruzar faixa etária com setor a partir dessas duas tabelas fato**, pois essas dimensões estão separadas para economizar espaço. Escolaridade não foi incluída nas tabelas finais por ampliar o volume e ter menor relevância para o recorte definido.

## 2. Processo de tratamento e reprodutibilidade

### 2.1 Ferramentas

- Python, pandas, SQLAlchemy, psycopg2, python-dotenv e py7zr;
- SQL/PostgreSQL para modelagem, chaves, relacionamentos e agregações carregadas;
- GitHub para versionamento do código e documentação;
- PostgreSQL gerenciado pelo Aiven para armazenamento na nuvem.

### 2.2 Fluxo executado

1. Manutenção dos microdados originais fora do repositório.
2. Tratamento dos arquivos MOV, FOR e EXC e emissão de CSVs derivados em `saida/`.
3. Criação do serviço PostgreSQL no Aiven e configuração local das variáveis de conexão em `.env` (arquivo não publicado).
4. Criação das 9 tabelas a partir de `sql/criar_tabelas.sql`.
5. Carga das seis dimensões a partir do layout de referência do Novo CAGED.
6. Importação incremental de 424 CSVs tratados pelo script `importar_aiven.py`; consolidação das chaves no banco.
7. Preenchimento de `controle_carga` e execução de consultas de consistência e tamanho.

**Cuidado com reexecução:** o SQL de criação contém comandos `DROP TABLE`, portanto não deve ser executado novamente no banco populado. O carregador da nuvem foi concebido para bloquear uma segunda importação quando as tabelas fato ou a de controle já contêm dados. Credenciais devem permanecer em `.env`, excluído do Git por `.gitignore`.

## 3. Base armazenada no banco de dados

### 3.1 Arquitetura e modelagem

Foi adotado um **modelo dimensional de duas tabelas fato e seis dimensões**, além de uma tabela para rastrear a carga. O DDL completo, com tipos, índices, chaves primárias e estrangeiras, consta em `sql/criar_tabelas.sql`.

| Tabela | Função | Registros após a carga |
|---|---|---:|
| `fato_movimentacao` | Métricas por competência, UF, setor, sexo, raça/cor e tipo de movimentação | 1.875.754 |
| `fato_perfil` | Métricas por competência, UF, sexo, raça/cor, faixa etária e grupo | 312.896 |
| `dim_uf` | Unidades federativas e referência de não identificado | 28 |
| `dim_setor` | Seções CNAE | 22 |
| `dim_sexo` | Categorias de sexo | 3 |
| `dim_raca_cor` | Categorias de raça/cor | 7 |
| `dim_faixa_etaria` | Faixas de idade | 8 |
| `dim_tipo_movimentacao` | Tipos e grupos de movimentação | 18 |
| `controle_carga` | Arquivos de origem e metadados de processamento | 212 |
| **Total** | **Todas as tabelas** | **2.188.948** |

As tabelas fato têm `competencia DATE`, dimensões codificadas (`SMALLINT`/`CHAR(1)`), métricas `INTEGER` e somatórios `NUMERIC(18,2)`. `fato_perfil` possui `grupo VARCHAR(12)`. As dimensões possuem códigos como chaves primárias e descrições como campos textuais. `controle_carga` identifica o arquivo original e guarda metadados como competência de declaração, linhas lidas e data de carga.

As chaves compostas estabelecem granularidade única em cada tabela fato, com chaves estrangeiras para as dimensões correspondentes. O modelo privilegia consultas analíticas e evita repetir descrições textuais em milhões de linhas.

### 3.2 Nuvem e limite de armazenamento

A implantação utiliza o banco **`defaultdb`** no serviço gerenciado PostgreSQL do Aiven, com conexão protegida por SSL. Na verificação após a importação, `pg_database_size(current_database())` retornou **361 MB**. A soma dos tamanhos relatados por relação, incluindo índices, destacou `fato_movimentacao` com **293 MB** e `fato_perfil` com **60 MB**. As demais tabelas ocupam uma fração pequena do total.

Com referência nominal de **1 GB** para o plano gratuito, os 361 MB representam aproximadamente **36%** dessa capacidade. **Importante:** `pg_database_size` mede o tamanho lógico do banco e não é a mesma métrica de uso de disco do serviço Aiven; a ocupação real da instância deve ser confirmada no painel do provedor. Não se recomenda preencher toda a capacidade devido ao crescimento, metadados, logs e operações de manutenção.

**Estratégia de otimização:** preservar arquivos brutos fora do banco, carregar somente fatos agregados, separar fatos por grão analítico, usar tipos compactos, manter índices justificáveis e monitorar a ocupação.

### 3.3 Verificações já realizadas

| Verificação | Resultado observado |
|---|---|
| Conexão Python → Aiven | Bem-sucedida |
| Execução do carregador | `IMPORTACAO FINALIZADA` |
| Ausência de `competencia` em `fato_movimentacao` | 0 |
| Ausência de `competencia` em `fato_perfil` | 0 |
| Saldos diferentes de admissões menos desligamentos | 0 em ambas as tabelas |
| Código de UF sem correspondência em `dim_uf` (`fato_movimentacao`, códigos não nulos) | 0 |
| Competência mínima e máxima, ambas as tabelas fato | 2020-01-01 a 2025-12-01 |
| Tamanho lógico do banco | 361 MB |

Os testes acima demonstram consistência **nos critérios efetivamente consultados**, mas não substituem uma auditoria de todas as chaves, de todas as competências e dos totais entre as duas tabelas fato. O arquivo `AUDITORIA_FINAL.sql` acompanha a entrega para complementar essa comprovação.

### 3.4 Limitações e riscos

- Os dados refletem os arquivos de declaração usados pela equipe até dezembro de 2025; competências recentes podem ser revistas por declarações atrasadas e exclusões posteriores.
- O README registra discrepâncias pequenas entre saldos ajustados históricos e séries oficiais de data de corte diferente, e uma diferença de 1.745 para janeiro de 2025; a comparação deve sempre informar a data-base da extração.
- O recorte agregado não permite recuperar microdados nem cruzar dimensões omitidas ou intencionalmente separadas.
- A verificação no painel Aiven e a auditoria completa das dimensões ainda devem integrar as evidências finais.

## 4. Evidências e entrega

Anexar ao repositório:

1. `README.md` atualizado para mencionar que a implantação final está no **Aiven / defaultdb** (em vez de somente no banco local `BigData`) e com as medições atuais de 361 MB, distinguindo os dois ambientes.
2. `importar_aiven.py`, `requirements.txt`, `scripts/`, `sql/`, `.env.example` (sem segredos) e `AUDITORIA_FINAL.sql`.
3. Este relatório e capturas do serviço Aiven com status em operação e tamanho em disco, da estrutura das 9 tabelas e dos resultados de consultas SQL.
4. Referência à fonte oficial e instruções para obter os microdados originais e reconstruir a pasta `BasesDados`.

**Nunca publicar** `.env`, credenciais, chaves de serviço, arquivos brutos de grande porte ou dados pessoais por engano. Verificar também o histórico do Git antes de disponibilizar o repositório.

## 5. Conclusão

O projeto produziu duas tabelas fato e seis dimensões a partir dos microdados públicos do Novo CAGED, com rastreabilidade de 212 arquivos de origem. Foram carregadas **2.188.650 linhas nas tabelas fato** e **2.188.948 linhas no total**, considerando controle e dimensões. A medição lógica pós-carga foi de **361 MB**, compatível com a estratégia de agregação adotada para o plano de armazenamento limitado. A carga executou até a mensagem de conclusão e os testes básicos de competência, saldo e relacionamento por UF tiveram resultado satisfatório. Permanecem a auditoria complementar, a captura de evidências visuais e a atualização/publicação final do repositório.
