# main.py
from __future__ import annotations

from pathlib import Path
import pandas as pd

from utils.config_loader import get_config
from utils.extrae_data import (
    extrae_data_total_vertimientos,
    extrae_data_cmg,
    extrae_gx_real,
    extrae_gx_real_comparacion,
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

DEV           = _cfg["reporte"]["dev_mode"]
FECHA_ESTUDIO = _cfg["reporte"]["fecha_estudio"]


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

def limpiar_outliers(df: pd.DataFrame) -> pd.DataFrame:
    """Elimina registros con vertimiento = 0."""
    df_clean = df[df["vertimiento"] != 0].copy()
    print(f"Se eliminaron {len(df) - len(df_clean)} registros con vertimiento = 0")
    return df_clean

def _limpiar_strings_vertimientos(df: pd.DataFrame) -> pd.DataFrame:
    for col in ["tipo", "nombre_central"]:
        if col in df.columns:
            sep = "" if col == "tipo" else " "
            df[col] = df[col].astype(str).str.replace(r"[\r\n]+", sep, regex=True).str.strip()
    return df


# -----------------------
# Main
# -----------------------

def main(fecha_fin: pd.Timestamp):

    IMG_DIR.mkdir(parents=True, exist_ok=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    shutil.copy(TEMPL_DIR / "template_reporte.pptx", PPT_PATH)

    # -----------------------
    # Rutas CSV
    # -----------------------
    ruta_vertimientos             = BASE_DIR / "data" / "raw" / "db" / "vertimientos.csv"
    ruta_vertimientos_comparacion = BASE_DIR / "data" / "raw" / "db" / "vertimientos_comparacion.csv"
    ruta_vertimientos_trim        = BASE_DIR / "data" / "raw" / "db" / "vertimientos_trim.csv"
    ruta_vertimientos_trim_comp   = BASE_DIR / "data" / "raw" / "db" / "vertimientos_trim_comparacion.csv"
    ruta_cmg                      = BASE_DIR / "data" / "raw" / "db" / "cmg.csv"
    ruta_cmg_comparacion          = BASE_DIR / "data" / "raw" / "db" / "cmg_comparacion.csv"
    ruta_gx_real_trim             = BASE_DIR / "data" / "raw" / "db" / "gx_real_trim.csv"
    ruta_gx_real_trim_comparacion = BASE_DIR / "data" / "raw" / "db" / "gx_real_trim_comparacion.csv"
    ruta_gx_real_comparacion_2022 = BASE_DIR / "data" / "raw" / "db" / "gx_real_comparacion_2022.csv"

    # =========================
    # 1) Obtener datos
    # =========================
    if DEV:
        print("🔧 Modo desarrollo: cargando CSV locales...")

        df_vertimientos             = pd.read_csv(ruta_vertimientos,             encoding="utf-8", sep=";")
        df_vertimientos_comparacion = pd.read_csv(ruta_vertimientos_comparacion, encoding="utf-8", sep=";")
        df_vertimientos_trim        = pd.read_csv(ruta_vertimientos_trim,        encoding="utf-8", sep=";")
        df_vertimientos_trim_comp   = pd.read_csv(ruta_vertimientos_trim_comp,   encoding="utf-8", sep=";")
        df_cmg_all                  = pd.read_csv(ruta_cmg,                     encoding="utf-8", sep=";")
        df_cmg_all_comparacion      = pd.read_csv(ruta_cmg_comparacion,         encoding="utf-8", sep=";")
        df_gx_real_trim             = pd.read_csv(ruta_gx_real_trim,            encoding="utf-8", sep=";")
        df_gx_real_trim_comparacion = pd.read_csv(ruta_gx_real_trim_comparacion,encoding="utf-8", sep=";")
        df_gx_real_comparacion_2022 = pd.read_csv(ruta_gx_real_comparacion_2022,encoding="utf-8", sep=";")

        df_gx_real = df_gx_real_trim[
            (df_gx_real_trim["anio"].astype(int) == fecha_fin.year) &
            (df_gx_real_trim["mes"].astype(int)  == fecha_fin.month)
        ].copy()

        df_gx_real_comparacion = df_gx_real_trim_comparacion[
            (df_gx_real_trim_comparacion["anio"].astype(int) == fecha_fin.year - 1) &
            (df_gx_real_trim_comparacion["mes"].astype(int)  == fecha_fin.month)
        ].copy()

    else:
        print("🗄️  Modo producción: extrayendo desde base de datos...")

        df_vertimientos, df_vertimientos_comparacion = extrae_data_total_vertimientos(
            fecha_fin=fecha_fin
        )
        df_vertimientos.to_csv(ruta_vertimientos,            index=False, encoding="utf-8", sep=";")
        df_vertimientos_comparacion.to_csv(ruta_vertimientos_comparacion, index=False, encoding="utf-8", sep=";")
        print("📁 CSV vertimientos guardados.")

        df_vertimientos_trim      = df_vertimientos.copy()
        df_vertimientos_trim_comp = df_vertimientos_comparacion.copy()
        df_vertimientos_trim.to_csv(ruta_vertimientos_trim,     index=False, encoding="utf-8", sep=";")
        df_vertimientos_trim_comp.to_csv(ruta_vertimientos_trim_comp, index=False, encoding="utf-8", sep=";")

        df_cmg_all, df_cmg_all_comparacion = extrae_data_cmg(fecha_fin=fecha_fin)
        df_cmg_all.to_csv(ruta_cmg,                index=False, encoding="utf-8", sep=";")
        df_cmg_all_comparacion.to_csv(ruta_cmg_comparacion, index=False, encoding="utf-8", sep=";")
        print("📁 CSV CMg guardados.")

        df_gx_real_trim, df_gx_real_trim_comparacion = extrae_gx_real(fecha_fin=fecha_fin)

        df_gx_real = df_gx_real_trim[
            (df_gx_real_trim["anio"] == fecha_fin.year) &
            (df_gx_real_trim["mes"]  == fecha_fin.month)
        ].copy()

        df_gx_real_comparacion = df_gx_real_trim_comparacion[
            (df_gx_real_trim_comparacion["anio"] == fecha_fin.year - 1) &
            (df_gx_real_trim_comparacion["mes"]  == fecha_fin.month)
        ].copy()

        df_gx_real_trim.to_csv(ruta_gx_real_trim,            index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        df_gx_real_trim_comparacion.to_csv(ruta_gx_real_trim_comparacion, index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        print("📁 CSV GX real guardados.")

        df_gx_real_comparacion_2022 = extrae_gx_real_comparacion(mes=fecha_fin.month)
        df_gx_real_comparacion_2022.to_csv(ruta_gx_real_comparacion_2022, index=False, date_format="%Y-%m-%d %H:%M:%S", encoding="utf-8", sep=";")
        print("📁 CSV GX real comparación 2022 guardado.")

    # =========================
    # 2) Limpieza
    # =========================

    for _df in [df_vertimientos, df_vertimientos_comparacion,
                df_vertimientos_trim, df_vertimientos_trim_comp]:
        _limpiar_strings_vertimientos(_df)

    df_vertimientos             = limpiar_outliers(df_vertimientos)
    df_vertimientos_comparacion = limpiar_outliers(df_vertimientos_comparacion)
    df_vertimientos_trim        = limpiar_outliers(df_vertimientos_trim)
    df_vertimientos_trim_comp   = limpiar_outliers(df_vertimientos_trim_comp)

    # CMg — convertir fechas y guardar copia horaria ANTES de truncar
    df_cmg_all["fecha_hora"]             = pd.to_datetime(df_cmg_all["fecha_hora"])
    df_cmg_all_comparacion["fecha_hora"] = pd.to_datetime(df_cmg_all_comparacion["fecha_hora"])

    df_cmg_detalle      = df_cmg_all.copy()              # estudio horario — para spread y mapa
    df_cmg_detalle_comp = df_cmg_all_comparacion.copy()  # comparación horaria — para mapa

    # Truncar a mes para agregados y KPIs
    df_cmg_all["fecha_hora"]             = df_cmg_all["fecha_hora"].dt.strftime("%Y-%m")
    df_cmg_all_comparacion["fecha_hora"] = df_cmg_all_comparacion["fecha_hora"].dt.strftime("%Y-%m")

    df_cmg = (
        df_cmg_all
        .groupby(["fecha_hora", "nombre_cmg"], as_index=False)
        .agg({"CMG_DOLAR_MWH": "mean"})
    )
    df_cmg.to_csv(CSV_DIR / "df_cmg.csv", encoding="utf-8", sep=";")

    # =========================
    # 3) Cálculos intermedios
    # =========================

    df_gx_real_tipico         = gx_real_tipico(df_gx_real)
    fecha_tipica              = df_gx_real_tipico["fecha_tipica"]
    df_dia_tipico             = df_gx_real_tipico["df_dia_tipico"]
    print("Fecha típica:", fecha_tipica)

    df_gx_real_tipico_comp    = gx_real_tipico(df_gx_real_comparacion_2022)
    fecha_tipica_comparacion  = df_gx_real_tipico_comp["fecha_tipica"]
    df_dia_tipico_comparacion = df_gx_real_tipico_comp["df_dia_tipico"]
    print("Fecha típica comparación:", fecha_tipica_comparacion)

    df_spread = spread_cmg(df_cmg_detalle)
    df_spread.to_csv(CSV_DIR / "df_spread.csv", encoding="utf-8", sep=";")

    df_gx_ver_iny = gx_ver_iny(
        pd.concat([df_gx_real_trim, df_gx_real_trim_comparacion], ignore_index=True),
        pd.concat([df_vertimientos, df_vertimientos_comparacion],  ignore_index=True),
    )

    df_top_vertimientos = top_vertimientos(df_vertimientos)

    # =========================
    # 4) Generar gráficos
    # =========================

    
    generar_graficas(
        df_vertimientos=df_vertimientos,
        df_vertimientos_comparacion=df_vertimientos_comparacion,
        df_vertimientos_trim=df_vertimientos_trim,
        df_vertimientos_trim_comparacion=df_vertimientos_trim_comp,
        df_spread=df_spread,
        df_cmg=df_cmg,
        df_cmg_raw=df_cmg_detalle,              # ← estudio horario
        df_cmg_comparacion=df_cmg_detalle_comp, # ← comparación horaria
        df_dia_tipico=df_dia_tipico,
        df_dia_tipico_comparacion=df_dia_tipico_comparacion,
        fecha_tipica=fecha_tipica,
        fecha_tipica_comparacion=fecha_tipica_comparacion,
        gx_real=df_gx_real,
        gx_real_comparacion=df_gx_real_comparacion,
        df_gx_real_trim=df_gx_real_trim,
        df_gx_real_trim_comparacion=df_gx_real_trim_comparacion,
        df_gx_ver_iny=df_gx_ver_iny,
        df_top_vertimiento=df_top_vertimientos,
        mes_reporte=fecha_fin.month,
        anio_reporte=fecha_fin.year,
        ppt_path=PPT_PATH,
        outdir=str(IMG_DIR),
    )

    # =========================
    # 5) KPIs
    # =========================

    vertimiento_total     = float(df_vertimientos["vertimiento"].sum())
    empresa_vert_max      = df_top_vertimientos["Nombre central"].iloc[0]
    vert_empresa_vert_max = df_top_vertimientos["Reducción renovable"].iloc[0]

    cmg_mes     = df_cmg.groupby("fecha_hora", as_index=False)["CMG_DOLAR_MWH"].mean()
    cmg_prom    = float(cmg_mes["CMG_DOLAR_MWH"].mean())
    idx_cmg_max = cmg_mes["CMG_DOLAR_MWH"].idxmax()
    cmg_max         = float(cmg_mes.loc[idx_cmg_max, "CMG_DOLAR_MWH"])
    cmg_max_periodo = str(cmg_mes.loc[idx_cmg_max, "fecha_hora"])

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
        .groupby(["fecha", "nombre_cmg", "es_solar"], as_index=False)["CMG_DOLAR_MWH"].mean()
        .pivot_table(index=["fecha", "nombre_cmg"], columns="es_solar", values="CMG_DOLAR_MWH")
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
        "vert_total_mwh":                       fmt_int(vertimiento_total),
        "vert_total_mwh_clave":                 f"{fmt_int(vertimiento_total)} MWh",
        "empresa_vert_max":                     empresa_vert_max,
        "vert_empresa_vert_max":                f"{fmt_int(vert_empresa_vert_max)} MWh",
        "cmg_promedio":                         fmt_float(cmg_prom),
        "cmg_promedio_clave":                   f"{fmt_float(cmg_prom)} $/kWh",
        "cmg_max":                              fmt_float(cmg_max),
        "cmg_max_mensual_periodo":              cmg_max_periodo,
        "cmg_spread_max_crucero":               f"{fmt_float(spread_max_crucero)} $/kWh",
        "cmg_spread_max_p_montt":               f"{fmt_float(spread_max_p_montt)} $/kWh",
        "dia_cmg_spread_max_periodo_charrua":   dia_spread_crucero,
        "dia_cmg_spread_max_periodo_p_montt":   fmt_float(dia_spread_p_montt),
        "barra_cmg_spread_min":                 barra_spread_min,
        "fecha_perfil_1":                       str(fecha_tipica),
        "fecha_perfil_2":                       str(fecha_tipica_comparacion),
        "fecha_referencia_1":                   str(fecha_tipica),
        "fecha_referencia_2":                   str(fecha_tipica_comparacion),
    }

    # =========================
    # 6) Inserciones texto PPT
    # =========================
    periodo_estudio = f"{fecha_fin.year}-01"
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
    _cfg      = get_config()
    fecha_fin = pd.to_datetime(FECHA_ESTUDIO, format="%Y-%m")

    print(f"Fecha estudio: {fecha_fin:%Y-%m}")
    print(f"Estudio:     {fecha_fin.year}-01 → {fecha_fin:%Y-%m}")
    print(f"Comparación: {fecha_fin.year - 1}-01 → {fecha_fin.year - 1}-12")

    main(fecha_fin=fecha_fin)