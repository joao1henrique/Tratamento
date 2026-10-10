# Todas as configuracoes do projeto ficam aqui.
import os
from dotenv import load_dotenv

# ---------- Pastas (montadas a partir de onde este arquivo esta) ----------
PASTA_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PASTA_TRATAMENTO = os.path.dirname(PASTA_SCRIPTS)
PASTA_BASES = os.path.join(os.path.dirname(PASTA_TRATAMENTO), "BasesDados")
PASTA_CAGED = os.path.join(PASTA_BASES, "01_NOVO_CAGED")
PASTA_SAIDA = os.path.join(PASTA_TRATAMENTO, "saida")
PASTA_TEMP = os.path.join(PASTA_TRATAMENTO, "temp")
ARQUIVO_SQL = os.path.join(PASTA_TRATAMENTO, "sql", "criar_tabelas.sql")
ARQUIVO_LAYOUT = os.path.join(PASTA_CAGED, "documentacao", "Layout Novo Caged Movimentação.xlsx")

# Subpasta de cada tipo de arquivo (origem)
PASTAS_ORIGEM = {
    "MOV": "movimentacoes",   # declaradas no prazo
    "FOR": "fora_do_prazo",   # declaradas fora do prazo
    "EXC": "exclusoes",       # movimentacoes excluidas
}

# ---------- O que processar ----------
ANOS = [2020, 2021, 2022, 2023, 2024, 2025]

# Para testar com poucos arquivos, coloque as competencias aqui (ex.: ["202401"]).
# Lista vazia = processa todos os meses dos ANOS.
COMPETENCIAS_TESTE = []

# ---------- Leitura dos arquivos ----------
SEPARADOR = ";"
ENCODING = "utf-8"
TAMANHO_CHUNK = 500000

# Colunas usadas: nome original no arquivo -> nome tratado (minusculo, sem acento)
COLUNAS = {
    "competênciamov": "competenciamov",
    "uf": "uf",
    "seção": "setor",
    "saldomovimentação": "saldo",
    "idade": "idade",
    "horascontratuais": "horas_contratuais",
    "raçacor": "raca_cor",
    "sexo": "sexo",
    "tipomovimentação": "tipo_movimentacao",
    "salário": "salario",
}

# ---------- Codigos de "Nao identificado" (iguais aos do layout do MTE) ----------
NAO_IDENTIFICADO = {
    "uf": 99,
    "setor": "Z",
    "sexo": 9,
    "raca_cor": 9,
    "tipo_movimentacao": 99,
    "faixa_etaria": 99,
}

# ---------- Faixas etarias: codigo, descricao, idade minima, idade maxima ----------
# Idade vazia ou fora de 14 a 100 anos fica como "Nao identificado" (codigo 99)
FAIXAS_ETARIAS = [
    [1, "14 a 17", 14, 17],
    [2, "18 a 24", 18, 24],
    [3, "25 a 29", 25, 29],
    [4, "30 a 39", 30, 39],
    [5, "40 a 49", 40, 49],
    [6, "50 a 64", 50, 64],
    [7, "65 ou mais", 65, 100],
]

# ---------- Salario ----------
# Um valor por ano (o que valeu na maior parte do ano).
# Jan/2020 foi 1039 e jan-abr/2023 foi 1302, mas isso nao muda o filtro abaixo.
SALARIO_MINIMO = {2020: 1045, 2021: 1100, 2022: 1212, 2023: 1320, 2024: 1412, 2025: 1518}

# So entram na soma salarial os salarios entre 0,3 e 150 salarios minimos
SALARIO_MINIMOS_DE = 0.3
SALARIO_MINIMOS_ATE = 150

# ---------- Tipo de movimentacao ----------
TIPOS_ADMISSAO = [10, 20, 25, 35, 70, 97]

# Subgrupo dos desligamentos. O que nao estiver aqui vira "outros".
SUBGRUPO_DESLIGAMENTO = {
    31: "sem justa causa",
    32: "justa causa",
    40: "a pedido",
    43: "término de contrato",
    45: "término de contrato",
}

# ---------- UF: sigla e regiao (o layout so traz o nome) ----------
SIGLA_UF = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL", 28: "SE", 29: "BA",
    31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS",
    50: "MS", 51: "MT", 52: "GO", 53: "DF",
    99: "NI",
}

# O primeiro digito do codigo da UF indica a regiao
REGIAO = {1: "Norte", 2: "Nordeste", 3: "Sudeste", 4: "Sul", 5: "Centro-Oeste", 9: "Não identificado"}

# ---------- Banco de dados (lido do arquivo .env, nenhuma senha no codigo) ----------
load_dotenv(os.path.join(PASTA_TRATAMENTO, ".env"))
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
