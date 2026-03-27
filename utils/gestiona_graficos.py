import os
import pandas as pd
from utils.inserta_texto_ppt import insertar_top_vertimiento
from utils.config_loader import get_config
#IMPORTACIÓN FUNCIONES GRÁFICOS
from .graficos.cmg_mapa import graficar_cmg_con_mapa, generar_mapa_regiones
from .graficos.distribucion_vertimientos import graficar_boxplot_vertimientos_con_total
from .graficos.energia_inyectada_vertida import graficar_inyectada_vertida
from .graficos.evolucion_inyeccion_bess import graficar_evolucion_inyeccion_bess
from .graficos.evolucion_vertimientos import graficar_evolucion_vertimiento
from .graficos.gx_tipico import graficar_gx_tipico
from .graficos.spread_cmg import graficar_spread_cmg
from utils.insercion_graficos import insertar_graficos_ppt, get_figsize, TARGET_DPI
from .graficos.helpers import render_table_image
from pathlib import Path
from .graficos.helpers import _setup_theme
from dotenv import load_dotenv

# ══════════════════════════════════════════════════════════════════════════════
# VARIABLES DE ENTORNO
# ══════════════════════════════════════════════════════════════════════════════
load_dotenv()   # ← faltaban los paréntesis en el original

# ══════════════════════════════════════════════════════════════════════════════
# CONSTANTES GLOBALES DE ESTILO
# ══════════════════════════════════════════════════════════════════════════════

_cfg = get_config()
_viz = _cfg["visualizacion"]

FONT_FAMILY  = _viz["font_family"]
FONT_COLOR   = _viz["font_color"]
GRID_ALPHA   = _viz["grid_alpha"]
GRID_LW      = _viz["grid_lw"]
EDGE_COLOR   = _viz["edge_color"]
LEGEND_ALPHA = _viz["legend_alpha"]

MUTED            = _viz["paleta"]
COLOR_TECNOLOGIA = _viz["colores_tecnologia"]

shp_env = os.getenv("SHP_REGIONES")
if shp_env:
    SHP_REGIONES = Path(shp_env)
    if SHP_REGIONES.exists():
        print(f"SHP encontrado: {SHP_REGIONES}")
    else:
        print("⚠️ Archivo no encontrado, revisar ruta en variable de entorno")
else:
    print("⚠️ Variable SHP_REGIONES no definida en entorno ni en .env")

BAR_POINTS = {
    nombre: {"lon": coords["lon"], "lat": coords["lat"]}
    for nombre, coords in _cfg["barras"]["coordenadas"].items()
}

# ══════════════════════════════════════════════════════════════════════════════
# ORQUESTADOR
# ══════════════════════════════════════════════════════════════════════════════

