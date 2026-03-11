# main.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd

from utils.extrae_data import (
    extract_data_vertimientos,
    extract_data_total_vertimientos,
    extract_data_cmg,
)
from utils.graficos import generar_graficas
from utils.pdf_chromium import render_html_to_pdf

# -----------------------
# Config
# -----------------------


BASE_DIR = Path(__file__).parent
TEMPL_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
IMG_DIR = BASE_DIR / "data" / "processed" / "images"
OUT_PDF_DIR = BASE_DIR / "data" / "processed" / "reports"

TEMPLATE_NAME = "reporte.html"
PDF_NAME = "reporte.pdf"
DEV = True 

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
            # Celdas: pandas pone <td>VAL</td>
            # Ojo: esto es best-effort; lo más robusto es Styler, pero así basta.
    return html


def limpiar_outliers(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Elimina registros con kwh = 0."""
    df_clean = df_vertimientos[df_vertimientos["kwh"] != 0].copy()
    print(f"Se eliminaron {len(df_vertimientos) - len(df_clean)} registros de vertimientos con kwh = 0")
    return df_clean


def tabla_maximos_por_periodo(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Máximo vertimiento por periodo con detalle temporal y central/tecnología."""
    idx_max = df_vertimientos.groupby("periodo")["kwh"].idxmax()
    df_max = df_vertimientos.loc[
        idx_max,
        ["periodo", "nombre_infotecnica", "tecnologia", "dia", "hora", "minuto", "kwh"],
    ].reset_index(drop=True)
    return df_max.rename(columns={"kwh": "vertimiento_max_kwh"})


def tabla_maximos_acumulados_por_periodo(df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    """Top 5 mayores vertimientos acumulados (suma por central/tecnología por periodo)."""

    df_acum = (
        df_vertimientos.groupby(
            ["periodo", "nombre_infotecnica", "tecnologia"],
            as_index=False
        )
        .agg({"kwh": "sum"})
    )

    # Obtener el máximo por periodo
    idx_max = df_acum.groupby("periodo")["kwh"].idxmax()

    df_max = (
        df_acum.loc[idx_max, ["periodo", "nombre_infotecnica", "tecnologia", "kwh"]]
        .rename(columns={"kwh": "vertimiento_acumulado_kwh"})
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
    OUT_PDF_DIR.mkdir(parents=True, exist_ok=True)

    #ruta_vertimientos_csv = BASE_DIR / "data" / "raw" / "extraido_db" / "vertimientos.csv"
    ruta_vertimientos_total_csv = BASE_DIR / "data" / "raw" / "extraido_db" / "vertimientos.csv"
    ruta_cmg_csv = BASE_DIR / "data" / "raw" / "extraido_db" / "cmg.csv"

    # =========================
    # 1) Obtener datos
    # =========================
    if DEV:
        print("🔧 Modo desarrollo: cargando CSV locales...")

        #df_vertimientos_totales = pd.read_csv(ruta_vertimientos_csv)
        df_vertimientos = pd.read_csv(ruta_vertimientos_total_csv)
        df_cmg_all = pd.read_csv(ruta_cmg_csv)
        df_vertimientos_totales=df_vertimientos.groupby(["periodo"], as_index=False).agg({"kwh": "sum"})

    else:
        print("🗄️  Modo producción: extrayendo desde base de datos...")

        #df_vertimientos_totales, _ = extract_data_vertimientos(
        #    fecha_inicio=fecha_inicio,
        #    fecha_fin=fecha_fin
        #)

        df_vertimientos = extract_data_total_vertimientos(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        df_cmg_all = extract_data_cmg(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )

        # Guardar CSV para reutilizar
        #df_vertimientos_totales.to_csv(ruta_vertimientos_csv, index=False)
        df_vertimientos.to_csv(ruta_vertimientos_total_csv, index=False)
        df_cmg_all.to_csv(ruta_cmg_csv, index=False)

        print("📁 CSV guardados para futuras ejecuciones DEV.")

    # =========================
    # Limpieza
    # =========================
    df_vertimientos = limpiar_outliers(df_vertimientos)

    df_maximos = tabla_maximos_por_periodo(df_vertimientos)
    df_max_acum = tabla_maximos_acumulados_por_periodo(df_vertimientos)

    df_cmg = (
        df_cmg_all.groupby(["fecha_version", "nombre_cmg"], as_index=False)
        .agg({"CMG_PESO_KWH": "mean"})
    )

    # =========================
    # 2) Generar gráficos
    # =========================
    generar_graficas(
        df_vertimientos_totales, df_vertimientos, df_maximos, df_max_acum, df_cmg,
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

    vert_total = float(df_vertimientos_totales["kwh"].sum())
    vert_prom = float(df_vertimientos_totales["kwh"].mean())
    idx_max = df_vertimientos_totales["kwh"].idxmax()
    #Empresa que presenta el maximo vertimiento en el periodo de análisis 
    print(df_max_acum)
    #fila con mayor vertimiento máximo acumulado
    idx_max = df_max_acum["vertimiento_acumulado_kwh"].idxmax()
    empresa_vert_max = df_max_acum.loc[idx_max, "nombre_infotecnica"]
    periodo_empresa_max = df_max_acum.loc[idx_max, "periodo"]
    periodo_empresa_max = periodo_empresa_max[:7] 
    vert_empresa_vert_max=df_max_acum.loc[df_max_acum["vertimiento_acumulado_kwh"].idxmax(), "vertimiento_acumulado_kwh"]

    vert_max = float(df_vertimientos_totales.loc[idx_max, "kwh"])
    vert_max_periodo = str(df_vertimientos_totales.loc[idx_max, "periodo"])


    cmg_mes = df_cmg.groupby("fecha_version", as_index=False)["CMG_PESO_KWH"].mean()
    cmg_prom = float(cmg_mes["CMG_PESO_KWH"].mean())

    idx_cmg_max = cmg_mes["CMG_PESO_KWH"].idxmax()
    cmg_max = float(cmg_mes.loc[idx_cmg_max, "CMG_PESO_KWH"])

    try:
        cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_version"].date())
    except:
        cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_version"])



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

    # =========================
    # 5) Renderizar PDF
    # =========================
    css_path = ASSETS_DIR / "reporte.css"
    logo_path = ASSETS_DIR / "logo.png"

    def img_uri(stem):
        svg = IMG_DIR / f"{stem}.svg"
        png = IMG_DIR / f"{stem}.png"
        if svg.exists():
            return svg.as_uri()
        if png.exists():
            return png.as_uri()
        return None

    # Convertir fecha_inicio a formato YYYY-MM
    fecha_inicio = fecha_inicio[:7]  # Extrae "2024-01" de "2024-01-01"
    fecha_fin = fecha_fin[:7]  # Extrae "2024-01" de "2024-01-01"
    context = {
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
        "generado_el": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "css_href": css_path.as_uri(),
        "logo_href": logo_path.as_uri() if logo_path.exists() else None,
        "kpis": kpis,
        "tables_html": tables_html,
        "imgs": {
            "cmg": img_uri("cmg"),
            "boxplot": img_uri("boxplot"),
            "total_mwh": img_uri("total_kwh"),
            "background_href" :img_uri("fondo_energia"),
            "logo_energia": img_uri("logo_energia"),
            "mapa_barras": img_uri("se_sen")
        },
    }

    pdf_path = OUT_PDF_DIR / PDF_NAME

    pdf_path, html_debug_path = render_html_to_pdf(
        template_dir=TEMPL_DIR,
        template_name=TEMPLATE_NAME,
        context=context,
        output_pdf=pdf_path,
        base_dir=BASE_DIR,
    )

    print("✅ PDF generado:", pdf_path)
    print("🧩 HTML (debug):", html_debug_path)


if __name__ == "__main__":
    fecha_inicio = "2024-01-01"
    fecha_fin = "2024-12-31"
    main(fecha_inicio,fecha_fin)