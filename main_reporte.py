# main.py
from __future__ import annotations

from pathlib import Path
import pandas as pd

from utils.config_loader import get_config
from utils.extrae_data import (
    extrae_data_total_vertimientos,
    extrae_data_cmg,
    extrae_gx_real,
    extrae_gx_real_comparacion
)
from utils.gestiona_graficos import generar_graficas
from utils.calcula_gx_tipico import gx_real_tipico
from utils.calcula_spread_cmg import spread_cmg
from utils.calcula_gx_inyectada_vertida import gx_ver_iny
from utils.calcula_top_vertimiento import top_vertimientos
from utils.inserta_texto_ppt import insertar_periodo_estudio, exportar_ppt_a_pdf, insertar_texto_con_placeholders
import shutil

# -----------------------
# Config
# -----------------------

_cfg = get_config()

BASE_DIR   = Path(__file__).parent
TEMPL_DIR  = BASE_DIR / _cfg["rutas"]["templates"]
ASSETS_DIR = BASE_DIR / _cfg["rutas"]["assets"]
IMG_DIR    = BASE_DIR / _cfg["rutas"]["imagenes"]
OUT_DIR    = BASE_DIR / _cfg["rutas"]["reportes"]
CSV_DIR    = BASE_DIR / _cfg["rutas"]["csv"]

PPT_PATH = OUT_DIR / "reporte_generacion.pptx"
PDF_PATH = OUT_DIR / "reporte_generacion.pdf"

PDF_NAME          = "reporte.pdf"
DEV               = _cfg["reporte"]["dev_mode"]
GENERAR_PLANTILLA = _cfg["reporte"]["generar_plantilla"]
FECHA_ESTUDIO     = _cfg["reporte"]["fecha_estudio"]


# -----------------------
# Helpers
# -----------------------

def fmt_int(x):
    try:
        return f"{int(round(float(x))):,}".replace(",", ".")
    except Exception:
        return "—"

def fmt_float(x, nd=2):
    try:
        return f"{float(x):.{nd}f}".replace(".", ",")
    except Exception:
        return "—"

def df_to_html_table(df, numeric_cols=None, max_rows=None):
    if max_rows is None:
        max_rows = get_config()["reporte"]["max_filas_tabla_html"]
    df_show = df.copy()
    if max_rows and len(df_show) > max_rows:
        df_show = df_show.head(max_rows)
    html = df_show.to_html(index=False, escape=True)
    if numeric_cols:
        for col in numeric_cols:
            html = html.replace(f"<th>{col}</th>", f'<th class="num">{col}</th>')
    return html


