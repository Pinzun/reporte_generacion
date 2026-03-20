import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
#IMPORTACION DE HELPERS
from .helpers import _guardar_fig, evolucion_vertimiento, _estilo_leyenda, _estilo_ax

# ══════════════════════════════════════════════════════════════════════════════
# 7) EVOLUCIÓN VERTIMIENTO
# ══════════════════════════════════════════════════════════════════════════════

def graficar_evolucion_vertimiento(df_vertimientos, df_vertimientos_comparacion, muted_dict, font_dict, font_family_dict, grid_alpha, grid_lw, edge_color, legend_alpha,
                                    out_path, figsize=(5.90, 3.85), font_scale=1.0, dpi=300):

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_title  = round(12 * font_scale)
    fs_label  = round(10  * font_scale)
    fs_tick   = round(8  * font_scale)
    fs_leg    = round(8  * font_scale)
    fs_leg_t  = round(9  * font_scale)
    fs_annot  = round(7  * font_scale)

    COLORES = {0: muted_dict["c2"], 1: muted_dict["c1"]}

    df = evolucion_vertimiento(df_vertimientos, df_vertimientos_comparacion)
    if df.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Sin datos de vertimiento", ha="center", va="center",
                fontsize=fs_title, color=font_dict)
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    anios      = sorted(df["anio"].unique())
    trimestres = sorted(df["trimestre"].unique())
    x      = np.arange(len(trimestres))
    ancho  = 0.35
    offset = ancho / 2

    fig, ax = plt.subplots(figsize=figsize)

    for i, anio in enumerate(anios):
        df_a    = df[df["anio"] == anio].set_index("trimestre")
        valores = [df_a.loc[t, "vertimiento"] if t in df_a.index else 0 for t in trimestres]
        pos     = x - offset + i * ancho
        color   = COLORES.get(i, muted_dict["c5"])

        bars = ax.bar(pos, valores, width=ancho, color=color, label=anio, linewidth=0)

        max_val = max([v for v in valores if v > 0], default=1)
        for bar, val in zip(bars, valores):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + max_val * 0.01,
                        f"{val:,.0f}".replace(",", "."),
                        ha="center", va="bottom", fontsize=fs_annot, color=font_dict,
                        fontfamily=font_family_dict)

    ax.set_xticks(x)
    ax.set_xticklabels([t.split("Q")[1] + "T" for t in trimestres], fontsize=fs_tick)
    ax.set_xlabel("Trimestre", fontsize=fs_label, color=font_dict)
    ax.set_title("Evolución trimestral de vertimientos", fontsize=fs_title,
                 fontweight="bold", color=font_dict)
    ax.set_ylabel("Vertimiento (MWh)", fontsize=fs_label, color=font_dict)
    ax.tick_params(axis="y", labelsize=fs_tick)
    _estilo_ax(ax, grid_alpha, grid_lw, font_dict)

    leg = ax.legend(title="Año", fontsize=fs_leg, title_fontsize=fs_leg_t,
                    frameon=True, loc="upper left")
    _estilo_leyenda(leg, font_dict, font_family_dict, edge_color, legend_alpha)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.15)
    _guardar_fig(fig, out_path, dpi=dpi)