# =========================================================
# PARTE 1: LIMPEZA DOS DADOS
# =========================================================
from pathlib import Path

import numpy as np
import pandas as pd

PASTA = Path(__file__).resolve().parents[1]  # a pasta lead-engine

# Colunas do Kaggle que vamos usar -> nome novo, em minúsculas e sem espaços
COLUNAS = {
    "Prospect ID": "prospect_id",
    "Lead Number": "lead_id",
    "Lead Origin": "lead_origin",
    "Lead Source": "lead_source",
    "Do Not Email": "do_not_email",
    "Do Not Call": "do_not_call",
    "Converted": "converted_historical",
    "TotalVisits": "total_visits",
    "Total Time Spent on Website": "time_on_site_sec",
    "Page Views Per Visit": "pages_per_visit",
    "Last Activity": "last_activity",
    "Specialization": "specialization",
    "What is your current occupation": "occupation",
    "City": "city",
}
CATEGORICAS = ["lead_origin", "lead_source", "last_activity", "occupation", "specialization", "city"]
NUMERICAS = ["total_visits", "time_on_site_sec", "pages_per_visit"]

bruto = pd.read_csv(PASTA / "data" / "Leads.csv")
df = bruto[list(COLUNAS)].rename(columns=COLUNAS)

# "Select" = a pessoa não preencheu o campo no formulário -> vira vazio
df = df.replace("Select", np.nan)
df = df.drop_duplicates(subset="lead_id")

# "google" e "Google" são a mesma origem
df["lead_source"] = df["lead_source"].replace({"google": "Google"})

# Colunas de texto: vazio vira "Não informado"; categorias raras viram "Outros"
for col in CATEGORICAS:
    df[col] = df[col].fillna("Não informado")
    contagem = df[col].value_counts()
    raras = contagem[contagem < 30].index
    df.loc[df[col].isin(raras), col] = "Outros"

# Colunas de número: vazio vira a mediana; valores exagerados são limitados
for col in NUMERICAS:
    df[col] = pd.to_numeric(df[col], errors="coerce")
    df[col] = df[col].fillna(df[col].median())
    df[col] = df[col].clip(upper=df[col].quantile(0.99))

# "Yes"/"No" vira verdadeiro/falso
for col in ["do_not_email", "do_not_call"]:
    df[col] = df[col].eq("Yes")

print("Leads após a limpeza:", len(df))
print(df["lead_source"].value_counts().head(8))


# =========================================================
# PARTE 2: SCORE (nota de 0 a 100 para cada lead)
# =========================================================
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import cross_val_predict
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

CORTE_QUENTE = 70  # a partir desta nota, o lead é "quente"

# O modelo: prepara as colunas e aplica uma regressão logística
modelo = Pipeline([
    ("preparo", ColumnTransformer([
        ("texto", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
        ("numeros", StandardScaler(), NUMERICAS),
    ])),
    ("regressao", LogisticRegression(max_iter=2000)),
])

X = df[CATEGORICAS + NUMERICAS]   # as características de cada lead
y = df["converted_historical"]    # a resposta: comprou (1) ou não (0)

# Chance de compra de cada lead, calculada por validação cruzada (5 rodadas)
chance = cross_val_predict(modelo, X, y, cv=5, method="predict_proba")[:, 1]
print("\nAUC do modelo:", round(roc_auc_score(y, chance), 3))

df["lead_score"] = np.round(chance * 100).astype(int)
df["score_band"] = pd.cut(
    df["lead_score"],
    bins=[-1, 39, CORTE_QUENTE - 1, 100],
    labels=["frio", "morno", "quente"],
).astype(str)

print("\nLeads por faixa:")
print(df["score_band"].value_counts())
print("\nConversão real por faixa:")
print(df.groupby("score_band")["converted_historical"].mean().round(3))


# =========================================================
# PARTE 3: CONTATOS FICTÍCIOS (o dataset não tem dados pessoais)
# =========================================================
import re
import unicodedata

from faker import Faker

fake = Faker("pt_BR")
Faker.seed(42)  # sempre gera os mesmos nomes, toda vez que rodar


def para_email(nome):
    """'Dra. Júlia Araújo' -> 'julia.araujo'"""
    texto = unicodedata.normalize("NFKD", nome).encode("ascii", "ignore").decode().lower()
    palavras = [p for p in re.sub(r"[^a-z ]", "", texto).split()
                if p not in {"dr", "dra", "sr", "sra", "srta"}]
    return ".".join(palavras)


nomes = [fake.name() for _ in range(len(df))]
df["full_name"] = nomes
df["email"] = [f"{para_email(n)}.{i}@exemplo.com" for i, n in zip(df["lead_id"], nomes)]
df["phone"] = [fake.cellphone_number() for _ in range(len(df))]

print("\nExemplo de leads prontos:")
print(df[["full_name", "email", "lead_score", "score_band"]].head().to_string())


# =========================================================
# PARTE 4: GRAVAR NO BANCO DE DADOS
# Uso:  python scripts/load_leads.py       -> grava 300 leads novos
#       python scripts/load_leads.py 50    -> grava 50 leads novos
# =========================================================
import sys

import psycopg2
from psycopg2.extras import execute_values

# Lê usuário e senha do arquivo .env
config = {}
for linha in (PASTA / ".env").read_text().splitlines():
    if "=" in linha and not linha.startswith("#"):
        chave, valor = linha.split("=", 1)
        config[chave.strip()] = valor.strip()

quantidade = int(sys.argv[1]) if len(sys.argv) > 1 else 300

conexao = psycopg2.connect(
    host=config["POSTGRES_HOST"],
    port=config["POSTGRES_PORT"],
    user=config["POSTGRES_USER"],
    password=config["POSTGRES_PASSWORD"],
    dbname=config["POSTGRES_DB"],
)
cursor = conexao.cursor()

# Separa só os leads que ainda não estão no banco e sorteia a quantidade pedida
cursor.execute("SELECT lead_id FROM leads")
ja_no_banco = {linha[0] for linha in cursor.fetchall()}
novos = df[~df["lead_id"].isin(ja_no_banco)].sample(frac=1).head(quantidade)

colunas = ["lead_id", "prospect_id", "full_name", "email", "phone", "lead_origin",
           "lead_source", "last_activity", "occupation", "specialization", "city",
           "total_visits", "time_on_site_sec", "pages_per_visit", "do_not_email",
           "do_not_call", "converted_historical", "lead_score", "score_band"]
linhas = [tuple(l) for l in novos[colunas].astype(object).itertuples(index=False)]

execute_values(
    cursor,
    f"INSERT INTO leads ({', '.join(colunas)}) VALUES %s ON CONFLICT (lead_id) DO NOTHING",
    linhas,
)
conexao.commit()
conexao.close()

print(f"\n{len(linhas)} leads novos gravados no banco.")
print(f"Total no banco agora: {len(ja_no_banco) + len(linhas)}")