def limpiar_outliers(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Elimina registros con vertimiento = 0."""
    df_clean = df_vertimientos[df_vertimientos["vertimiento"] != 0].copy()
    print(f"Se eliminaron {len(df_vertimientos) - len(df_clean)} registros con vertimiento = 0")
    return df_clean


def tabla_maximos_por_periodo(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Máximo vertimiento por periodo con detalle temporal y central/tecnología."""
    idx_max = df_vertimientos.groupby("periodo")["vertimiento"].idxmax()
    df_max = df_vertimientos.loc[
        idx_max,
        ["periodo", "nombre_central", "tipo", "dia", "hora", "minuto", "vertimiento"],
    ].reset_index(drop=True)
    return df_max.rename(columns={"vertimiento": "vertimiento_max_kwh"})


# -----------------------
# Main
# -----------------------

def main(
    fecha_inicio,
    fecha_fin,
    fecha_inicio_trimestral,
    fecha_comparacion_inicio,
    fecha_comparacion_fin,
    fecha_comparacion_inicio_trimestral,
):
    # Crear carpetas
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    # -----------------------
    # Templates
    # -----------------------
    shutil.copy(TEMPL_DIR / "template_reporte.pptx", PPT_PATH)

    # -----------------------
    # Rutas CSV — ventana simple
    # -----------------------
    ruta_vertimientos            = BASE_DIR / "data" / "raw" / "db" / "vertimientos.csv"
    ruta_vertimientos_comparacion= BASE_DIR / "data" / "raw" / "db" / "vertimientos_comparacion.csv"
    ruta_cmg                     = BASE_DIR / "data" / "raw" / "db" / "cmg.csv"
    ruta_cmg_comparacion         = BASE_DIR / "data" / "raw" / "db" / "cmg_comparacion.csv"
    ruta_gx_real                 = BASE_DIR / "data" / "raw" / "db" / "gx_real.csv"
    ruta_gx_real_comparacion     = BASE_DIR / "data" / "raw" / "db" / "gx_real_comparacion.csv"
    ruta_gx_real_comparacion_2022= BASE_DIR / "data" / "raw" / "db" / "gx_real_comparacion_2022.csv"

    # -----------------------
    # Rutas CSV — ventana trimestral
    # -----------------------
    ruta_gx_real_trim                    = BASE_DIR / "data" / "raw" / "db" / "gx_real_trim.csv"
    ruta_gx_real_trim_comparacion        = BASE_DIR / "data" / "raw" / "db" / "gx_real_trim_comparacion.csv"
    ruta_vertimientos_trim               = BASE_DIR / "data" / "raw" / "db" / "vertimientos_trim.csv"
    ruta_vertimientos_trim_comparacion   = BASE_DIR / "data" / "raw" / "db" / "vertimientos_trim_comparacion.csv"

    # Otras rutas
    ruta_graficos_excel  = BASE_DIR / "data" / "processed" / "reports" / "graficos.xlsx"
    ruta_template_excel  = BASE_DIR / "data" / "raw" / "template" / "template_graficos.xlsx"

    # =========================
    # 1) Obtener datos
    # =========================
    if DEV:
        print("🔧 Modo desarrollo: cargando CSV locales...")

        df_vertimientos              = pd.read_csv(ruta_vertimientos,             encoding="utf-8", sep=";")
        df_vertimientos_comparacion  = pd.read_csv(ruta_vertimientos_comparacion, encoding="utf-8", sep=";")
        df_vertimientos_trim             = pd.read_csv(ruta_vertimientos_trim,             encoding="utf-8", sep=";")
        df_vertimientos_trim_comparacion = pd.read_csv(ruta_vertimientos_trim_comparacion, encoding="utf-8", sep=";")

        df_cmg_all             = pd.read_csv(ruta_cmg,              encoding="utf-8", sep=";")
        df_cmg_all_comparacion = pd.read_csv(ruta_cmg_comparacion,  encoding="utf-8", sep=";")

        df_gx_real                 = pd.read_csv(ruta_gx_real,                  encoding="utf-8", sep=";")
        df_gx_real_comparacion     = pd.read_csv(ruta_gx_real_comparacion,      encoding="utf-8", sep=";")
        df_gx_real_comparacion_2022= pd.read_csv(ruta_gx_real_comparacion_2022, encoding="utf-8", sep=";")
        df_gx_real_trim            = pd.read_csv(ruta_gx_real_trim,             encoding="utf-8", sep=";")
        df_gx_real_trim_comparacion= pd.read_csv(ruta_gx_real_trim_comparacion, encoding="utf-8", sep=";")

    else:
        print("🗄️  Modo producción: extrayendo desde base de datos...")

        # ── Vertimientos ventana simple ───────────────────────────
        df_vertimientos, df_vertimientos_comparacion = extrae_data_total_vertimientos(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_comparacion_inicio=fecha_comparacion_inicio,
            fecha_comparacion_fin=fecha_comparacion_fin,
        )
        df_vertimientos.to_csv(ruta_vertimientos,             index=False, encoding="utf-8", sep=";")
        df_vertimientos_comparacion.to_csv(ruta_vertimientos_comparacion, index=False, encoding="utf-8", sep=";")
        print("📁 CSV vertimientos (simple) guardados.")

        # ── Vertimientos ventana trimestral ───────────────────────
        df_vertimientos_trim, df_vertimientos_trim_comparacion = extrae_data_total_vertimientos(
            fecha_inicio=fecha_inicio_trimestral,
            fecha_fin=fecha_fin,
            fecha_comparacion_inicio=fecha_comparacion_inicio_trimestral,
            fecha_comparacion_fin=fecha_comparacion_fin,
        )
        df_vertimientos_trim.to_csv(ruta_vertimientos_trim,             index=False, encoding="utf-8", sep=";")
        df_vertimientos_trim_comparacion.to_csv(ruta_vertimientos_trim_comparacion, index=False, encoding="utf-8", sep=";")
        print("📁 CSV vertimientos (trimestral) guardados.")

        # ── CMg ───────────────────────────────────────────────────
        df_cmg_all, df_cmg_all_comparacion = extrae_data_cmg(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_inicio_comparacion=fecha_comparacion_inicio,
            fecha_fin_comparacion=fecha_comparacion_fin,
        )
        df_cmg_all.to_csv(ruta_cmg,             index=False, encoding="utf-8", sep=";")
        df_cmg_all_comparacion.to_csv(ruta_cmg_comparacion, index=False, encoding="utf-8", sep=";")
        print("📁 CSV CMg guardados.")

        # ── GX real ventana simple ────────────────────────────────
        df_gx_real, df_gx_real_comparacion = extrae_gx_real(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_inicio_comparacion=fecha_comparacion_inicio,
            fecha_fin_comparacion=fecha_comparacion_fin,
        )
        df_gx_real_comparacion_2022 = extrae_gx_real_comparacion()

        df_gx_real.to_csv(ruta_gx_real,                  index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        df_gx_real_comparacion.to_csv(ruta_gx_real_comparacion,      index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        df_gx_real_comparacion_2022.to_csv(ruta_gx_real_comparacion_2022, index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        print("📁 CSV GX real (simple) guardados.")

        # ── GX real ventana trimestral ────────────────────────────
        df_gx_real_trim, df_gx_real_trim_comparacion = extrae_gx_real(
            fecha_inicio=fecha_inicio_trimestral,
            fecha_fin=fecha_fin,
            fecha_inicio_comparacion=fecha_comparacion_inicio_trimestral,
            fecha_fin_comparacion=fecha_comparacion_fin,
        )
        df_gx_real_trim.to_csv(ruta_gx_real_trim,             index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        df_gx_real_trim_comparacion.to_csv(ruta_gx_real_trim_comparacion, index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        print("📁 CSV GX real (trimestral) guardados.")

    # =========================
    # 2) Limpieza
    # =========================

    # Limpieza de strings en todos los df de vertimientos
    for _df in [df_vertimientos, df_vertimientos_comparacion,
                df_vertimientos_trim, df_vertimientos_trim_comparacion]:
        _df["tipo"] = (
            _df["tipo"].astype(str)
            .str.replace(r"[\r\n]+", "", regex=True)
            .str.strip()
        )
        _df["nombre_central"] = (
            _df["nombre_central"].astype(str)
            .str.replace(r"[\r\n]+", " ", regex=True)
            .str.strip()
        )

    # Eliminar registros con vertimiento = 0
    df_vertimientos                  = limpiar_outliers(df_vertimientos)
    df_vertimientos_comparacion      = limpiar_outliers(df_vertimientos_comparacion)
    df_vertimientos_trim             = limpiar_outliers(df_vertimientos_trim)
    df_vertimientos_trim_comparacion = limpiar_outliers(df_vertimientos_trim_comparacion)

    # CMg — truncar a mes y agregar
    df_cmg_all["fecha_hora"] = pd.to_datetime(df_cmg_all["fecha_hora"])
    df_cmg_detalle = df_cmg_all.copy()
    df_cmg_all["fecha_hora"] = df_cmg_all["fecha_hora"].dt.strftime("%Y-%m")

    df_cmg = (
        df_cmg_all
        .groupby(["fecha_hora", "nombre_cmg"], as_index=False)
        .agg({"CMG_PESO_KWH": "mean"})
    )
    df_cmg_out = CSV_DIR / "df_cmg.csv"
    df_cmg.to_csv(df_cmg_out, encoding="utf-8", sep=";")

    # =========================
    # 3) Cálculos intermedios
    # =========================

    # Día típico — ventana simple
    df_gx_real_tipico           = gx_real_tipico(df_gx_real)
    fecha_tipica                = df_gx_real_tipico["fecha_tipica"]
    df_dia_tipico               = df_gx_real_tipico["df_dia_tipico"]
    print("Fecha típica:", fecha_tipica)

    # Día típico comparación
    df_gx_real_tipico_comparacion   = gx_real_tipico(df_gx_real_comparacion_2022)
    fecha_tipica_comparacion        = df_gx_real_tipico_comparacion["fecha_tipica"]
    df_dia_tipico_comparacion       = df_gx_real_tipico_comparacion["df_dia_tipico"]
    print("Fecha típica comparación:", fecha_tipica_comparacion)

    # Spread CMg
    df_spread = spread_cmg(df_cmg_detalle)
    df_spread.to_csv(CSV_DIR / "df_spread.csv", encoding="utf-8", sep=";")

    # Generación inyectada vs vertida — ventana simple
    df_gx_ver_iny = gx_ver_iny(df_gx_real, df_vertimientos)

    # Top vertimientos — ventana simple
    df_top_vertimientos = top_vertimientos(df_vertimientos)

    # =========================
    # 4) Generar gráficos
    # =========================
    generar_graficas(
        # Vertimientos ventana simple
        df_vertimientos=df_vertimientos,
        df_vertimientos_comparacion=df_vertimientos_comparacion,
        # Vertimientos ventana trimestral
        df_vertimientos_trim=df_vertimientos_trim,
        df_vertimientos_trim_comparacion=df_vertimientos_trim_comparacion,
        # CMg
        df_spread=df_spread,
        df_cmg=df_cmg,
        df_cmg_comparacion=df_cmg_all_comparacion,
        # Día típico
        df_dia_tipico=df_dia_tipico,
        df_dia_tipico_comparacion=df_dia_tipico_comparacion,
        fecha_tipica=fecha_tipica,
        fecha_tipica_comparacion=fecha_tipica_comparacion,
        # GX real ventana simple
        gx_real=df_gx_real,
        gx_real_comparacion=df_gx_real_comparacion,
        # GX real ventana trimestral
        df_gx_real_trim=df_gx_real_trim,
        df_gx_real_trim_comparacion=df_gx_real_trim_comparacion,
        # Otros
        df_gx_ver_iny=df_gx_ver_iny,
        df_top_vertimiento=df_top_vertimientos,
        # Parámetros temporales para gráficos trimestrales
        mes_reporte=fecha_fin.month,
        anio_reporte=fecha_fin.year,
        # Rutas
        ppt_path=PPT_PATH,
        outdir=str(IMG_DIR),
    )

    # =========================
    # 5) KPIs
    # =========================

    # ── Vertimientos ──────────────────────────────────────────────
    vertimiento_total    = float(df_vertimientos["vertimiento"].sum())
    empresa_vert_max     = df_top_vertimientos["Nombre central"].iloc[0]
    vert_empresa_vert_max= df_top_vertimientos["Reducción renovable"].iloc[0]

    # ── CMg ───────────────────────────────────────────────────────
    cmg_mes  = df_cmg.groupby("fecha_hora", as_index=False)["CMG_PESO_KWH"].mean()
    cmg_prom = float(cmg_mes["CMG_PESO_KWH"].mean())

    idx_cmg_max     = cmg_mes["CMG_PESO_KWH"].idxmax()
    cmg_max         = float(cmg_mes.loc[idx_cmg_max, "CMG_PESO_KWH"])
    cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_hora"])

    # ── Spread ────────────────────────────────────────────────────
    idx_spread_min   = df_spread["spread_abs"].idxmax()
    barra_spread_min = df_spread.loc[idx_spread_min, "nombre_cmg"]

    def _get_spread_barra(nombre_cmg):
        row = df_spread[df_spread["nombre_cmg"] == nombre_cmg]
        return float(row["spread_abs"].iloc[0]) if not row.empty else 0.0

    spread_max_crucero = _get_spread_barra("CRUCERO_______220")
    spread_max_p_montt = _get_spread_barra("P.MONTT_______220")

    df_cmg_detalle["fecha_hora"] = pd.to_datetime(df_cmg_detalle["fecha_hora"])
    df_cmg_detalle["es_solar"]   = df_cmg_detalle["fecha_hora"].dt.hour.between(8, 18)
    df_cmg_detalle["fecha"]      = df_cmg_detalle["fecha_hora"].dt.date

    df_spread_diario = (
        df_cmg_detalle
        .groupby(["fecha", "nombre_cmg", "es_solar"], as_index=False)["CMG_PESO_KWH"].mean()
        .pivot_table(index=["fecha", "nombre_cmg"], columns="es_solar", values="CMG_PESO_KWH")
        .rename_axis(columns=None)
        .reset_index()
        .rename(columns={False: "no_solar", True: "solar"})
    )
    df_spread_diario["spread_dia"] = (df_spread_diario["no_solar"] - df_spread_diario["solar"]).abs()
    df_spread_diario.to_csv(CSV_DIR / "df_spread_diario.csv", encoding="utf-8", sep=";")

    def _dia_max_spread(nombre_cmg):
        df_b = df_spread_diario[df_spread_diario["nombre_cmg"] == nombre_cmg]
        if df_b.empty:
            return "—"
        return str(df_b.sort_values("spread_dia", ascending=False).iloc[0]["fecha"])

    dia_spread_crucero = _dia_max_spread("CRUCERO_______220")
    dia_spread_p_montt = _dia_max_spread("P.MONTT_______220")

    empresa_vert_max = empresa_vert_max.replace("PFV", "").replace("Pfv", "").strip().title()

    kpis = {
        # Vertimientos
        "vert_total_mwh":           fmt_int(vertimiento_total),
        "vert_total_mwh_clave":     f"{fmt_int(vertimiento_total)} MWh",
        "empresa_vert_max":         empresa_vert_max,
        "vert_empresa_vert_max":    f"{fmt_int(vert_empresa_vert_max)} MWh",
        # CMg
        "cmg_promedio":             fmt_float(cmg_prom),
        "cmg_promedio_clave":       f"{fmt_float(cmg_prom)} $/kWh",
        "cmg_max":                  fmt_float(cmg_max),
        "cmg_max_mensual_periodo":  cmg_max_periodo,
        # Spread
        "cmg_spread_max_crucero":               f"{fmt_float(spread_max_crucero)} $/kWh",
        "cmg_spread_max_p_montt":               f"{fmt_float(spread_max_p_montt)} $/kWh",
        "dia_cmg_spread_max_periodo_charrua":   dia_spread_crucero,
        "dia_cmg_spread_max_periodo_p_montt":   fmt_float(dia_spread_p_montt),
        "barra_cmg_spread_min":                 barra_spread_min,
        # Perfiles día típico
        "fecha_perfil_1":       str(fecha_tipica),
        "fecha_perfil_2":       str(fecha_tipica_comparacion),
        "fecha_referencia_1":   str(fecha_tipica),
        "fecha_referencia_2":   str(fecha_tipica_comparacion),
    }

    # =========================
    # 6) Inserciones texto PPT
    # =========================
    periodo_estudio = f"{fecha_inicio.strftime('%Y-%m')} → {fecha_fin.strftime('%Y-%m')}"
    insertar_periodo_estudio(PPT_PATH, periodo_estudio)
    insertar_texto_con_placeholders(PPT_PATH, kpis)

    # =========================
    # 7) Exportar PPT → PDF
    # =========================
    exportar_ppt_a_pdf(PPT_PATH, PDF_PATH)


# -----------------------
# Entry point
# -----------------------

if __name__ == "__main__":

    def trimestre_del_mes(mes: int) -> int:
        return (mes - 1) // 3 + 1

    def meses_desde_inicio_trimestre(mes: int) -> int:
        return (mes - 1) % 3

    def calcular_inicio_trimestral(fecha_fin: pd.Timestamp, meses_historico: int) -> pd.Timestamp:
        fecha_ancla = fecha_fin - pd.DateOffset(months=meses_historico)
        primer_mes_trimestre = (trimestre_del_mes(fecha_ancla.month) - 1) * 3 + 1
        fecha_inicio = fecha_ancla.replace(
            month=primer_mes_trimestre, day=1,
            hour=0, minute=0, second=0, microsecond=0
        )
        return fecha_inicio

    _cfg = get_config()

    fecha_fin = pd.to_datetime(FECHA_ESTUDIO, format="%Y-%m")

    # Ventana simple
    fecha_inicio = fecha_fin - pd.DateOffset(months=_cfg["reporte"]["meses_historico"])
    fecha_inicio = fecha_inicio.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Ventana trimestral
    fecha_inicio_trimestral = calcular_inicio_trimestral(
        fecha_fin, _cfg["reporte"]["meses_historico"]
    )

    # Fechas de comparación
    _anios = _cfg["reporte"]["anios_comparacion"]
    fecha_comparacion_inicio             = fecha_inicio            - pd.DateOffset(years=_anios)
    fecha_comparacion_fin                = fecha_fin               - pd.DateOffset(years=_anios)
    fecha_comparacion_inicio_trimestral  = fecha_inicio_trimestral - pd.DateOffset(years=_anios)

    print(f"Fecha fin:                            {fecha_fin:%Y-%m}")
    print(f"Fecha inicio (simple):                {fecha_inicio:%Y-%m}")
    print(f"Fecha inicio (trimestral):            {fecha_inicio_trimestral:%Y-%m}")
    print(f"Comparación inicio (simple):          {fecha_comparacion_inicio:%Y-%m}")
    print(f"Comparación inicio (trimestral):      {fecha_comparacion_inicio_trimestral:%Y-%m}")
    print(f"Comparación fin:                      {fecha_comparacion_fin:%Y-%m}")

    main(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        fecha_inicio_trimestral=fecha_inicio_trimestral,
        fecha_comparacion_inicio=fecha_comparacion_inicio,
        fecha_comparacion_fin=fecha_comparacion_fin,
        fecha_comparacion_inicio_trimestral=fecha_comparacion_inicio_trimestral,
    )
