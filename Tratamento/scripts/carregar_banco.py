# Cria as tabelas (roda o criar_tabelas.sql) e carrega dimensoes, fatos e controle_carga.
import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
import config
from tratar_dados import CHAVES_FATO, CHAVES_PERFIL, MEDIDAS

# Coluna do fato -> dimensao onde o codigo precisa existir
COLUNAS_DIMENSOES = {
    "uf": "dim_uf",
    "setor": "dim_setor",
    "sexo": "dim_sexo",
    "raca_cor": "dim_raca_cor",
    "faixa_etaria": "dim_faixa_etaria",
    "tipo_movimentacao": "dim_tipo_movimentacao",
}


def conectar(nome_banco):
    endereco = URL.create("postgresql+psycopg2", username=config.DB_USER, password=config.DB_PASSWORD,
                          host=config.DB_HOST, port=config.DB_PORT, database=nome_banco)
    return create_engine(endereco)


def criar_banco_se_nao_existir():
    # Conecta no banco padrao "postgres" so para verificar/criar o nosso banco.
    # CREATE DATABASE nao pode rodar dentro de transacao, por isso o AUTOCOMMIT.
    engine = conectar("postgres").execution_options(isolation_level="AUTOCOMMIT")
    with engine.connect() as conexao:
        existe = conexao.execute(text("SELECT 1 FROM pg_database WHERE datname = :nome"),
                                 {"nome": config.DB_NAME}).fetchone()
        if existe:
            print("Banco", config.DB_NAME, "ja existe")
        else:
            # Aspas porque o nome tem letras maiusculas
            conexao.execute(text('CREATE DATABASE "' + config.DB_NAME + '"'))
            print("Banco", config.DB_NAME, "criado")


def criar_tabelas(engine):
    with open(config.ARQUIVO_SQL, encoding="utf-8") as arquivo:
        comandos = arquivo.read()
    with engine.begin() as conexao:
        conexao.exec_driver_sql(comandos)
    print("Tabelas criadas")


def ler_aba_do_layout(aba):
    # Cada aba do layout do MTE tem duas colunas: codigo e descricao
    tabela = pd.read_excel(config.ARQUIVO_LAYOUT, sheet_name=aba, usecols=[0, 1])
    tabela.columns = ["codigo", "descricao"]
    return tabela.dropna()


def classificar_grupo(codigo):
    if codigo in config.TIPOS_ADMISSAO:
        return "Admissão"
    if codigo == config.NAO_IDENTIFICADO["tipo_movimentacao"]:
        return "Não identificado"
    return "Desligamento"


def classificar_subgrupo(codigo):
    if codigo in config.TIPOS_ADMISSAO:
        return "admissão"
    if codigo == config.NAO_IDENTIFICADO["tipo_movimentacao"]:
        return "não identificado"
    return config.SUBGRUPO_DESLIGAMENTO.get(codigo, "outros")


def carregar_dimensoes(engine):
    dim_uf = ler_aba_do_layout("uf").rename(columns={"descricao": "nome"})
    dim_uf["sigla"] = dim_uf["codigo"].map(config.SIGLA_UF)
    dim_uf["regiao"] = (dim_uf["codigo"] // 10).map(config.REGIAO)

    dim_tipo = ler_aba_do_layout("tipomovimentação")
    dim_tipo["grupo"] = dim_tipo["codigo"].apply(classificar_grupo)
    dim_tipo["subgrupo"] = dim_tipo["codigo"].apply(classificar_subgrupo)

    # A faixa etaria nao existe no layout: vem do config
    faixas = []
    for codigo, descricao, idade_minima, idade_maxima in config.FAIXAS_ETARIAS:
        faixas.append({"codigo": codigo, "descricao": descricao})
    faixas.append({"codigo": config.NAO_IDENTIFICADO["faixa_etaria"], "descricao": "Não identificado"})

    dimensoes = {
        "dim_uf": dim_uf,
        "dim_setor": ler_aba_do_layout("seção"),
        "dim_sexo": ler_aba_do_layout("sexo"),
        "dim_raca_cor": ler_aba_do_layout("raçacor"),
        "dim_faixa_etaria": pd.DataFrame(faixas),
        "dim_tipo_movimentacao": dim_tipo,
    }
    for nome, tabela in dimensoes.items():
        tabela.to_sql(nome, engine, if_exists="append", index=False)
        print(nome, "-", len(tabela), "linhas")
    return dimensoes


def carregar_fato(engine, dimensoes, nome_tabela, final_do_arquivo, chaves):
    # Junta os CSVs de todos os arquivos (MOV, FOR e EXC)
    pedacos = []
    for arquivo in sorted(os.listdir(config.PASTA_SAIDA)):
        if arquivo.endswith(final_do_arquivo):
            pedacos.append(pd.read_csv(os.path.join(config.PASTA_SAIDA, arquivo), parse_dates=["competencia"]))
    fato = pd.concat(pedacos)

    # Codigo que nao existe na dimensao vira "Nao identificado" (senao a chave estrangeira falha)
    for coluna, nome_dimensao in COLUNAS_DIMENSOES.items():
        if coluna in chaves:
            desconhecidos = ~fato[coluna].isin(dimensoes[nome_dimensao]["codigo"])
            if desconhecidos.sum() > 0:
                print("Codigos desconhecidos em", coluna, ":", fato.loc[desconhecidos, coluna].unique())
                fato.loc[desconhecidos, coluna] = config.NAO_IDENTIFICADO[coluna]

    # Os arquivos FOR e EXC trazem movimentacoes de meses anteriores. Somando tudo pela
    # competencia da movimentacao, cada linha fica com o valor ajustado: MOV + FOR - EXC
    # (as exclusoes ja estao com sinal negativo nos CSVs).
    fato = fato.groupby(chaves)[MEDIDAS].sum().reset_index()

    print("Carregando", nome_tabela, ":", len(fato), "linhas...")
    fato.to_sql(nome_tabela, engine, if_exists="append", index=False, chunksize=10000, method="multi")


def carregar_controle(engine):
    # Uma linha por arquivo original, calculada a partir do CSV agregado dele
    controle = []
    for arquivo in sorted(os.listdir(config.PASTA_SAIDA)):
        if arquivo.endswith("_fato.csv"):
            agregado = pd.read_csv(os.path.join(config.PASTA_SAIDA, arquivo))
            # Nome do arquivo: CAGED + tipo (3 letras) + AAAAMM
            nome = arquivo.replace("_fato.csv", "")
            controle.append({
                "nome_arquivo": nome + ".7z",
                "tipo": nome[5:8],
                "competencia_declaracao": pd.to_datetime(nome[8:14], format="%Y%m"),
                "linhas_lidas": (agregado["qtd_admissoes"] + agregado["qtd_desligamentos"]).abs().sum(),
                "linhas_salario_valido": agregado["qtd_salario_valido"].abs().sum(),
                "saldo": agregado["saldo"].sum(),
                "data_carga": datetime.now(),
            })
    pd.DataFrame(controle).to_sql("controle_carga", engine, if_exists="append", index=False)
    print("controle_carga -", len(controle), "arquivos")


def carregar_tudo():
    criar_banco_se_nao_existir()
    engine = conectar(config.DB_NAME)
    criar_tabelas(engine)
    dimensoes = carregar_dimensoes(engine)
    carregar_fato(engine, dimensoes, "fato_movimentacao", "_fato.csv", CHAVES_FATO)
    carregar_fato(engine, dimensoes, "fato_perfil", "_perfil.csv", CHAVES_PERFIL)
    carregar_controle(engine)


if __name__ == "__main__":
    carregar_tudo()
