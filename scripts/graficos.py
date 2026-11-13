# =========================================================
# GRÁFICOS DO PROJETO (salvos na pasta docs/img)
# =========================================================
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

PASTA = Path(__file__).resolve().parents[1]
SAIDA = PASTA / "docs" / "img"
SAIDA.mkdir(parents=True, exist_ok=True)  # cria a pasta, se ainda não existir

df = pd.read_csv(PASTA / "data" / "leads_pontuados.csv")
MEDIA = df["converted_historical"].mean() * 100  # conversão geral, em %

# Cores: troque à vontade (códigos de cor em hexadecimal)
DESTAQUE = "#2a78d6"   # barra em destaque
NEUTRA = "#c9c8c3"     # demais barras
TEXTO = "#1d1d1b"
CINZA = "#6b6a66"


def grafico(arquivo, titulo, subtitulo, nomes, valores, qtds):
    fig, ax = plt.subplots(figsize=(10, 10), dpi=120)
    cores = [DESTAQUE] + [NEUTRA] * (len(valores) - 1)  # só a primeira barra em destaque
    barras = ax.bar(nomes, valores, color=cores, width=0.62, zorder=3)

    # linha tracejada com a média geral
    ax.axhline(MEDIA, color=TEXTO, lw=1.4, ls="--", zorder=4)

    # número em cima de cada barra e quantidade de leads dentro dela
    for i, (barra, valor, qtd) in enumerate(zip(barras, valores, qtds)):
        x = barra.get_x() + barra.get_width() / 2
        ax.text(x, valor + 1.5, f"{valor:.0f}%", ha="center", fontsize=24, fontweight="bold", color=TEXTO)
        ax.text(x, 2.5, f"{qtd:,}\nleads".replace(",", "."), ha="center", fontsize=13,
                color="white" if i == 0 else TEXTO, zorder=5)

    # aparência dos eixos
    ax.set_ylim(0, 105)
    ax.set_yticks([0, 25, 50, 75, 100])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"], fontsize=13, color=CINZA)
    ax.tick_params(axis="x", labelsize=17, colors=TEXTO, length=0, pad=12)
    ax.tick_params(axis="y", length=0)
    ax.grid(axis="y", color="#e6e5e1", zorder=0)
    for borda in ax.spines.values():
        borda.set_visible(False)

    # títulos e rodapé
    media_txt = f"{MEDIA:.1f}".replace(".", ",")
    fig.text(0.07, 0.95, titulo, fontsize=27, fontweight="bold", color=TEXTO, va="top")
    fig.text(0.07, 0.885, subtitulo, fontsize=16, color=CINZA, va="top")
    fig.text(0.07, 0.845, f"- - -  linha tracejada: média geral de {media_txt}%", fontsize=14, color=TEXTO, va="top")
    fig.text(0.07, 0.025, "Dataset Leads (Kaggle), " + f"{len(df):,} leads".replace(",", "."), fontsize=12, color=CINZA)
    fig.subplots_adjust(left=0.1, right=0.95, top=0.78, bottom=0.15)

    fig.savefig(SAIDA / arquivo, facecolor="white")
    plt.close(fig)
    print("Gráfico salvo:", SAIDA / arquivo)


# ---------- Gráfico 1: conversão por faixa do score ----------
faixas = df.groupby("score_band")["converted_historical"].agg(["count", "mean"])
faixas = faixas.loc[["quente", "morno", "frio"]]  # coloca na ordem certa
grafico(
    "conversao_por_faixa.png",
    f"Leads quentes convertem {faixas.loc['quente', 'mean'] * 100:.0f}%",
    "Conversão real por faixa do score de 0 a 100",
    ["Quente\n(70 a 100)", "Morno\n(40 a 69)", "Frio\n(0 a 39)"],
    faixas["mean"] * 100,
    faixas["count"],
)

# ---------- Gráfico 2: conversão por origem ----------
NOMES = {
    "Reference": "Indicação",
    "Google": "Google",
    "Organic Search": "Busca\norgânica",
    "Direct Traffic": "Acesso\ndireto",
    "Olark Chat": "Chat do\nsite",
}
origens = df.groupby("lead_source")["converted_historical"].agg(["count", "mean"])
origens = origens[origens["count"] > 500].sort_values("mean", ascending=False)  # só as grandes
grafico(
    "conversao_por_origem.png",
    "Indicação converte mais que o dobro",
    "Conversão por origem do lead (origens com mais de 500 leads)",
    [NOMES.get(o, o) for o in origens.index],
    origens["mean"] * 100,
    origens["count"],
)