#IMPORTACION DE LIBRERIAS GENERALES
import geopandas as gpd
import pandas as pd 
import matplotlib.pyplot as plt
import seaborn as sns

import numpy as np
#IMPORTACION DE HELPERS
from .helpers import _guardar_fig, _estilo_ax, _estilo_leyenda
# ══════════════════════════════════════════════════════════════════════════════
# 2) DÍA TÍPICO
# ══════════════════════════════════════════════════════════════════════════════

def graficar_gx_tipico(df_dia_tipico, dia_tipico_comparacion,
                        fecha_tipica, fecha_tipica_comparacion, font_dict, font_family_dict, color_tecnologia, edge_color, grid_alpha, grid_lw, legend_alpha,
                        out_path, figsize=(10.74, 5.02), font_scale=1.0, dpi=300):

    # ── Tamaños de fuente escalados ───────────────────────────────
    fs_title  = round(10 * font_scale)
    fs_label  = round(9  * font_scale)
    fs_tick   = round(8  * font_scale)
    fs_fecha  = round(8  * font_scale)
    fs_leg    = round(8  * font_scale)
    fs_leg_t  = round(9  * font_scale)

    def _preparar_df(df):
        if df.empty:
            return df
        df = df.copy()
        df["inyeccion_retiro"] = pd.to_numeric(df["inyeccion_retiro"], errors="coerce")
        df = df.dropna(subset=["inyeccion_retiro", "tipo"]).copy()

        if "hora_decimal" not in df.columns:
            if {"hora", "minuto"}.issubset(df.columns):
                df["hora"]   = pd.to_numeric(df["hora"],   errors="coerce").fillna(0)
                df["minuto"] = pd.to_numeric(df["minuto"], errors="coerce").fillna(0)
                df["hora_decimal"] = df["hora"] + df["minuto"] / 60.0
            else:
                df["fecha_hora"]   = pd.to_datetime(df["fecha_hora"], errors="coerce")
                df["hora_decimal"] = df["fecha_hora"].dt.hour + df["fecha_hora"].dt.minute / 60.0

        df["tipo"]    = df["tipo"].fillna("Sin clasificar").astype(str).str.strip()
        df["subtipo"] = df["subtipo"].fillna("-").astype(str).str.strip()

        rename_tipo = {
            "Eólicas": "Eólica", "Solar": "Solar", "Solares": "Solar",
            "Hidroeléctrica": "Hidro", "Hidroeléctricas": "Hidro", "Hidro": "Hidro",
            "Térmica": "Térmica", "Térmicas": "Térmica", "Termica": "Térmica", "Termicas": "Térmica",
            "Geotérmica": "Geotérmica", "Geotermia": "Geotérmica",
            "Bess": "BESS", "BESS": "BESS",
        }
        df["tipo_plot"]      = df["tipo"].replace(rename_tipo)
        df["categoria_plot"] = df["tipo_plot"]
        mask_bess   = df["tipo_plot"].eq("BESS")
        mask_retiro = df["subtipo"].str.contains("Retiro", case=False, na=False)
        mask_iny    = df["subtipo"].str.contains("Inye",   case=False, na=False)
        df.loc[mask_bess & mask_retiro, "categoria_plot"] = "BESS Retiro"
        df.loc[mask_bess & mask_iny,    "categoria_plot"] = "BESS Inyección"
        return df

    def _construir_pivot(df):
        if df.empty:
            return pd.DataFrame()
        df_plot = (df.groupby(["hora_decimal", "categoria_plot"], as_index=False)
                   ["inyeccion_retiro"].sum())
        orden = ["Solar", "Eólica", "Hidro", "Geotérmica", "Térmica", "BESS Inyección", "BESS Retiro"]
        pivot = (df_plot.pivot(index="hora_decimal", columns="categoria_plot",
                               values="inyeccion_retiro")
                 .fillna(0).sort_index())
        presentes = [t for t in orden if t in pivot.columns]
        restantes = sorted([t for t in pivot.columns if t not in presentes])
        return pivot[presentes + restantes]

    def _dibujar_areas(ax, pivot, fecha_label):
        if pivot.empty or len(pivot.index) <= 1 or np.isclose(pivot.to_numpy().sum(), 0):
            ax.text(0.5, 0.5, "Sin datos suficientes", ha="center", va="center",
                    fontsize=fs_title, color=font_dict)
            ax.axis("off")
            return

        x        = pivot.index.values
        cols_pos = [c for c in pivot.columns if pivot[c].max() > 0]
        cols_neg = [c for c in pivot.columns if pivot[c].min() < 0]

        if cols_pos:
            ax.stackplot(x, [pivot[c].clip(lower=0).values for c in cols_pos],
                         labels=cols_pos,
                         colors=[color_tecnologia.get(c, "#D9E2EC") for c in cols_pos],
                         alpha=0.95, linewidth=0.6)
        if cols_neg:
            ax.stackplot(x, [pivot[c].clip(upper=0).values for c in cols_neg],
                         labels=cols_neg,
                         colors=[color_tecnologia.get(c, "#D9E2EC") for c in cols_neg],
                         alpha=0.95, linewidth=0.6)

        ax.axhline(0, color=edge_color, linewidth=0.8)
        ax.text(0.01, 1.13, fecha_label, transform=ax.transAxes,
                fontsize=fs_fecha, color="#667085", ha="left", va="bottom",
                fontstyle="italic", fontfamily=font_family_dict)
        ax.set_title("Generación diaria típica por tecnología", fontsize=fs_title,
                     fontweight="bold", pad=4, color=font_dict)
        ax.set_xlabel("Hora del día", fontsize=fs_label, color=font_dict)
        ax.set_ylabel("Generación (mWh)", fontsize=fs_label, color=font_dict)
        _estilo_ax(ax, grid_alpha=grid_alpha, grid_lw=grid_lw, font_dict=font_dict)
        xticks = np.arange(0, 25, 4)
        ax.set_xticks(xticks)
        ax.set_xlim(0, 24)
        ax.set_xticklabels([f"{int(h):02d}:00" for h in xticks], fontsize=fs_tick)
        ax.tick_params(axis="y", labelsize=fs_tick)

    pivot_est  = _construir_pivot(_preparar_df(df_dia_tipico))
    pivot_comp = _construir_pivot(_preparar_df(dia_tipico_comparacion))

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=figsize, sharey=True)
    _dibujar_areas(ax1, pivot_est,  f"Fecha de referencia: {fecha_tipica}")
    _dibujar_areas(ax2, pivot_comp, f"Fecha de referencia: {fecha_tipica_comparacion}")

    handles, labels = ax1.get_legend_handles_labels()
    if not handles:
        handles, labels = ax2.get_legend_handles_labels()

    leg = fig.legend(handles, labels, title="Tecnología", loc="lower center",
                     ncol=len(labels), fontsize=fs_leg, title_fontsize=fs_leg_t,
                     frameon=True, bbox_to_anchor=(0.5, -0.05))
    _estilo_leyenda(leg, font_dict=font_dict, font_family_dict=font_family_dict,
                    edge_color=edge_color, legend_alpha=legend_alpha)

    fig.subplots_adjust(left=0.06, right=0.98, top=0.84, bottom=0.20, wspace=0.08)
    _guardar_fig(fig, out_path, dpi=dpi)