# main.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd

from utils.extrae_data import (
    extrae_data_total_vertimientos,
    extrae_data_cmg,
    extrae_gx_real,
)
from utils.graficos import generar_graficas
from utils.pdf_chromium import render_html_to_png
from utils.calcula_gx_tipico import gx_real_tipico
from utils.calcula_spread_cmg import spread_cmg
# -----------------------
# Config
# -----------------------


BASE_DIR = Path(__file__).parent
TEMPL_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
IMG_DIR = BASE_DIR / "data" / "processed" / "images"
OUT_DIR = BASE_DIR / "data" / "processed" / "reports"

PNG_PATH_1 = OUT_DIR / "png" / "plantilla_reporte_p1.png"
PNG_PATH_2 = OUT_DIR / "png" / "plantilla_reporte_p2.png"
PNG_PATH_3 = OUT_DIR / "png" / "plantilla_reporte_p3.png"
HTML_PATH_1 = OUT_DIR / "html" / "plantilla_reporte_p1.html"
HTML_PATH_2 = OUT_DIR / "html" / "plantilla_reporte_p2.html"
HTML_PATH_3 = OUT_DIR / "html" / "plantilla_reporte_p3.html"



TEMPLATE_NAME_1 = "reporte_p1.html"
TEMPLATE_NAME_2 = "reporte_p2.html"
TEMPLATE_NAME_3 = "reporte_p3.html"
PDF_NAME = "reporte.pdf"
DEV = False 
GENERAR_PLANTILLA =True
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

def df_to_html_table(df, numeric_cols=None, max_rows=30):
    """
    Convierte DF a HTML (pandas) y marca columnas numéricas con class 'num'
    para alineación a la derecha via CSS.
    """
    df_show = df.copy()
    if max_rows and len(df_show) > max_rows:
        df_show = df_show.head(max_rows)

    # Pandas HTML
    html = df_show.to_html(index=False, escape=True)

    # Agrega class="num" a th/td de columnas numéricas
    if numeric_cols:
        for col in numeric_cols:
            # Header
            html = html.replace(f"<th>{col}</th>", f'<th class="num">{col}</th>')
         
    return html