def generar_graficas(
    # Vertimientos ventana simple
    df_vertimientos,
    df_vertimientos_comparacion,
    # Vertimientos ventana trimestral
    df_vertimientos_trim,
    df_vertimientos_trim_comparacion,
    # CMg
    df_spread,
    df_cmg,
    df_cmg_comparacion,
    # Día típico
    df_dia_tipico,
    df_dia_tipico_comparacion,
    fecha_tipica,
    fecha_tipica_comparacion,
    # GX real ventana simple
    gx_real,
    gx_real_comparacion,
    # GX real ventana trimestral
    df_gx_real_trim,
    df_gx_real_trim_comparacion,
    # Otros
    df_gx_ver_iny,
    df_top_vertimiento,
    # Parámetros temporales para gráficos trimestrales
    mes_reporte,
    anio_reporte,
    # Rutas y config
    ppt_path,
    outdir="outputs",
    font_scale=None,
    dpi=None,
):
    if font_scale is None:
        font_scale = _viz["font_scale"]
    if dpi is None:
        dpi = _viz["dpi"]

    os.makedirs(outdir, exist_ok=True)
    _setup_theme(
        font_dict=FONT_COLOR, font_family_dict=FONT_FAMILY,
        grid_alph=GRID_ALPHA, grid_lw=GRID_LW,
        edge_color=EDGE_COLOR, legend_alpha=LEGEND_ALPHA,
    )

    rename_map = _cfg["barras"]["nombres"]

    # ── 1) CMG con mapa ───────────────────────────────────────────────────────
    gdf_reg = generar_mapa_regiones(SHP_REGIONES)

    df_c = df_cmg.copy()
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
    print(f"fecha_tipica: {fecha_tipica}")
    print(f"fecha_tipica_comparacion: {fecha_tipica_comparacion}")
    print(f"df_dia_tipico shape: {df_dia_tipico.shape}")
    print(f"df_dia_tipico_comparacion shape: {df_dia_tipico_comparacion.shape}")

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

    # ── 4) Boxplot vertimientos — ventana simple ──────────────────────────────
    graficar_boxplot_vertimientos_con_total(
        df_all=df_vertimientos,
        muted_dict=MUTED,
        font_dict=FONT_COLOR,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        font_family_dict=FONT_FAMILY,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        out_path=os.path.join(outdir, "boxplot.png"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 5) Inyectada vs vertida — ventana simple ──────────────────────────────
    graficar_inyectada_vertida(
        df_gx_ver_iny=df_gx_ver_iny,
        muted_dict=MUTED,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        font_dict=FONT_COLOR,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        font_family_dict=FONT_FAMILY,
        out_path=os.path.join(outdir, "inyec_vert.png"),
        figsize=get_figsize("img_inyecciones_vertimientos"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 6) Evolución inyección BESS — ventana trimestral ─────────────────────
    graficar_evolucion_inyeccion_bess(
        df_gx_real=df_gx_real_trim,
        df_gx_real_comparacion=df_gx_real_trim_comparacion,
        muted_dict=MUTED,
        font_dict=FONT_COLOR,
        font_family_dict=FONT_FAMILY,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        mes_reporte=mes_reporte,
        anio_reporte=anio_reporte,
        out_path=os.path.join(outdir, "inyecciones_bess.png"),
        figsize=get_figsize("img_inyeccion_bess"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 7) Evolución vertimientos — ventana trimestral ────────────────────────
    graficar_evolucion_vertimiento(
        df_vertimientos=df_vertimientos_trim,
        df_vertimientos_comparacion=df_vertimientos_trim_comparacion,
        muted_dict=MUTED,
        font_dict=FONT_COLOR,
        font_family_dict=FONT_FAMILY,
        grid_alpha=GRID_ALPHA,
        grid_lw=GRID_LW,
        edge_color=EDGE_COLOR,
        legend_alpha=LEGEND_ALPHA,
        mes_reporte=mes_reporte,
        anio_reporte=anio_reporte,
        out_path=os.path.join(outdir, "evolucion_vertimiento.png"),
        figsize=get_figsize("img_evolucion_vertimientos"),
        font_scale=font_scale, dpi=dpi,
    )

    # ── 8) Tabla top vertimientos ─────────────────────────────────────────────
    df_top_vertimiento["Nombre central"] = (
        df_top_vertimiento["Nombre central"]
        .str.replace("Pfv", "", regex=False)
        .str.replace("PFV", "", regex=False)
    )

    render_table_image(
        df=df_top_vertimiento,
        title="Top vertimientos por central",
        out_path=os.path.join(outdir, "tabla_top.png"),
        font_dict=FONT_COLOR,
        font_family_dict=FONT_FAMILY,
        muted_dict=MUTED,
        edge_color=EDGE_COLOR,
        figsize=get_figsize("tabla_top"),
        font_scale=font_scale,
        dpi=TARGET_DPI,
    )

    # ── 9) Insertar todas las imágenes en el PPT ──────────────────────────────
    insertar_graficos_ppt(ppt_path, outdir)