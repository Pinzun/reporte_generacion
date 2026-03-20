# main.py
from __future__ import annotations

from pathlib import Path
from datetime import datetime
import pandas as pd

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
from utils.inserta_texto_ppt import insertar_periodo_estudio, exportar_ppt_a_pdf,insertar_texto_con_placeholders
import shutil 

# -----------------------
# Config
# -----------------------

BASE_DIR = Path(__file__).parent
TEMPL_DIR = BASE_DIR / "data" / "raw"/ "templates"
ASSETS_DIR = BASE_DIR / "assets"
IMG_DIR = BASE_DIR / "data" / "processed" / "images"
OUT_DIR = BASE_DIR / "data" / "processed" / "reports"
CSV_DIR = BASE_DIR / "data" / "processed" / "csv"

PPT_PATH = OUT_DIR / "reporte_generacion.pptx"
PDF_PATH = OUT_DIR / "reporte_generacion.pdf"


PDF_NAME = "reporte.pdf"
DEV = False 
GENERAR_PLANTILLA =True
FECHA_ESTUDIO = "2026-01-31 23:45:00"   


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


# -----------------------
# Main
# -----------------------
def main(fecha_inicio, fecha_fin, fecha_comparacion_inicio, fecha_comparacion_fin):
    # Crear carpetas
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    # -----------------------
    # Templates
    # -----------------------
    # Siempre partir desde plantilla limpia
    shutil.copy(
        TEMPL_DIR / "template_reporte.pptx",
        PPT_PATH
    )


    #rutas de guardado de df del periodo de estudio
    ruta_vertimientos = BASE_DIR / "data" / "raw" / "db" / "vertimientos.csv"
    ruta_cmg = BASE_DIR / "data" / "raw" / "db" / "cmg.csv"
    ruta_gx_real = BASE_DIR / "data" / "raw" / "db" / "gx_real.csv"
    #rutas de guardado de df del periodo de comparacion
    ruta_vertimientos_comparacion = BASE_DIR / "data" / "raw" / "db" / "vertimientos_comparacion.csv"
    ruta_cmg_comparacion = BASE_DIR / "data" / "raw" / "db" / "cmg_comparacion.csv"
    ruta_gx_real_comparacion_2022 = BASE_DIR / "data" / "raw" / "db" / "gx_real_comparacion_2022.csv"
    ruta_gx_real_comparacion = BASE_DIR / "data" / "raw" / "db" / "gx_real_comparacion.csv"
    ruta_graficos_excel = BASE_DIR / "data" / "processed" / "reports" / "graficos.xlsx"

    #Rutas de templates
    
    ruta_template_excel = BASE_DIR / "data" / "raw" / "template" / "template_graficos.xlsx"
    # =========================
    # 1) Obtener datos
    # =========================
    if DEV:
        print("🔧 Modo desarrollo: cargando CSV locales...")

        #df_vertimientos_totales = pd.read_csv(ruta_vertimientos_csv)
        df_vertimientos = pd.read_csv(ruta_vertimientos)
        df_vertimientos_comparacion=pd.read_csv(ruta_vertimientos_comparacion)
        df_cmg_all = pd.read_csv(ruta_cmg)
        df_cmg_all_comparacion=pd.read_csv(ruta_cmg_comparacion)
        df_gx_real = pd.read_csv(ruta_gx_real)
        df_gx_real_comparacion =pd.read_csv(ruta_gx_real_comparacion)
        df_gx_real_comparacion_2022 =pd.read_csv(ruta_gx_real_comparacion_2022)
        #df_vertimientos_totales=df_vertimientos.groupby(["periodo"], as_index=False).agg({"vertimiento": "sum"})

    else:
        print("🗄️  Modo producción: extrayendo desde base de datos...") 

        df_vertimientos,df_vertimientos_comparacion = extrae_data_total_vertimientos(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_comparacion_inicio=fecha_comparacion_inicio,
            fecha_comparacion_fin=fecha_comparacion_fin
        )
        df_vertimientos.to_csv(ruta_vertimientos, index=False, sep=";")
        df_vertimientos_comparacion.to_csv(ruta_vertimientos_comparacion, index=False)        
        print("📁 CSV vertimiento Guardado para futuras ejecuciones DEV.")      

        df_cmg_all,df_cmg_all_comparacion = extrae_data_cmg(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_inicio_comparacion=fecha_comparacion_inicio,
            fecha_fin_comparacion=fecha_comparacion_fin
        )

        df_cmg_all.to_csv(ruta_cmg, index=False, sep=";")
        df_cmg_all_comparacion.to_csv(ruta_cmg_comparacion, index=False)  
        print("📁 CSV cmg Guardado para futuras ejecuciones DEV.")

        df_gx_real, df_gx_real_comparacion = extrae_gx_real(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_inicio_comparacion=fecha_comparacion_inicio,   
            fecha_fin_comparacion=fecha_comparacion_fin          
        )

        df_gx_real_comparacion_2022=extrae_gx_real_comparacion()

        df_vertimientos["tipo"] = (
        df_vertimientos["tipo"]
        .astype(str)
        .str.replace(r"[\r\n]+", "", regex=True)
        .str.strip()
            )
        
        df_vertimientos["nombre_central"] = (
        df_vertimientos["nombre_central"]
        .astype(str)
        .str.replace(r"[\r\n]+", " ", regex=True)
        .str.strip()
            )

        # Guardar CSV para reutilizar        

        df_gx_real.to_csv(
            ruta_gx_real,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S",
            sep=";"
        )
        df_gx_real_comparacion.to_csv(
            ruta_gx_real_comparacion,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S", 
            sep=";"
        )  

        df_gx_real_comparacion_2022.to_csv(
            ruta_gx_real_comparacion_2022,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S",
            sep=";"
        )  

        print("📁 CSV guardados para futuras ejecuciones DEV.")

    # =========================
    # 1) Limpieza
    # =========================
    df_vertimientos = limpiar_outliers(df_vertimientos)
    df_vertimientos_comparacion=limpiar_outliers(df_vertimientos_comparacion)
    #Truncamos el dato fecha_hora
    df_cmg_all['fecha_hora']=pd.to_datetime(df_cmg_all['fecha_hora'])
    df_cmg_detalle=df_cmg_all.copy()
    df_cmg_all['fecha_hora'] = df_cmg_all['fecha_hora'].dt.strftime('%Y-%m')

    df_cmg = (
        df_cmg_all.groupby(["fecha_hora", "nombre_cmg"], as_index=False)
        .agg({"CMG_PESO_KWH": "mean"})
    )   
    df_cmg_out= CSV_DIR / "df_cmg.csv"
    df_cmg.to_csv(df_cmg_out, encoding="utf-8", sep= ";")


    # =========================
    # 1.1) Generación real día típico
    # =========================
    df_gx_real_tipico=gx_real_tipico(df_gx_real)
    fecha_tipica= df_gx_real_tipico["fecha_tipica"]
    print("Fecha típica:",fecha_tipica )
    df_dia_tipico = df_gx_real_tipico["df_dia_tipico"]

    # =========================
    # 1.1.2) Generación real día típico comparacion
    # =========================
    df_gx_real_tipico_comparacion=gx_real_tipico(df_gx_real_comparacion_2022)
    fecha_tipica_comparacion = df_gx_real_tipico_comparacion["fecha_tipica"]
    print("Fecha típica comparacion:", fecha_tipica_comparacion )
    df_dia_tipico_comparacion = df_gx_real_tipico_comparacion["df_dia_tipico"]
   
    # =========================
    # 1.2) Spread CMG
    # =========================
    df_spread=spread_cmg(df_cmg_detalle) 
    #Guardamos csv para auditoria
    df_spread_out= CSV_DIR / "df_spread.csv"
    df_spread.to_csv(df_spread_out, encoding="utf-8", sep= ";")

    # =========================
    # 1.3) Generación inyectada vs real
    # =========================
    df_gx_ver_iny=gx_ver_iny(df_gx_real,df_vertimientos)

    # =========================
    # 1.4) Top vertimientos
    # =========================
    df_top_vertimientos=top_vertimientos(df_vertimientos)
    # =========================
    # 2) Generar gráficos
    # =========================
    generar_graficas(
    df_vertimientos=df_vertimientos,
    df_vertimientos_comparacion=df_vertimientos_comparacion,
    df_spread=df_spread,
    df_cmg=df_cmg,
    df_cmg_comparacion=df_cmg_all_comparacion,
    df_dia_tipico=df_dia_tipico,
    df_dia_tipico_comparacion=df_dia_tipico_comparacion,
    fecha_tipica=fecha_tipica,
    fecha_tipica_comparacion=fecha_tipica_comparacion,
    df_gx_ver_iny=df_gx_ver_iny,
    df_top_vertimiento=df_top_vertimientos,
    gx_real=df_gx_real,
    gx_real_comparacion=df_gx_real_comparacion,
    ppt_path= PPT_PATH,
    outdir=str(IMG_DIR),
            )


    # =========================
    # 3) KPIs
    # =========================
    # ── Vertimientos ──────────────────────────────────────────────
    vertimiento_total = float(df_vertimientos["vertimiento"].sum())
    print(df_top_vertimientos.head())      
    empresa_vert_max = df_top_vertimientos["nombre_central"].iloc[0]
    vert_empresa_vert_max = df_top_vertimientos["vertimiento"].iloc[0]   

    # ── CMG ───────────────────────────────────────────────────────
    cmg_mes  = df_cmg.groupby("fecha_hora", as_index=False)["CMG_PESO_KWH"].mean()
    cmg_prom = float(cmg_mes["CMG_PESO_KWH"].mean())

    idx_cmg_max      = cmg_mes["CMG_PESO_KWH"].idxmax()
    cmg_max          = float(cmg_mes.loc[idx_cmg_max, "CMG_PESO_KWH"])
    cmg_max_periodo  = str(cmg_mes.loc[idx_cmg_max, "fecha_hora"])

    # ── Spread ────────────────────────────────────────────────────
    idx_spread_min  = df_spread["spread_abs"].idxmax()
    barra_spread_min = df_spread.loc[idx_spread_min, "nombre_cmg"]   

    def _get_spread_barra(nombre_cmg):
        row = df_spread[df_spread["nombre_cmg"] == nombre_cmg]
        return float(row["spread_abs"].iloc[0]) if not row.empty else 0.0

    spread_max_crucero = _get_spread_barra("CRUCERO_______220")
    spread_max_p_montt = _get_spread_barra("P.MONTT_______220")

    # Día de mayor spread por barra (desde detalle horario)
    df_cmg_detalle["fecha_hora"] = pd.to_datetime(df_cmg_detalle["fecha_hora"])
    df_cmg_detalle["es_solar"]   = df_cmg_detalle["fecha_hora"].dt.hour.between(8, 18)
    df_cmg_detalle["fecha"]      = df_cmg_detalle["fecha_hora"].dt.date

    df_spread_diario = (
        df_cmg_detalle
        .groupby(["fecha", "nombre_cmg", "es_solar"], as_index=False)["CMG_PESO_KWH"].mean()
        .pivot_table(index=["fecha", "nombre_cmg"], columns="es_solar", values="CMG_PESO_KWH")
        .rename_axis(columns=None)          # ← elimina el nombre residual del eje
        .reset_index()
        .rename(columns={False: "no_solar", True: "solar"})
    )
    df_spread_diario["spread_dia"] = (df_spread_diario["no_solar"] - df_spread_diario["solar"]).abs()
    df_spread_diario_out= CSV_DIR / "df_spread_diario.csv"
    df_spread_diario.to_csv(df_spread_diario_out, encoding="utf-8", sep= ";")
    print(df_spread_diario.columns)
    print(df_spread_diario.head())
    print(df_spread_diario["nombre_cmg"].unique())

    def _dia_max_spread(nombre_cmg):
        df_b = df_spread_diario[df_spread_diario["nombre_cmg"] == nombre_cmg]
        if df_b.empty:
            return "—"
        return str(df_b.sort_values("spread_dia", ascending=False).iloc[0]["fecha"])

    dia_spread_crucero = _dia_max_spread("CRUCERO_______220")
    dia_spread_p_montt = _dia_max_spread("P.MONTT_______220")


    empresa_vert_max = empresa_vert_max.replace("PFV", "").capitalize()

    kpis = {
        # Vertimientos
        "vert_total_mwh":                         fmt_int(vertimiento_total),
        "vert_total_mwh_clave":                   f"{fmt_int(vertimiento_total)} MWh",
        "empresa_vert_max":                       empresa_vert_max,
        "vert_empresa_vert_max":                  f"{fmt_int(fmt_int(vert_empresa_vert_max))} MWh",
        # CMG
        "cmg_promedio":                           fmt_float(cmg_prom),
        "cmg_promedio_clave":                     f"{fmt_float(cmg_prom)} $/kWh",
        "cmg_max":                                fmt_float(cmg_max),
        "cmg_max_mensual_periodo":                cmg_max_periodo,
        # Spread — nombres alineados con el texto del PPT
        "cmg_spread_max_crucero":                 f"{fmt_float(spread_max_crucero)} $/kWh",
        "cmg_spread_max_p_montt":                 f"{fmt_float(spread_max_p_montt)} $/kWh",
        "dia_cmg_spread_max_periodo_charrua":     dia_spread_crucero,
        "dia_cmg_spread_max_periodo_p_montt":     fmt_float(dia_spread_p_montt),
        "barra_cmg_spread_min":                   barra_spread_min,
        #Perfiles día típico
        "fecha_perfil_1":                         str(fecha_tipica),
        "fecha_perfil_2":                         str(fecha_tipica_comparacion)

    }


    # ==========================================================
    # 4) Inserciones finales de texto
    # ========================================================== 
    fecha_inicio_formateada = fecha_inicio.strftime('%Y-%m')
    fecha_fin_formateada = fecha_fin.strftime('%Y-%m')

    periodo_estudio= f"{fecha_inicio_formateada} → {fecha_fin_formateada}"
    insertar_periodo_estudio(PPT_PATH,periodo_estudio)  
    insertar_texto_con_placeholders(PPT_PATH, kpis)

    # ==========================================================
    # 5) Exportar ppt a pdf para distribución final
    # ========================================================== 

    exportar_ppt_a_pdf(PPT_PATH, PDF_PATH)


if __name__ == "__main__":
    # Fechas originales como string
    fecha_fin = FECHA_ESTUDIO
    # Convertir a datetime
    fecha_fin = pd.to_datetime(fecha_fin)
    fecha_inicio = fecha_fin - pd.DateOffset(months=12)
    fecha_inicio = pd.to_datetime(fecha_inicio)

    # Generar fechas de comparación (un año antes)
    fecha_comparacion_inicio = fecha_inicio - pd.DateOffset(years=1)
    fecha_comparacion_fin = fecha_fin - pd.DateOffset(years=1)

    print("Fecha inicio:", fecha_inicio)
    print("Fecha fin:", fecha_fin)
    print("Fecha comparación inicio:", fecha_comparacion_inicio)
    print("Fecha comparación fin:", fecha_comparacion_fin)


    main(fecha_inicio,fecha_fin, fecha_comparacion_inicio, fecha_comparacion_fin)