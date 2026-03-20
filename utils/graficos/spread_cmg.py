#IMPORTACION DE LIBRERIAS GENERALES
import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.lines import Line2D
from matplotlib.colors import LinearSegmentedColormap
import numpy as np
#IMPORTACION DE HELPERS
from .helpers import _guardar_fig,_estilo_ax,_estilo_leyenda


# ══════════════════════════════════════════════════════════════════════════════
# 3) SPREAD CMG
# ══════════════════════════════════════════════════════════════════════════════

def graficar_spread_cmg(df_spread, out_path, muted_dict, grid_alpha, grid_lw, font_dict, font_family_dict, edge_color, legend_alpha, figsize=(6.04, 4.29), font_scale=1.0, dpi=300):

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_title  = round(12 * font_scale)
    fs_label  = round(10 * font_scale)
    fs_tick   = round(8  * font_scale)
    fs_leg    = round(8  * font_scale)

    columnas = {"nombre_cmg", "horas_solares", "horas_no_solares"}
    faltantes = columnas - set(df_spread.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas: {sorted(faltantes)}")

    df_plot = df_spread.copy()
    if "spread_abs" in df_plot.columns:
        df_plot = df_plot.sort_values("spread_abs", ascending=False).reset_index(drop=True)

    x     = np.arange(len(df_plot))
    width = 0.38
    fig, ax = plt.subplots(figsize=figsize)

    ax.bar(x - width/2, df_plot["horas_solares"],    width=width,
           label="Horas solares",    color=muted_dict["c2"], edgecolor="white", linewidth=0.8)
    ax.bar(x + width/2, df_plot["horas_no_solares"], width=width,
           label="Horas no solares", color=muted_dict["c1"], edgecolor="white", linewidth=0.8)

    ax.set_title("CMG promedio: horas solares vs no solares", fontsize=fs_title,
                 fontweight="bold", color=font_dict)
    ax.set_xlabel("Barra CMG", fontsize=fs_label, color=font_dict)
    ax.set_ylabel("CMG promedio ($/kWh)", fontsize=fs_label, color=font_dict)
    ax.set_xticks(x)
    ax.set_xticklabels(df_plot["nombre_cmg"], rotation=35, ha="right", fontsize=fs_tick)
    ax.tick_params(axis="y", labelsize=fs_tick)
    _estilo_ax(ax, grid_alpha, grid_lw, font_dict)

    leg = ax.legend(frameon=True, fontsize=fs_leg)
    _estilo_leyenda(leg, font_dict=font_dict, font_family_dict=font_family_dict,
                    edge_color=edge_color, legend_alpha=legend_alpha)

    fig.subplots_adjust(left=0.09, right=0.98, top=0.87, bottom=0.28)
    _guardar_fig(fig, out_path, dpi=dpi)