import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import os
from matplotlib.ticker import FuncFormatter 
from pptx import Presentation


# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════


def evolucion_inyeccion_bess(df_gx_real: pd.DataFrame, df_gx_real_comparacion: pd.DataFrame) -> pd.DataFrame:

    def _calcular_trimestral(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        mask = (
            df["tipo"].astype(str).str.strip().str.lower().eq("bess") &
            df["subtipo"].astype(str).str.strip().str.contains("inye", case=False, na=False)
        )
        df = df[mask].copy()

        if df.empty:
            return pd.DataFrame(columns=["trimestre", "inyeccion_retiro", "anio"])

        df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
        df["trimestre"]  = df["fecha_hora"].dt.to_period("Q").astype(str)
        df["anio"]       = df["fecha_hora"].dt.year.astype(str)  # ← año extraído del DF

        return (
            df.groupby(["trimestre", "anio"], as_index=False)["inyeccion_retiro"]
            .sum()
        )

    df_estudio     = _calcular_trimestral(df_gx_real)
    df_comparacion = _calcular_trimestral(df_gx_real_comparacion)

    return pd.concat([df_estudio, df_comparacion], ignore_index=True)

def evolucion_vertimiento(df_vertimientos: pd.DataFrame, df_vertimientos_comparacion: pd.DataFrame) -> pd.DataFrame:

    def _calcular_trimestral(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if df.empty:
            return pd.DataFrame(columns=["trimestre", "vertimiento", "anio"])

        df["periodo"]   = pd.to_datetime(df["periodo"], errors="coerce")
        df["trimestre"] = df["periodo"].dt.to_period("Q").astype(str)
        df["anio"]      = df["periodo"].dt.year.astype(str)

        return (
            df.groupby(["trimestre", "anio"], as_index=False)["vertimiento"]
            .sum()
        )

    df_estudio     = _calcular_trimestral(df_vertimientos)
    df_comparacion = _calcular_trimestral(df_vertimientos_comparacion)

    return pd.concat([df_estudio, df_comparacion], ignore_index=True)


def _setup_theme(font_dict,font_family_dict,grid_alph,grid_lw,edge_color,legend_alpha):
    """Aplica el tema global Seaborn coherente con el estilo día típico."""
    plt.rcParams["font.family"] = font_family_dict
    sns.set_theme(
        style="whitegrid",
        context="notebook",
        rc={
            "font.family":        font_family_dict,
            "axes.titlesize":     12,
            "axes.titleweight":   "bold",
            "axes.labelsize":     10,
            "xtick.labelsize":    8,
            "ytick.labelsize":    8,
            "grid.alpha":         grid_alph,
            "grid.linewidth":     grid_lw,
            "axes.edgecolor":     edge_color,
            "axes.linewidth":     0.9,
            "figure.facecolor":   "none",
            "axes.facecolor":     "white",
            "legend.frameon":     True,
            "legend.framealpha":  legend_alpha,
            "text.color":         font_dict,
            "axes.labelcolor":    font_dict,
            "xtick.color":        font_dict,
            "ytick.color":        font_dict,
        },
    )


def _fmt_thousands(x, pos):
    try:
        return f"{x:,.0f}".replace(",", ".")
    except Exception:
        return str(x)


def _guardar_fig(fig, path, dpi=300):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".svg":
        fig.savefig(path, format="svg", bbox_inches="tight")
    else:
        fig.savefig(
            path,
            dpi=dpi,
            bbox_inches="tight",
            pad_inches=0.06,
            transparent=True,   # ← fondo transparente
        )
    plt.close(fig)


def _estilo_leyenda(leg, font_dict, font_family_dict, edge_color, legend_alpha):
    leg.get_frame().set_alpha(legend_alpha)
    leg.get_frame().set_edgecolor(edge_color)
    for text in leg.get_texts():
        text.set_color(font_dict)
        text.set_fontfamily(font_family_dict)
    if leg.get_title():
        leg.get_title().set_color(font_dict)
        leg.get_title().set_fontfamily(font_family_dict)


def _estilo_ax(ax, grid_alpha, grid_lw,font_dict):
    """Aplica estilo base consistente a un eje."""
    ax.grid(True,  axis="y", alpha=grid_alpha, linewidth=grid_lw, color="#CCCCCC")
    ax.grid(False, axis="x")
    ax.yaxis.set_major_formatter(FuncFormatter(_fmt_thousands))
    ax.tick_params(axis="x", labelsize=8, colors=font_dict)
    ax.tick_params(axis="y", labelsize=8, colors=font_dict)
    sns.despine(ax=ax, top=True, right=True)


def listar_shapes(pptx_path, slide_idx):
    prs = Presentation(pptx_path)
    slide = prs.slides[slide_idx]
    for i, shape in enumerate(slide.shapes):
        tipo = "TABLA" if shape.has_table else shape.shape_type
        print(f"  [{i}] nombre='{shape.name}'  tipo={tipo}")
