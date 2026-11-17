# =========================================================
# GRÁFICOS DA OPERAÇÃO (dados direto do banco, salvos em docs/img)
# =========================================================
from pathlib import Path

import matplotlib.pyplot as plt
import psycopg2

PASTA = Path(__file__).resolve().parents[1]
SAIDA = PASTA / "docs" / "img"
SAIDA.mkdir(parents=True, exist_ok=True)

DESTAQUE = "#2a78d6"
NEUTRA = "#c9c8c3"
TEXTO = "#1d1d1b"
CINZA = "#6b6a66"

# Lê usuário e senha do arquivo .env e conecta no banco
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

# ---------- Consulta 1: leads recebidos por vendedor ----------
cursor.execute("""
    SELECT r.name, r.team, COUNT(d.dispatch_id) AS leads
      FROM sales_reps r
      LEFT JOIN lead_dispatches d ON d.rep_id = r.rep_id
     GROUP BY r.name, r.team, r.rep_id
     ORDER BY r.rep_id
""")
vendedores = cursor.fetchall()   # lista de (nome, time, quantidade)

# ---------- Consulta 2: funil dos leads quentes ----------
cursor.execute("""
    SELECT
        COUNT(*)                                                   AS quentes,
        COUNT(*) FILTER (WHERE status <> 'novo')                   AS enviados,
        COUNT(*) FILTER (WHERE status IN ('em_contato', 'ganho', 'perdido')) AS contatados,
        COUNT(*) FILTER (WHERE status = 'ganho')                   AS ganhos,
        COUNT(*) FILTER (WHERE status = 'perdido')                 AS perdidos
      FROM leads
     WHERE score_band = 'quente'
""")
quentes, enviados, contatados, ganhos, perdidos = cursor.fetchone()
conexao.close()


def estilo(ax):
    ax.tick_params(length=0)
    for borda in ax.spines.values():
        borda.set_visible(False)


# ---------- Gráfico 1: distribuição entre vendedores ----------
fig, ax = plt.subplots(figsize=(10, 10), dpi=120)
nomes = [f"{nome}\n({time})" for nome, time, _ in vendedores]
qtds = [qtd for _, _, qtd in vendedores]
cores = [DESTAQUE if time == "enterprise" else NEUTRA for _, time, _ in vendedores]
barras = ax.bar(nomes, qtds, color=cores, width=0.6, zorder=3)
for barra, qtd in zip(barras, qtds):
    ax.text(barra.get_x() + barra.get_width() / 2, qtd + max(qtds) * 0.02, str(qtd),
            ha="center", fontsize=24, fontweight="bold", color=TEXTO)
ax.set_ylim(0, max(qtds) * 1.2 if max(qtds) else 1)
ax.set_yticks([])
ax.tick_params(axis="x", labelsize=16, colors=TEXTO, pad=10)
estilo(ax)
fig.text(0.07, 0.95, "Como o n8n distribuiu os leads", fontsize=27, fontweight="bold", color=TEXTO, va="top")
fig.text(0.07, 0.885, "Leads quentes enviados a cada vendedor, em rodízio por time", fontsize=16, color=CINZA, va="top")
fig.text(0.07, 0.845, "Azul: time enterprise (score 85+)   ·   Cinza: time smb (score 70 a 84)",
         fontsize=14, color=TEXTO, va="top")
fig.subplots_adjust(left=0.08, right=0.95, top=0.78, bottom=0.12)
fig.savefig(SAIDA / "leads_por_vendedor.png", facecolor="white")
plt.close(fig)
print("Gráfico salvo:", SAIDA / "leads_por_vendedor.png")

# ---------- Gráfico 2: funil dos leads quentes ----------
etapas = ["Leads quentes", "Enviados pelo n8n", "Contatados", "Vendas"]
valores = [quentes, enviados, contatados, ganhos]
fig, ax = plt.subplots(figsize=(10, 10), dpi=120)
y = list(range(len(etapas)))[::-1]   # de cima para baixo
cores = [NEUTRA, NEUTRA, NEUTRA, DESTAQUE]
ax.barh(y, valores, color=cores, height=0.6, zorder=3)
for posicao, valor in zip(y, valores):
    parte = f"  {valor}  ({valor / quentes:.0%} dos quentes)" if quentes else f"  {valor}"
    ax.text(valor, posicao, parte, va="center", fontsize=17, color=TEXTO)
ax.set_yticks(y)
ax.set_yticklabels(etapas, fontsize=17, color=TEXTO)
ax.set_xticks([])
ax.set_xlim(0, max(valores) * 1.7 if max(valores) else 1)
estilo(ax)
taxa = f"{ganhos / (ganhos + perdidos):.0%}" if (ganhos + perdidos) else "-"
fig.text(0.07, 0.95, "Funil dos leads quentes", fontsize=27, fontweight="bold", color=TEXTO, va="top")
fig.text(0.07, 0.885, "Do banco de dados até a venda (operação simulada)", fontsize=16, color=CINZA, va="top")
fig.text(0.07, 0.845, f"Negócios fechados: {ganhos} ganhos e {perdidos} perdidos (taxa de ganho de {taxa})",
         fontsize=14, color=TEXTO, va="top")
fig.subplots_adjust(left=0.27, right=0.97, top=0.78, bottom=0.1)
fig.savefig(SAIDA / "funil_leads_quentes.png", facecolor="white")
plt.close(fig)
print("Gráfico salvo:", SAIDA / "funil_leads_quentes.png")