import os
import pandas as pd
from utils.inserta_texto_ppt import insertar_top_vertimiento
#IMPORTACIÓN FUNCIONES GRÁFICOS
from .graficos.cmg_mapa import graficar_cmg_con_mapa, generar_mapa_regiones
from .graficos.distribucion_vertimientos import graficar_boxplot_vertimientos_con_total
from .graficos.energia_inyectada_vertida import graficar_inyectada_vertida
from .graficos.evolucion_inyeccion_bess import graficar_evolucion_inyeccion_bess
from .graficos.evolucion_vertimientos import graficar_evolucion_vertimiento
from .graficos.gx_tipico import graficar_gx_tipico
from .graficos.spread_cmg import graficar_spread_cmg
from utils.insercion_graficos import insertar_graficos_ppt, get_figsize, TARGET_DPI

#HELPER
from .graficos.helpers import _setup_theme

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES GLOBALES DE ESTILO
# ══════════════════════════════════════════════════════════════════════════════

FONT_FAMILY  = "Candara"
FONT_COLOR   = "#003366"
GRID_ALPHA   = 0.18
GRID_LW      = 0.7
EDGE_COLOR   = "#D0D5DD"
LEGEND_ALPHA = 0.9

# Paleta Seaborn Muted — orden fijo para consistencia entre gráficos
MUTED = {
    "c1": "#9EC8E8",   # Azul pizarra   — año reciente / serie principal
    "c2": "#F4B89A",   # Naranja tostado — año anterior / serie secundaria
    "c3": "#A8DDA5",   # Verde salvia
    "c4": "#E8A5A5",   # Rojo arcilla
    "c5": "#C4A8D4",   # Violeta suave
    "c6": "#C4A882",   # Café rosado
}

# Colores específicos por tecnología (día típico — paleta propia clara)
COLOR_TECNOLOGIA = {
    "Solar":          "#F6C48E",
    "Eólica":         "#A8D5BA",
    "Hidro":          "#8EC5FF",
    "Geotérmica":     "#D9C2A3",
    "Térmica":        "#C9C2E6",
    "BESS Inyección": "#D96C6C",
    "BESS Retiro":    "#6FA8DC",
}

SHP_REGIONES = r"C:\Users\pinzunza\OneDrive - Ministerio de Energia\Escritorio\escritorio desrodenado\capas\Comunas\COMUNAS_NACIONAL.shp"

BAR_POINTS = {
    "Barra crucero 200kV":       {"lon": -69.5677773900849, "lat": -22.27773471974709},
    "Barra Pan de Azucar 220kV": {"lon": -71.100,           "lat": -29.900},
    "Barra Quillota 220kV":      {"lon": -71.260,           "lat": -32.880},
    "Barra Alto Jahuel 500kV":   {"lon": -70.630,           "lat": -33.720},
    "Barra Puerto Montt 220kV":  {"lon": -72.940,           "lat": -41.470},
    "Barra Charrua 500kV":       {"lon": -72.940,           "lat": -41.470},}

# ══════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR 
# ══════════════════════════════════════════════════════════════════════════════

