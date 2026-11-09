import pandas as pd

df = pd.read_csv("data/Leads.csv")
print(df.shape)

print(df["Converted"].mean())

por_origem = df.groupby("Lead Source")["Converted"].agg(["count", "mean"])
print(por_origem.sort_values("count", ascending=False).head(10))