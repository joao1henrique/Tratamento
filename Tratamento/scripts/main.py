# Roda o processo completo: tratar -> carregar no banco -> validar.
# Uso (de dentro da pasta Tratamento): python scripts/main.py
from tratar_dados import tratar_tudo
from carregar_banco import carregar_tudo
from validar import validar_tudo

if __name__ == "__main__":
    print("===== 1) Tratamento dos arquivos =====")
    tratar_tudo()
    print("\n===== 2) Carga no banco =====")
    carregar_tudo()
    print("\n===== 3) Validacao =====")
    validar_tudo()