def limpiar_outliers(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Elimina registros con kwh = 0."""
    df_clean = df_vertimientos[df_vertimientos["vertimiento"] != 0].copy()
    print(f"Se eliminaron {len(df_vertimientos) - len(df_clean)} registros de vertimientos con kwh = 0")
    return df_clean


def tabla_maximos_por_periodo(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Máximo vertimiento por periodo con detalle temporal y central/tecnología."""
    idx_max = df_vertimientos.groupby("periodo")["vertimiento"].idxmax()
    df_max = df_vertimientos.loc[
        idx_max,
        ["periodo", "nombre_central", "tipo", "dia", "hora", "minuto", "vertimiento"],
    ].reset_index(drop=True)
    return df_max.rename(columns={"vertimiento": "vertimiento_max_kwh"})


def tabla_maximos_acumulados_por_periodo(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Top 5 mayores vertimientos acumulados (suma por central/tecnología por periodo)."""

    df_acum = (
        df_vertimientos.groupby(
            ["periodo", "nombre_central", "tipo"],
            as_index=False
        )
        .agg({"vertimiento": "sum"})
    )

    # Obtener el máximo por periodo
    idx_max = df_acum.groupby("periodo")["vertimiento"].idxmax()

    df_max = (
        df_acum.loc[idx_max, ["periodo", "nombre_central", "tipo", "vertimiento"]]
        .rename(columns={"vertimiento": "vertimiento_acumulado_kwh"})
        .copy()
    )

    # 🔥 Top 5 global
    df_top5 = (
        df_max
        .sort_values("vertimiento_acumulado_kwh", ascending=False)
        .head(8)
        .reset_index(drop=True)
    )

    return df_top5

# -----------------------
# Main
# -----------------------
def main(fecha_inicio, fecha_fin):
    # Crear carpetas
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    #ruta_vertimientos_csv = BASE_DIR / "data" / "raw" / "extraido_db" / "vertimientos.csv"
    ruta_vertimientos_total_csv = BASE_DIR / "data" / "raw" / "extraido_db" / "vertimientos.csv"
    ruta_cmg_csv = BASE_DIR / "data" / "raw" / "extraido_db" / "cmg.csv"
    ruta_gx_real = BASE_DIR / "data" / "raw" / "extraido_db" / "gx_real.csv"

    # =========================
    # 1) Obtener datos
    # =========================
    if DEV:
        print("🔧 Modo desarrollo: cargando CSV locales...")

        #df_vertimientos_totales = pd.read_csv(ruta_vertimientos_csv)
        df_vertimientos = pd.read_csv(ruta_vertimientos_total_csv)
        df_cmg_all = pd.read_csv(ruta_cmg_csv)
        df_gx_real = pd.read_csv(ruta_gx_real)
        df_vertimientos_totales=df_vertimientos.groupby(["periodo"], as_index=False).agg({"vertimiento": "sum"})

    else:
        print("🗄️  Modo producción: extrayendo desde base de datos...")

        #df_vertimientos_totales, _ = extract_data_vertimientos(
        #    fecha_inicio=fecha_inicio,
        #    fecha_fin=fecha_fin
        #)

        df_vertimientos = extrae_data_total_vertimientos(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        df_cmg_all = extrae_data_cmg(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        df_gx_real=extrae_gx_real(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        # Guardar CSV para reutilizar        
        df_vertimientos.to_csv(ruta_vertimientos_total_csv, index=False)        
        df_cmg_all.to_csv(ruta_cmg_csv, index=False)
        df_gx_real.to_csv(
            ruta_gx_real,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S"
        )
        df_vertimientos_totales=df_vertimientos.groupby(["periodo"], as_index=False).agg({"vertimiento": "sum"})


        print("📁 CSV guardados para futuras ejecuciones DEV.")

    # =========================
    # 1) Limpieza
    # =========================
    df_vertimientos = limpiar_outliers(df_vertimientos)

    df_maximos = tabla_maximos_por_periodo(df_vertimientos)
    df_max_acum = tabla_maximos_acumulados_por_periodo(df_vertimientos)

    #Truncamos el dato fecha_hora
    df_cmg_all['fecha_hora']=pd.to_datetime(df_cmg_all['fecha_hora'])
    df_cmg_all['fecha_hora'] = df_cmg_all['fecha_hora'].dt.strftime('%Y-%m')

    df_cmg = (
        df_cmg_all.groupby(["fecha_hora", "nombre_cmg"], as_index=False)
        .agg({"CMG_PESO_KWH": "mean"})
    )

    print("Primeras filas de dataframe cmg")
    print(df_cmg_all.head())

    # =========================
    # 1.1) Generación real día típico
    # =========================
    print(df_gx_real.head())
    df_gx_real_tipico=gx_real_tipico(df_gx_real)
    print("Fecha típica:", df_gx_real_tipico["fecha_tipica"])
    print(df_gx_real_tipico["distancias"].head())
    df_dia_tipico = df_gx_real_tipico["df_dia_tipico"]
    print(df_dia_tipico.head())
    df_dia_tipico.to_csv(OUT_DIR/"dia_tipico.csv")
    print("Cantidad de horas únicas:", df_dia_tipico["hora_decimal"].nunique())
    
    # =========================
    # 1.2) Spread CMG
    # =========================
    df_spread=spread_cmg(df_cmg_all)

    

    # =========================
    # 2) Generar gráficos
    # =========================
    generar_graficas(
        df_vertimientos_totales, df_spread, df_cmg, df_dia_tipico,
        outdir=str(IMG_DIR)
    )

    # =========================
    # 3) KPIs
    # =========================
    def fmt_int(x):
        try:
            return f"{int(round(float(x))):,}".replace(",", ".")
        except:
            return "—"

    def fmt_float(x, nd=2):
        try:
            return f"{float(x):.{nd}f}".replace(".", ",")
        except:
            return "—"

    vert_total = float(df_vertimientos_totales["vertimiento"].sum())
    vert_prom = float(df_vertimientos_totales["vertimiento"].mean())
    idx_max = df_vertimientos_totales["vertimiento"].idxmax()
    #Empresa que presenta el maximo vertimiento en el periodo de análisis 
    df_max_acum["periodo"] = pd.to_datetime(df_max_acum["periodo"])
    print(df_max_acum)
    #fila con mayor vertimiento máximo acumulado
    idx_max = df_max_acum["vertimiento_acumulado_kwh"].idxmax()
    empresa_vert_max = df_max_acum.loc[idx_max, "nombre_central"]
    periodo_empresa_max = df_max_acum.loc[idx_max, "periodo"]    
    periodo_empresa_max = periodo_empresa_max.strftime("%Y-%m")
    vert_empresa_vert_max=df_max_acum.loc[df_max_acum["vertimiento_acumulado_kwh"].idxmax(), "vertimiento_acumulado_kwh"]

    vert_max = float(df_vertimientos_totales.loc[idx_max, "vertimiento"])
    vert_max_periodo = str(df_vertimientos_totales.loc[idx_max, "periodo"])


    cmg_mes = df_cmg.groupby("fecha_hora", as_index=False)["CMG_PESO_KWH"].mean()
    cmg_prom = float(cmg_mes["CMG_PESO_KWH"].mean())

    idx_cmg_max = cmg_mes["CMG_PESO_KWH"].idxmax()
    cmg_max = float(cmg_mes.loc[idx_cmg_max, "CMG_PESO_KWH"])

    try:
        cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_hora"].date())
    except:
        cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_hora"])


    if GENERAR_PLANTILLA == True:

        kpis = {
            "vert_total_mwh": fmt_int(vert_total),         #Vertimientos totales
            "vert_prom_mensual_mwh": fmt_int(vert_prom),   #Promedio mensual de energia vertida
            "vert_max_mensual_mwh": fmt_int(vert_max),     #Vertimiento maximo mensual
            "vert_max_mensual_periodo": vert_max_periodo,  #Mes en el que se produjo el máximo vertimiento
            "cmg_promedio": fmt_float(cmg_prom),           #Costo marginal promedio
            "cmg_max_mensual": fmt_float(cmg_max),         #Costo marginal maximo por mes
            "cmg_max_mensual_periodo": cmg_max_periodo,    #Costos marginal maximo en el periodo de estudio
            "empresa_vert_max":empresa_vert_max,             #Empresa que presenta el maximo vertimiento acumulado     
            "periodo_empresa_max":periodo_empresa_max,       #Periodo en el que empresa_vert_max presente mayores vertimientos
            "vert_empresa_vert_max": vert_empresa_vert_max,   #Cantidad de energia vertida por empresa_vert_max
            #"vert_empresa_vert_max_pct" :vert_empresa_vert_max_pct                  # porción de la energía vertida por la empresa respecto del total vertido
            #"cmg_spread_max"                              #spread maximo 
            #"dia_cmg_spread_max_periodo"                  # Día en el que se produce el spread máximo
            #"barra_cmg_spread_max"                        #Barra en la que se genera el spread máximo
        }

        # =========================
        # 4) Tablas HTML
        # =========================
        tabla_max = df_maximos.copy()
        tabla_acum = df_max_acum.copy()

        tabla_max["vertimiento_max_kwh"] = tabla_max["vertimiento_max_kwh"].map(fmt_int)
        tabla_acum["vertimiento_acumulado_kwh"] = tabla_acum["vertimiento_acumulado_kwh"].map(fmt_int)

        tables_html = {
            "maximos": tabla_max.to_html(index=False, escape=True, classes="tbl", border=0),
            "acumulados": tabla_acum.to_html(index=False, escape=True, classes="tbl", border=0),
        }

if __name__ == "__main__":
    fecha_inicio = "2024-01-01 00:00:00"
    fecha_fin = "2024-12-31 : 23:45:00"
    main(fecha_inicio,fecha_fin)