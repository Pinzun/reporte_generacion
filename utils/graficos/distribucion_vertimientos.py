import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter 
import seaborn as sns

import numpy as np
#IMPORTACION DE HELPERS
from .helpers import _guardar_fig, _estilo_leyenda, _estilo_ax,_fmt_thousands

#══════════════════════════════════════════════════════════════════════════════
# 4) BOXPLOT VERTIMIENTOS + LÍNEA TOTAL
# ══════════════════════════════════════════════════════════════════════════════

def graficar_boxplot_vertimientos_con_total(df_all, out_path, muted_dict, font_dict, grid_alpha, grid_lw, font_family_dict, edge_color, legend_alpha,
                                             figsize=(10.4, 4.8), font_scale=1.0, dpi=300):

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_title  = round(12 * font_scale)
    fs_label  = round(10 * font_scale)
    fs_tick   = round(8  * font_scale)
    fs_leg    = round(9  * font_scale)

    df_box = df_all.copy()
    df_box["periodo"] = pd.to_datetime(df_box["periodo"], errors="coerce").dt.strftime("%Y-%m").astype(str)
    order_periodos = sorted(df_box["periodo"].dropna().unique().tolist())

    df_line = (df_box.groupby("periodo", as_index=False)["vertimiento"]
               .sum().rename(columns={"vertimiento": "kwh_total"}))
    df_line["periodo"] = pd.Categorical(df_line["periodo"], categories=order_periodos, ordered=True)
    df_line = df_line.sort_values("periodo")
    pos_map = {p: i for i, p in enumerate(order_periodos)}
    x_pos   = df_line["periodo"].astype(str).map(pos_map).astype(float)

    fig, ax = plt.subplots(figsize=figsize)
    ax2 = ax.twinx()

    ax2.plot(x_pos, df_line["kwh_total"].values,
             linewidth=2.2, color=muted_dict["c2"], alpha=0.9, zorder=1, label="Total mensual")
    ax2.set_ylabel("kWh total mensual", color=font_dict, fontsize=fs_label)
    ax2.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    ax2.tick_params(colors=font_dict, labelsize=fs_tick)
    ax2.grid(False)
    ax2.patch.set_alpha(0)
    sns.despine(ax=ax2, top=True, left=True)

    sns.boxplot(data=df_box, x="periodo", y="vertimiento", order=order_periodos,
                ax=ax, width=0.55, fliersize=2.2, linewidth=1.0,
                color=muted_dict["c1"], zorder=3)

    ax.set_title("Vertimientos por empresa en cada mes (kWh)", fontsize=fs_title,
                 fontweight="bold", color=font_dict)
    ax.set_xlabel("Periodo", fontsize=fs_label, color=font_dict)
    ax.set_ylabel("kWh (distribución)", fontsize=fs_label, color=font_dict)
    _estilo_ax(ax, grid_alpha=grid_alpha, grid_lw=grid_lw, font_dict=font_dict)
    ax.tick_params(axis="x", rotation=45, labelsize=fs_tick)
    ax.tick_params(axis="y", labelsize=fs_tick)

    leg = ax2.legend(loc="upper right", bbox_to_anchor=(0.99, 0.99),
                     frameon=True, fontsize=fs_leg)
    _estilo_leyenda(leg, font_dict=font_dict, font_family_dict=font_family_dict,
                    edge_color=edge_color, legend_alpha=legend_alpha)

    fig.subplots_adjust(left=0.06, right=0.96, top=0.88, bottom=0.20)
    _guardar_fig(fig, out_path, dpi=dpi)