import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
#IMPORTACION DE HELPERS
from .helpers import _guardar_fig, evolucion_vertimiento, _estilo_leyenda, _estilo_ax

def graficar_evolucion_vertimiento(df_vertimientos, df_vertimientos_comparacion, muted_dict, font_dict, font_family_dict, grid_alpha, grid_lw, edge_color, legend_alpha,
                                    out_path, mes_reporte: int, anio_reporte: int,
                                    figsize=(5.90, 3.85), font_scale=1.0, dpi=300):

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_tick  = round(12 * font_scale)
    fs_leg   = round(8  * font_scale)
    fs_leg_t = round(9  * font_scale)
    fs_annot = round(7  * font_scale)

    # ── Colores ───────────────────────────────────────────────────
    COLOR_PREV    = muted_dict["c2"]
    COLOR_CURR    = muted_dict["c1"]
    COLOR_PARCIAL = "#e67e22"
    ALPHA_PREV    = 0.55
    ALPHA_CURR    = 0.90
    ALPHA_PARC    = 0.90

    trimestre_en_curso = (mes_reporte - 1) // 3 + 1

    # ── Preparar datos ────────────────────────────────────────────
    df = evolucion_vertimiento(df_vertimientos, df_vertimientos_comparacion)

    if df.empty:
        fig, ax = plt.subplots(figsize=figsize)
        ax.text(0.5, 0.5, "Sin datos de vertimiento", ha="center", va="center",
                fontsize=fs_tick, color=font_dict)
        ax.axis("off")
        _guardar_fig(fig, out_path, dpi=dpi)
        return

    anio_prev = anio_reporte - 1

    def _get_valor(anio, q_num):
        q_label = f"Q{q_num}"
        mask = (df["anio"] == anio) & (df["trimestre"] == q_label)
        sub = df[mask]
        return sub["vertimiento"].sum() if not sub.empty else None

    # ── Dibujar ───────────────────────────────────────────────────
    x      = np.arange(4)
    ancho  = 0.35
    offset = ancho / 2

    fig, ax = plt.subplots(figsize=figsize)

    todos_los_vals = [
        _get_valor(anio_prev, q) for q in range(1, 5)
    ] + [
        _get_valor(anio_reporte, q) for q in range(1, trimestre_en_curso + 1)
    ]
    max_val = max((v for v in todos_los_vals if v), default=1)

    bars_prev = []
    bars_curr = []

    for q_idx, q_num in enumerate(range(1, 5)):
        pos_prev = x[q_idx] - offset
        pos_curr = x[q_idx]

        # ── Año anterior ──────────────────────────────────────────
        val_prev = _get_valor(anio_prev, q_num)
        b_prev = ax.bar(
            pos_prev, val_prev if val_prev else 0,
            width=ancho, color=COLOR_PREV, alpha=ALPHA_PREV,
            linewidth=0, label=str(anio_prev) if q_num == 1 else "_nolegend_"
        )
        bars_prev.append((b_prev, val_prev))

        # ── Año en curso ──────────────────────────────────────────
        if q_num < trimestre_en_curso:
            val_curr = _get_valor(anio_reporte, q_num)
            b_curr = ax.bar(
                pos_curr, val_curr if val_curr else 0,
                width=ancho, color=COLOR_CURR, alpha=ALPHA_CURR,
                linewidth=0, label=str(anio_reporte) if q_num == 1 else "_nolegend_"
            )
            bars_curr.append((b_curr, val_curr, False))

        elif q_num == trimestre_en_curso:
            val_curr = _get_valor(anio_reporte, q_num)
            b_curr = ax.bar(
                pos_curr, val_curr if val_curr else 0,
                width=ancho, color=COLOR_PARCIAL, alpha=ALPHA_PARC,
                linewidth=1, edgecolor=COLOR_PARCIAL,
                hatch="///", label=f"{anio_reporte} (en curso)" if q_num == 1 else "_nolegend_"
            )
            bars_curr.append((b_curr, val_curr, True))

        else:
            ax.bar(pos_curr, 0, width=ancho, color="none", linewidth=0)

    # ── Anotaciones ───────────────────────────────────────────────
    for b_prev, val in bars_prev:
        if val and val > 0:
            for bar in b_prev:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_val * 0.01,
                    f"{val:,.0f}".replace(",", "."),
                    ha="center", va="bottom",
                    fontsize=fs_annot, color=font_dict, fontfamily=font_family_dict
                )

    for b_curr, val, is_partial in bars_curr:
        if val and val > 0:
            for bar in b_curr:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + max_val * 0.01,
                    f"{val:,.0f}".replace(",", ".") + ("*" if is_partial else ""),
                    ha="center", va="bottom",
                    fontsize=fs_annot,
                    color=COLOR_PARCIAL if is_partial else font_dict,
                    fontfamily=font_family_dict,
                    fontweight="bold" if is_partial else "normal"
                )

    # ── Ejes ──────────────────────────────────────────────────────
    ax.set_xticks(x)
    ax.set_xticklabels(["1T", "2T", "3T", "4T"], fontsize=fs_tick)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=fs_tick)
    _estilo_ax(ax, grid_alpha, grid_lw, font_dict)

    # ── Nota pie ──────────────────────────────────────────────────
    mes_nombre = {1:"ene",2:"feb",3:"mar",4:"abr",5:"may",6:"jun",
                  7:"jul",8:"ago",9:"sep",10:"oct",11:"nov",12:"dic"}
    ax.annotate(
        f"* Valor acumulado a {mes_nombre[mes_reporte]} {anio_reporte}",
        xy=(0, 0), xycoords="axes fraction",
        xytext=(0, -0.46), textcoords="axes fraction",
        fontsize=fs_annot, color=COLOR_PARCIAL, fontfamily=font_family_dict
    )

    # ── Leyenda ───────────────────────────────────────────────────
    leg = ax.legend(
        bbox_to_anchor=(0.0, -0.51), title="Año",
        fontsize=fs_leg, title_fontsize=fs_leg_t,
        frameon=True, loc="lower left", ncol=3
    )
    _estilo_leyenda(leg, font_dict, font_family_dict, edge_color, legend_alpha)

    fig.subplots_adjust(left=0.08, right=0.98, top=0.88, bottom=0.23)
    _guardar_fig(fig, out_path, dpi=dpi)