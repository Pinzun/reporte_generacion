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
from utils.graficos import generar_graficas
from utils.exporta_excel import exporta_dfs_to_excel
from utils.calcula_gx_tipico import gx_real_tipico
from utils.calcula_spread_cmg import spread_cmg
from utils.calcula_gx_inyectada_vertida import gx_ver_iny
from utils.calcula_top_vertimiento import top_vertimientos
from utils.inserta_texto_ppt import insertar_periodo_estudio, exportar_ppt_a_pdf
# -----------------------
# Config
# -----------------------

BASE_DIR = Path(__file__).parent
TEMPL_DIR = BASE_DIR / "templates"
ASSETS_DIR = BASE_DIR / "assets"
IMG_DIR = BASE_DIR / "data" / "processed" / "images"
OUT_DIR = BASE_DIR / "data" / "processed" / "reports"
PPT_PATH = OUT_DIR / "reporte_generacion.pptx"
PDF_PATH = OUT_DIR / "reporte_generacion.pdf"

PDF_NAME = "reporte.pdf"
DEV = True 
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
def main(fecha_inicio, fecha_fin, fecha_comparacion_inicio, fecha_comparacion_fin):
    # Crear carpetas
    IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    #rutas de guardado de df del periodo de estudio
    ruta_vertimientos = BASE_DIR / "data" / "raw" / "extraido_db" / "vertimientos.csv"
    ruta_cmg = BASE_DIR / "data" / "raw" / "extraido_db" / "cmg.csv"
    ruta_gx_real = BASE_DIR / "data" / "raw" / "extraido_db" / "gx_real.csv"
    #rutas de guardado de df del periodo de comparacion
    ruta_vertimientos_comparacion = BASE_DIR / "data" / "raw" / "extraido_db" / "vertimientos_comparacion.csv"
    ruta_cmg_comparacion = BASE_DIR / "data" / "raw" / "extraido_db" / "cmg_comparacion.csv"
    ruta_gx_real_comparacion_2022 = BASE_DIR / "data" / "raw" / "extraido_db" / "gx_real_comparacion_2022.csv"
    ruta_gx_real_comparacion = BASE_DIR / "data" / "raw" / "extraido_db" / "gx_real_comparacion.csv"

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
        df_vertimientos.to_csv(ruta_vertimientos, index=False)
        df_vertimientos_comparacion.to_csv(ruta_vertimientos_comparacion, index=False)        
        print("📁 CSV vertimiento Guardado para futuras ejecuciones DEV.")      

        df_cmg_all,df_cmg_all_comparacion = extrae_data_cmg(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            fecha_inicio_comparacion=fecha_comparacion_inicio,
            fecha_fin_comparacion=fecha_comparacion_fin
        )

        df_cmg_all.to_csv(ruta_cmg, index=False)
        df_cmg_all_comparacion.to_csv(ruta_cmg_comparacion, index=False)  
        print("📁 CSV cmg Guardado para futuras ejecuciones DEV.")

        df_gx_real,df_gx_real_comparacion=extrae_gx_real(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
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
            date_format="%Y-%m-%d %H:%M:%S"
        )
        df_gx_real_comparacion.to_csv(
            ruta_gx_real_comparacion,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S"
        )  

        df_gx_real_comparacion_2022.to_csv(
            ruta_gx_real_comparacion_2022,
            index=False,
            date_format="%Y-%m-%d %H:%M:%S"
        )  

        print("📁 CSV guardados para futuras ejecuciones DEV.")

    # =========================
    # 1) Limpieza
    # =========================
    df_vertimientos = limpiar_outliers(df_vertimientos)
    df_max_acum = tabla_maximos_acumulados_por_periodo(df_vertimientos)
    #Truncamos el dato fecha_hora
    df_cmg_all['fecha_hora']=pd.to_datetime(df_cmg_all['fecha_hora'])
    df_cmg_detalle=df_cmg_all.copy()
    df_cmg_all['fecha_hora'] = df_cmg_all['fecha_hora'].dt.strftime('%Y-%m')

    df_cmg = (
        df_cmg_all.groupby(["fecha_hora", "nombre_cmg"], as_index=False)
        .agg({"CMG_PESO_KWH": "mean"})
    )   

    # =========================
    # 1.1) Generación real día típico
    # =========================
    df_gx_real_tipico=gx_real_tipico(df_gx_real)
    print("Fecha típica:", df_gx_real_tipico["fecha_tipica"])
    df_dia_tipico = df_gx_real_tipico["df_dia_tipico"]

    # =========================
    # 1.1.2) Generación real día típico comparacion
    # =========================
    df_gx_real_tipico_comparacion=gx_real_tipico(df_gx_real_comparacion_2022)
    print("Fecha típica:", df_gx_real_tipico_comparacion["fecha_tipica"])
    df_dia_tipico_comparacion = df_gx_real_tipico_comparacion["df_dia_tipico"]
   
    
    # =========================
    # 1.2) Spread CMG
    # =========================
    df_spread=spread_cmg(df_cmg_detalle) 

    # =========================
    # 1.3) Generación inyectada vs real
    # =========================
    df_gx_ver_iny=gx_ver_iny(df_gx_real,df_vertimientos)

    # =========================
    # 1.4) Top vertimientos
    # =========================
    df_top_vertimientos=top_vertimientos(df_vertimientos)

    # =========================
    # 2) Exportar a excel intermedio
    # =========================
    dfs_exportar=[
    df_vertimientos,
    df_vertimientos_comparacion,
    df_spread,
    df_cmg,
    df_cmg_all_comparacion,
    df_dia_tipico,
    df_gx_ver_iny,
    df_top_vertimientos]



    '''
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
    df_gx_ver_iny=df_gx_ver_iny,
    df_top_vertimiento=df_top_vertimientos,
    ppt_path= PPT_PATH,
    outdir=str(IMG_DIR),
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

    #vert_total = float(df_vertimientos_totales["vertimiento"].sum())
    #vert_prom = float(df_vertimientos_totales["vertimiento"].mean())
    #idx_max = df_vertimientos_totales["vertimiento"].idxmax()
    vert_total = float(df_vertimientos["vertimiento"].sum())
    vert_prom = float(df_vertimientos["vertimiento"].mean())

    idx_vert_max = df_vertimientos["vertimiento"].idxmax()
    vert_max = float(df_vertimientos.loc[idx_vert_max, "vertimiento"])
    vert_max_periodo = str(df_vertimientos.loc[idx_vert_max, "periodo"])

    # fila con mayor vertimiento acumulado
    idx_empresa_max = df_max_acum["vertimiento_acumulado_kwh"].idxmax()
    empresa_vert_max = df_max_acum.loc[idx_empresa_max, "nombre_central"]

    periodo_empresa_max = df_max_acum.loc[idx_empresa_max, "periodo"]

    # Asegurar que es datetime
    if not pd.api.types.is_datetime64_any_dtype(df_max_acum["periodo"]):
        periodo_empresa_max = pd.to_datetime(periodo_empresa_max, errors="coerce")

    # Si la conversión falla, mantener como string
    if pd.notnull(periodo_empresa_max):
        periodo_empresa_max = periodo_empresa_max.strftime("%Y-%m")
    else:
        periodo_empresa_max = str(df_max_acum.loc[idx_empresa_max, "periodo"])

    vert_empresa_vert_max = float(df_max_acum.loc[idx_empresa_max, "vertimiento_acumulado_kwh"])



    cmg_mes = df_cmg.groupby("fecha_hora", as_index=False)["CMG_PESO_KWH"].mean()
    cmg_prom = float(cmg_mes["CMG_PESO_KWH"].mean())

    idx_cmg_max = cmg_mes["CMG_PESO_KWH"].idxmax()
    cmg_max = float(cmg_mes.loc[idx_cmg_max, "CMG_PESO_KWH"])

    try:
        cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_hora"].date())
    except:
        cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_hora"])

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
    '''

    # ==========================================================
    # 4) Inserciones finales de texto
    # ========================================================== 
    fecha_inicio_formateada=pd.to_datatime(fecha_inicio)
    fecha_fin_formateada=pd.to_datatime(fecha_fin)
    fecha_inicio_formateada = fecha_inicio_formateada.dt.strftime('%Y-%m')
    fecha_fin_formateada = fecha_fin_formateada.dt.strftime('%Y-%m')

    periodo_estudio= f"{fecha_inicio_formateada} → {fecha_fin_formateada}"
    insertar_periodo_estudio(PPT_PATH,periodo_estudio)   



    # ==========================================================
    # 5) Exportar ppt a pdf para distribución final
    # ========================================================== 

    exportar_ppt_a_pdf(PPT_PATH, PDF_PATH)


if __name__ == "__main__":
    # Fechas originales como string
    fecha_inicio = "2025-01-01 00:00:00"
    fecha_fin = "2025-12-31 23:45:00"   # ojo, había un ":" extra en tu string

    # Convertir a datetime
    fecha_inicio = pd.to_datetime(fecha_inicio)
    fecha_fin = pd.to_datetime(fecha_fin)

    # Generar fechas de comparación (un año antes)
    fecha_comparacion_inicio = fecha_inicio - pd.DateOffset(years=1)
    fecha_comparacion_fin = fecha_fin - pd.DateOffset(years=1)

    print("Fecha inicio:", fecha_inicio)
    print("Fecha fin:", fecha_fin)
    print("Fecha comparación inicio:", fecha_comparacion_inicio)
    print("Fecha comparación fin:", fecha_comparacion_fin)


    main(fecha_inicio,fecha_fin, fecha_comparacion_inicio, fecha_comparacion_fin)