def generar_graficas(
    df_vertimientos,
    df_vertimientos_comparacion,
    df_spread,
    df_cmg,
    df_cmg_comparacion,
    df_dia_tipico,
    df_dia_tipico_comparacion,
    fecha_tipica,
    fecha_tipica_comparacion,
    df_gx_ver_iny,
    ppt_path,
    df_top_vertimiento,
    gx_real,
    gx_real_comparacion,
    outdir="outputs",
    font_scale=1.5,
    dpi=TARGET_DPI,
):

    os.makedirs(outdir, exist_ok=True)
    _setup_theme(font_dict=FONT_COLOR, font_family_dict=FONT_FAMILY, grid_alph=GRID_ALPHA,
                 grid_lw=GRID_LW, edge_color=EDGE_COLOR, legend_alpha=LEGEND_ALPHA)

    rename_map = {
        "CRUCERO_______220": "Barra crucero 220kV",
        "AJAHUEL_______500": "Barra Alto Jahuel 500kV",
        "P.MONTT_______220": "Barra Puerto Montt 220kV",
    }

    # ── 1) CMG con mapa ───────────────────────────────────────────────────────
    gdf_reg = generar_mapa_regiones(SHP_REGIONES)
    df_c    = df_cmg.copy()
    df_c["fecha_hora"] = pd.to_datetime(df_c["fecha_hora"], errors="coerce")
    df_c = df_c.sort_values("fecha_hora")
    df_c["nombre_cmg"] = df_c["nombre_cmg"].replace(rename_map)

    df_com = df_cmg_comparacion.copy()
    df_com["fecha_hora"] = pd.to_datetime(df_com["fecha_hora"], errors="coerce")
    df_com = df_com.sort_values("fecha_hora")
    df_com["nombre_cmg"] = df_com["nombre_cmg"].replace(rename_map)

    graficar_cmg_con_mapa(
        df_cmg=df_c, df_cmg_comparacion=df_com,
        gdf_reg=gdf_reg, bar_points=BAR_POINTS,
        out_path=os.path.join(outdir, "cmg.png"),
        figsize=get_figsize("img_cmg"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 2) Día típico ─────────────────────────────────────────────────────────
    graficar_gx_tipico(
        df_dia_tipico=df_dia_tipico,
        dia_tipico_comparacion=df_dia_tipico_comparacion,
        fecha_tipica=fecha_tipica,
        fecha_tipica_comparacion=fecha_tipica_comparacion,
        font_dict=FONT_COLOR,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        legend_alpha=LEGEND_ALPHA,
        font_family_dict=FONT_FAMILY,
        color_tecnologia=COLOR_TECNOLOGIA,
        edge_color=EDGE_COLOR,
        out_path=os.path.join(outdir, "gx_tipico.png"),
        figsize=get_figsize("img_dia_tipico"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 3) Spread CMG ─────────────────────────────────────────────────────────
    df_spread_plot = df_spread.copy()
    df_spread_plot["nombre_cmg"] = df_spread_plot["nombre_cmg"].replace(rename_map)
    graficar_spread_cmg(
        df_spread=df_spread_plot,
        muted_dict=MUTED,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        font_dict=FONT_COLOR,
        font_family_dict=FONT_FAMILY,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        out_path=os.path.join(outdir, "spread_cmg.png"),
        figsize=get_figsize("img_spread"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 4) Boxplot vertimientos ───────────────────────────────────────────────
    graficar_boxplot_vertimientos_con_total(
        df_all=df_vertimientos,
        muted_dict=MUTED,
        font_dict=FONT_COLOR,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,                  # ← estaba GRID_ALPHA por error
        font_family_dict=FONT_FAMILY,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        out_path=os.path.join(outdir, "boxplot.png"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 5) Inyectada vs vertida ───────────────────────────────────────────────
    graficar_inyectada_vertida(
        df_gx_ver_iny=df_gx_ver_iny,
        muted_dict=MUTED,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,                  # ← estaba GRID_ALPHA por error
        font_dict=FONT_COLOR,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        font_family_dict=FONT_FAMILY,
        out_path=os.path.join(outdir, "inyec_vert.png"),
        figsize=get_figsize("img_inyecciones_vertimientos"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 6) Evolución inyección BESS ───────────────────────────────────────────
    graficar_evolucion_inyeccion_bess(
        df_gx_real=gx_real,
        df_gx_real_comparacion=gx_real_comparacion,
        muted_dict=MUTED,
        font_dict=FONT_COLOR,
        font_family_dict=FONT_FAMILY,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        out_path=os.path.join(outdir, "inyecciones_bess.png"),
        figsize=get_figsize("img_inyeccion_bess"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 7) Evolución vertimientos ─────────────────────────────────────────────
    graficar_evolucion_vertimiento(
        df_vertimientos=df_vertimientos,
        df_vertimientos_comparacion=df_vertimientos_comparacion,
        muted_dict=MUTED,
        font_dict=FONT_COLOR,
        font_family_dict=FONT_FAMILY,     # ← estaba FONT_COLOR por error
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        out_path=os.path.join(outdir, "evolucion_vertimiento.png"),
        figsize=get_figsize("img_evolucion_vertimientos"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 8) Tabla top vertimientos ─────────────────────────────────────────────
    df_top_vertimiento["nombre_central"] = df_top_vertimiento["nombre_central"].str.replace("Pfv", "", regex=False)
    df_top_vertimiento["nombre_central"] = df_top_vertimiento["nombre_central"].str.replace("PFV", "", regex=False)
    print(df_top_vertimiento.head())
    insertar_top_vertimiento(ppt_path, 2, df_top_vertimiento=df_top_vertimiento)

    # ── 9) Insertar todas las imágenes en el PPT ──────────────────────────────
    insertar_graficos_ppt(ppt_path, outdir)