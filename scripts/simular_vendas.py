# =========================================================
# SIMULA O TRABALHO DO TIME DE VENDAS
# (os vendedores são fictícios, então simulamos o resultado
#  usando a resposta real do Kaggle: comprou ou não)
# =========================================================
import random
from pathlib import Path

import psycopg2

PASTA = Path(__file__).resolve().parents[1]

# Lê usuário e senha do arquivo .env
config = {}
for linha in (PASTA / ".env").read_text().splitlines():
    if "=" in linha and not linha.startswith("#"):
        chave, valor = linha.split("=", 1)
        config[chave.strip()] = valor.strip()

conexao = psycopg2.connect(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
    dbname=config["POSTGRES_DB"],
)
cursor = conexao.cursor()

# 1. Cerca de 70% dos leads enviados passam para "em contato"
cursor.execute("UPDATE leads SET status = 'em_contato' WHERE status = 'enviado' AND random() < 0.7")
em_contato = cursor.rowcount

# 2. Metade dos leads em contato fecha: ganho ou perdido
cursor.execute("SELECT lead_id, converted_historical FROM leads WHERE status = 'em_contato'")
ganhos = perdidos = 0
for lead_id, comprou in cursor.fetchall():
    if random.random() < 0.5:
        continue  # ainda em negociação
    resultado = comprou == 1          # usa a resposta real do Kaggle
    if random.random() < 0.1:
        resultado = not resultado     # 10% de imprevistos
    cursor.execute(
        "UPDATE leads SET status = %s, closed_at = now() WHERE lead_id = %s",
        ("ganho" if resultado else "perdido", lead_id),
    )
    if resultado:
        ganhos += 1
    else:
        perdidos += 1

conexao.commit()
conexao.close()
print(f"{em_contato} leads passaram para 'em contato'")
print(f"{ganhos} ganhos e {perdidos} perdidos")