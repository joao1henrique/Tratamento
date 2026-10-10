"""Importa CSVs tratados do Novo CAGED no Aiven sem carregar tudo em RAM.
Execute na raiz Tratamento (onde estao scripts/ e saida/).
Requer fatos e controle_carga vazios. Se uma execucao falhar, limpe SOMENTE
essas 3 tabelas antes de reiniciar, com cuidado. Nunca apaga dimensoes.
"""
import os
import sys
from pathlib import Path

import pandas as pd
from psycopg2.extras import execute_values
from sqlalchemy import text

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
import config  # noqa: E402
from carregar_banco import conectar, carregar_controle, COLUNAS_DIMENSOES  # noqa: E402
from tratar_dados import CHAVES_FATO, CHAVES_PERFIL, MEDIDAS  # noqa: E402

TABELAS = (
    ("fato_movimentacao", "_fato.csv", CHAVES_FATO),
    ("fato_perfil", "_perfil.csv", CHAVES_PERFIL),
)


def importar():
    pasta = Path(config.PASTA_SAIDA)
    if not pasta.is_dir():
        raise RuntimeError(f"Pasta de saida inexistente: {pasta}")
    engine = conectar("defaultdb")
    try:
        with engine.connect() as c:
            existentes = {t: c.execute(text(f"SELECT COUNT(*) FROM {t}")).scalar() for t in
                          ("fato_movimentacao", "fato_perfil", "controle_carga")}
            print("Contagem inicial:", existentes, flush=True)
            if any(existentes.values()):
                raise RuntimeError("Carga bloqueada: fatos ou controle_carga ja contem dados. "
                                   "Nao repetir: causaria duplicacao dos valores.")
            dim_codes = {
                coluna: set(c.execute(text(f"SELECT codigo FROM {tabela}")).scalars())
                for coluna, tabela in COLUNAS_DIMENSOES.items()
            }
        for tabela, sufixo, chaves in TABELAS:
            arquivos = sorted(pasta.glob(f"*{sufixo}"))
            if not arquivos:
                raise RuntimeError(f"Nenhum CSV encontrado com sufixo {sufixo}")
            nomes_colunas = chaves + MEDIDAS
            colunas_sql = ",".join(nomes_colunas)
            chave_sql = ",".join(chaves)
            alteracoes = ",".join(f"{m}={tabela}.{m}+EXCLUDED.{m}" for m in MEDIDAS)
            sql = (f"INSERT INTO {tabela} ({colunas_sql}) VALUES %s "
                   f"ON CONFLICT ({chave_sql}) DO UPDATE SET {alteracoes}")
            for num, arquivo in enumerate(arquivos, 1):
                # Um arquivo de cada vez. Agrega por chaves para garantir mesma
                # semantica do script original, incluindo MOV+FOR-EXC.
                df = pd.read_csv(arquivo, parse_dates=["competencia"])
                for coluna in chaves:
                    if coluna in dim_codes:
                        df.loc[~df[coluna].isin(dim_codes[coluna]), coluna] = config.NAO_IDENTIFICADO[coluna]
                df = df.groupby(chaves, as_index=False, sort=False)[MEDIDAS].sum()
                df["competencia"] = df["competencia"].dt.date
                # None e Decimal nao sao necessarios: tipos nativos do Python via itertuples
                valores = list(df[nomes_colunas].itertuples(index=False, name=None))
                raw = engine.raw_connection()
                try:
                    with raw.cursor() as cursor:
                        execute_values(cursor, sql, valores, page_size=1000)
                    raw.commit()
                except Exception:
                    raw.rollback()
                    raise
                finally:
                    raw.close()
                if num % 10 == 0 or num == len(arquivos):
                    print(f"{tabela}: {num}/{len(arquivos)} arquivos", flush=True)
            print(f"Carga terminada: {tabela}", flush=True)
        carregar_controle(engine)
        with engine.connect() as c:
            for tabela in ("fato_movimentacao", "fato_perfil", "controle_carga"):
                n = c.execute(text(f"SELECT COUNT(*) FROM {tabela}")).scalar()
                print(f"{tabela}: {n:,} registros", flush=True)
        print("IMPORTACAO FINALIZADA", flush=True)
    finally:
        engine.dispose()


if __name__ == "__main__":
    importar()
