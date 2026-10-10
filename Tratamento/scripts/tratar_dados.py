# Le os arquivos do Novo CAGED em pedacos (chunks), limpa, agrega
# e salva dois CSVs agregados por arquivo na pasta saida/ (um para cada tabela fato).
import os
import time
import pandas as pd
import py7zr
import config

# fato_movimentacao: detalhe por setor e tipo de movimentacao
CHAVES_FATO = ["competencia", "uf", "setor", "sexo", "raca_cor", "tipo_movimentacao"]
# fato_perfil: detalhe por faixa etaria (sem setor e sem tipo, para ficar pequena)
CHAVES_PERFIL = ["competencia", "uf", "sexo", "raca_cor", "faixa_etaria", "grupo"]
MEDIDAS = ["qtd_admissoes", "qtd_desligamentos", "saldo", "qtd_salario_valido", "soma_salario", "soma_horas"]


def listar_arquivos():
    # Monta a lista de arquivos .7z a partir dos anos e tipos do config
    arquivos = []
    for ano in config.ANOS:
        for mes in range(1, 13):
            competencia = str(ano) + str(mes).zfill(2)
            if config.COMPETENCIAS_TESTE and competencia not in config.COMPETENCIAS_TESTE:
                continue
            for origem, pasta in config.PASTAS_ORIGEM.items():
                nome = "CAGED" + origem + competencia
                caminho = os.path.join(config.PASTA_CAGED, pasta, str(ano), nome + ".7z")
                # Alguns meses de 2020 nao tem FOR/EXC, por isso o teste
                if os.path.exists(caminho):
                    arquivos.append([nome, origem, caminho])
    return arquivos


def texto_para_numero(coluna):
    # Os arquivos usam virgula como separador decimal
    coluna = coluna.str.replace(",", ".")
    return pd.to_numeric(coluna, errors="coerce")


def limpar_chunk(df, origem):
    df = df.rename(columns=config.COLUNAS)

    # Competencia da movimentacao (AAAAMM) vira data no primeiro dia do mes
    df["competencia"] = pd.to_datetime(df["competenciamov"], format="%Y%m")

    # Codigos viram inteiros. Vazio ou invalido vira "Nao identificado" (nao descartamos linhas)
    for coluna in ["uf", "sexo", "raca_cor", "tipo_movimentacao"]:
        df[coluna] = pd.to_numeric(df[coluna], errors="coerce")
        df[coluna] = df[coluna].fillna(config.NAO_IDENTIFICADO[coluna]).astype(int)
    df["setor"] = df["setor"].fillna(config.NAO_IDENTIFICADO["setor"])

    df["saldo"] = pd.to_numeric(df["saldo"], errors="coerce").fillna(0).astype(int)
    df["salario"] = texto_para_numero(df["salario"])
    df["horas_contratuais"] = texto_para_numero(df["horas_contratuais"]).fillna(0)

    # Faixa etaria: comeca como "Nao identificado" e recebe o codigo da faixa onde a idade se encaixa
    idade = pd.to_numeric(df["idade"], errors="coerce")
    df["faixa_etaria"] = config.NAO_IDENTIFICADO["faixa_etaria"]
    for codigo, descricao, idade_minima, idade_maxima in config.FAIXAS_ETARIAS:
        df.loc[(idade >= idade_minima) & (idade <= idade_maxima), "faixa_etaria"] = codigo

    # Grupo da movimentacao pelo sinal original do saldo (+1 admissao, -1 desligamento)
    df["grupo"] = "Desligamento"
    df.loc[df["saldo"] == 1, "grupo"] = "Admissão"

    # Salario valido: entre 0,3 e 150 salarios minimos do ano da movimentacao
    minimo = df["competencia"].dt.year.map(config.SALARIO_MINIMO)
    salario_valido = (df["salario"] >= config.SALARIO_MINIMOS_DE * minimo) & \
                     (df["salario"] <= config.SALARIO_MINIMOS_ATE * minimo)

    # Todos os registros entram nas contagens
    df["qtd_admissoes"] = (df["saldo"] == 1).astype(int)
    df["qtd_desligamentos"] = (df["saldo"] == -1).astype(int)

    # Salario e horas so sao somados quando o salario e valido,
    # assim soma_salario / soma_horas da um salario-hora coerente
    df["qtd_salario_valido"] = salario_valido.astype(int)
    df["soma_salario"] = df["salario"].where(salario_valido, 0)
    df["soma_horas"] = df["horas_contratuais"].where(salario_valido, 0)

    # Exclusoes entram com sinal invertido para subtrair do que ja foi contado
    if origem == "EXC":
        df[MEDIDAS] = df[MEDIDAS] * -1
    return df


def agregar(df, chaves):
    return df.groupby(chaves)[MEDIDAS].sum().reset_index()


def tratar_arquivo(nome, origem, caminho_7z):
    inicio = time.time()
    caminho_fato = os.path.join(config.PASTA_SAIDA, nome + "_fato.csv")
    caminho_perfil = os.path.join(config.PASTA_SAIDA, nome + "_perfil.csv")

    # Controle de duplicidade por arquivo: se ja foi tratado, nao trata de novo
    if os.path.exists(caminho_fato) and os.path.exists(caminho_perfil):
        print(nome, "- ja tratado, pulando")
        return

    # Descompacta na pasta temp (os dados brutos nao sao alterados)
    with py7zr.SevenZipFile(caminho_7z, mode="r") as compactado:
        compactado.extractall(path=config.PASTA_TEMP)
    caminho_txt = os.path.join(config.PASTA_TEMP, nome + ".txt")

    # Le em pedacos e so as colunas necessarias, para nao estourar a memoria
    leitor = pd.read_csv(caminho_txt, sep=config.SEPARADOR, encoding=config.ENCODING,
                         usecols=list(config.COLUNAS), dtype=str, chunksize=config.TAMANHO_CHUNK)
    linhas_lidas = 0
    pedacos_fato = []
    pedacos_perfil = []
    for chunk in leitor:
        linhas_lidas = linhas_lidas + len(chunk)
        chunk = limpar_chunk(chunk, origem)
        # As duas agregacoes saem da mesma leitura
        pedacos_fato.append(agregar(chunk, CHAVES_FATO))
        pedacos_perfil.append(agregar(chunk, CHAVES_PERFIL))

    # A mesma combinacao pode aparecer em mais de um chunk, entao soma de novo
    fato = agregar(pd.concat(pedacos_fato), CHAVES_FATO)
    perfil = agregar(pd.concat(pedacos_perfil), CHAVES_PERFIL)
    fato.to_csv(caminho_fato, index=False)
    perfil.to_csv(caminho_perfil, index=False)
    os.remove(caminho_txt)

    # Conferencia: nenhuma linha pode se perder na agregacao
    linhas_contadas = (fato["qtd_admissoes"] + fato["qtd_desligamentos"]).abs().sum()
    if linhas_contadas != linhas_lidas:
        print("ATENCAO:", nome, "leu", linhas_lidas, "linhas mas contou", linhas_contadas)

    print(nome, "- linhas lidas:", linhas_lidas, "| fato:", len(fato), "| perfil:", len(perfil),
          "| saldo:", fato["saldo"].sum(), "| tempo:", round(time.time() - inicio), "s")


def tratar_tudo():
    arquivos = listar_arquivos()
    print("Arquivos para tratar:", len(arquivos))
    for nome, origem, caminho in arquivos:
        tratar_arquivo(nome, origem, caminho)


if __name__ == "__main__":
    tratar_tudo()
