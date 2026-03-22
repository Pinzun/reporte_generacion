import pandas as pd
import numpy as np
from utils.config_loader import get_config


def spread_cmg(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcula, para cada nombre_cmg:
    - promedio de CMG en horas solares
    - promedio de CMG en horas no solares
    - spread = promedio_solar - promedio_no_solar
    - spread_abs = valor absoluto del spread

    Requiere un df detallado con columna fecha_hora en formato datetime
    o convertible a datetime.

    Columnas esperadas:
    - fecha_hora
    - nombre_cmg
    - CMG_PESO_KWH
    """
    columnas_requeridas = {"fecha_hora", "nombre_cmg", "CMG_PESO_KWH"}
    faltantes = columnas_requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {sorted(faltantes)}")

    df_work = df.copy()

    df_work["fecha_hora"] = pd.to_datetime(df_work["fecha_hora"], errors="coerce")
    df_work["CMG_PESO_KWH"] = pd.to_numeric(df_work["CMG_PESO_KWH"], errors="coerce")

    df_work = df_work.dropna(subset=["fecha_hora", "nombre_cmg", "CMG_PESO_KWH"]).copy()

    if df_work.empty:
        raise ValueError("No hay datos válidos para calcular spread_cmg.")

    df_work["hora"] = df_work["fecha_hora"].dt.hour

    _hs = get_config()["consultas"]["horas_solares"]
    df_work["bloque_horario"] = np.where(
        (df_work["hora"] >= _hs["inicio"]) & (df_work["hora"] < _hs["fin"]),
        "horas_solares",
        "horas_no_solares"
    )

    df_spread = (
        df_work.groupby(["nombre_cmg", "bloque_horario"], as_index=False)["CMG_PESO_KWH"]
        .mean()
        .pivot(index="nombre_cmg", columns="bloque_horario", values="CMG_PESO_KWH")
        .reset_index()
    )

    # Asegurar columnas aunque falte alguna categoría en un caso extremo
    if "horas_solares" not in df_spread.columns:
        df_spread["horas_solares"] = np.nan
    if "horas_no_solares" not in df_spread.columns:
        df_spread["horas_no_solares"] = np.nan

    df_spread["spread"] = df_spread["horas_solares"] - df_spread["horas_no_solares"]
    df_spread["spread_abs"] = df_spread["spread"].abs()

    return df_spread