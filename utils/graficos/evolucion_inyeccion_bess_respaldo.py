
import matplotlib.pyplot as plt


import numpy as np
#IMPORTACION DE HELPERS
from .helpers import _guardar_fig, evolucion_inyeccion_bess, _estilo_leyenda, _estilo_ax

# ══════════════════════════════════════════════════════════════════════════════
# 6) EVOLUCIÓN INYECCIÓN BESS
# ══════════════════════════════════════════════════════════════════════════════

def graficar_evolucion_inyeccion_bess(df_gx_real, df_gx_real_comparacion, muted_dict, font_dict, font_family_dict, grid_alpha, grid_lw, edge_color, legend_alpha,
                                       out_path, figsize=(5.90, 4.14), font_scale=1.0, dpi=300):

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_tick   = round(12  * font_scale)
    fs_leg    = round(8  * font_scale)
    fs_leg_t  = round(9  * font_scale)
    fs_annot  = round(7  * font_scale)

    COLORES = {0: muted_dict["c2"], 1: muted_dict["c1"]}

    df = evolucion_inyeccion_bess(df_gx_real, df_gx_real_comparacion)
    print("Evolución_inyecciones_bees test:")
    print(df.groupby(["anio", "trimestre"]).size().sort_values(ascending=False).head(10))
    if df.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Sin datos de inyección BESS", ha="center", va="center",
                fontsize=fs_tick, color=font_dict)
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
        valores = [df_a.loc[t, "inyeccion_retiro"] if t in df_a.index else 0 for t in trimestres]
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
    ax.set_xlabel("")       # ← eliminado
    ax.set_ylabel("")       # ← eliminado
    ax.tick_params(axis="y", labelsize=fs_tick)
    _estilo_ax(ax, grid_alpha, grid_lw, font_dict)

    leg = ax.legend(bbox_to_anchor=(0.0, -0.51),title="Año", fontsize=fs_leg, title_fontsize=fs_leg_t,
                    frameon=True, loc="lower left", ncol=2)
    _estilo_leyenda(leg, font_dict, font_family_dict, edge_color, legend_alpha)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.23)
    _guardar_fig(fig, out_path, dpi=dpi)