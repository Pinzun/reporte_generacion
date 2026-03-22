import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
from .helpers import _estilo_ax,_estilo_leyenda,_guardar_fig
# ══════════════════════════════════════════════════════════════════════════════
# 5) INYECTADA VS VERTIDA
# ══════════════════════════════════════════════════════════════════════════════

def graficar_inyectada_vertida(df_gx_ver_iny, out_path, muted_dict, font_dict, grid_alpha, grid_lw, font_family_dict, edge_color, legend_alpha,
                                figsize=(5.19, 4.86), font_scale=1.0, dpi=300):

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_tick   = round(12  * font_scale)
    fs_leg    = round(8  * font_scale)

    columnas = {"periodo", "inyeccion", "vertimiento"}
    faltantes = columnas - set(df_gx_ver_iny.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas: {sorted(faltantes)}")

    df_plot = df_gx_ver_iny.copy().sort_values("periodo", ascending=True).reset_index(drop=True)
    x     = np.arange(len(df_plot))
    width = 0.55

    fig, ax = plt.subplots(figsize=figsize)

    ax.bar(x, df_plot["inyeccion"],   width=width, label="Inyecciones",
           color=muted_dict["c2"], edgecolor="white", linewidth=0.8)
    ax.bar(x, df_plot["vertimiento"], width=width, bottom=df_plot["inyeccion"],
           label="Vertimientos", color=muted_dict["c1"], edgecolor="white", linewidth=0.8)

    ax.set_xlabel("")       # ← eliminado
    ax.set_ylabel("")       # ← eliminado
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot["periodo"], rotation=35, ha="right", fontsize=fs_tick)
    ax.tick_params(axis="y", labelsize=fs_tick)
    _estilo_ax(ax, grid_alpha, grid_lw, font_dict)

    leg = ax.legend(bbox_to_anchor=(0.0, -0.51),frameon=True, fontsize=fs_leg, ncol=2, loc="lower left")
    _estilo_leyenda(leg, font_dict, font_family_dict, edge_color, legend_alpha)

    fig.subplots_adjust(left=0.09, right=0.98, top=0.87, bottom=0.35)
    _guardar_fig(fig, out_path, dpi=dpi)