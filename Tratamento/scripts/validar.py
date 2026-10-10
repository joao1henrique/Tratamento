# Mostra contagens, tamanho das tabelas e o saldo por mes para conferir com o MTE.
import pandas as pd
import config
from carregar_banco import conectar

TABELAS = ["dim_uf", "dim_setor", "dim_sexo", "dim_raca_cor", "dim_faixa_etaria", "dim_tipo_movimentacao",
           "fato_movimentacao", "fato_perfil", "controle_carga"]


def mostrar_tamanhos(engine):
    print("\n--- Linhas e tamanho de cada tabela (com indices) ---")
    total_bytes = 0
    for tabela in TABELAS:
        consulta = "SELECT COUNT(*) AS linhas, pg_total_relation_size('" + tabela + "') AS bytes FROM " + tabela
        resultado = pd.read_sql(consulta, engine)
        linhas = resultado["linhas"][0]
        tamanho = resultado["bytes"][0]
        total_bytes = total_bytes + tamanho
        print(tabela.ljust(24), str(linhas).rjust(10), "linhas", str(round(tamanho / 1024 / 1024, 2)).rjust(10), "MB")
    print("TOTAL DAS TABELAS:", round(total_bytes / 1024 / 1024, 2), "MB (limite do Aiven: 1024 MB)")

    banco = pd.read_sql("SELECT pg_database_size(current_database()) AS bytes", engine)
    print("BANCO INTEIRO (com catalogo do Postgres):", round(banco["bytes"][0] / 1024 / 1024, 2), "MB")


def mostrar_controle(engine):
    print("\n--- Controle de carga (resumo por tipo) ---")
    consulta = """
        SELECT tipo, COUNT(*) AS arquivos, SUM(linhas_lidas) AS linhas_lidas,
               SUM(linhas_salario_valido) AS linhas_salario_valido, SUM(saldo) AS saldo
        FROM controle_carga
        GROUP BY tipo
        ORDER BY tipo
    """
    print(pd.read_sql(consulta, engine).to_string(index=False))


def conferir_fatos(engine):
    # As duas tabelas fato vem dos mesmos dados, entao os totais precisam ser iguais
    print("\n--- Totais das duas tabelas fato (precisam ser iguais) ---")
    for tabela in ["fato_movimentacao", "fato_perfil"]:
        consulta = "SELECT SUM(qtd_admissoes) AS admissoes, SUM(qtd_desligamentos) AS desligamentos, " \
                   "SUM(saldo) AS saldo FROM " + tabela
        resultado = pd.read_sql(consulta, engine)
        print(tabela.ljust(20), "admissoes:", resultado["admissoes"][0],
              "| desligamentos:", resultado["desligamentos"][0], "| saldo:", resultado["saldo"][0])


def mostrar_saldo_por_mes(engine):
    # saldo_sem_ajuste = saldo do arquivo MOV do mes (so o declarado no prazo; numero divulgado no mes)
    # saldo_com_ajuste = no prazo + fora do prazo - exclusoes (o que esta no fato)
    consulta = """
        SELECT f.competencia, c.saldo AS saldo_sem_ajuste, f.saldo_com_ajuste, f.admissoes, f.desligamentos
        FROM (
            SELECT competencia,
                   SUM(saldo) AS saldo_com_ajuste,
                   SUM(qtd_admissoes) AS admissoes,
                   SUM(qtd_desligamentos) AS desligamentos
            FROM fato_movimentacao
            GROUP BY competencia
        ) f
        LEFT JOIN controle_carga c ON c.competencia_declaracao = f.competencia AND c.tipo = 'MOV'
        ORDER BY f.competencia
    """
    print("\n--- Saldo nacional por mes ---")
    print(pd.read_sql(consulta, engine).to_string(index=False))


def validar_tudo():
    engine = conectar(config.DB_NAME)
    mostrar_tamanhos(engine)
    mostrar_controle(engine)
    conferir_fatos(engine)
    mostrar_saldo_por_mes(engine)


if __name__ == "__main__":
    validar_tudo()
