import numpy as np
import pandas as pd


def gx_real_tipico(df: pd.DataFrame):
    """
    Calcula un día típico real usando distancia a la curva media
    normalizada por desviación estándar.

    Espera columnas:
    - fecha_hora
    - inyeccion_retiro
    - tipo
    - subtipo
    Idealmente también:
    - hora
    - minuto
    - cuarto_hora
    """
    columnas_requeridas = {"fecha_hora", "inyeccion_retiro", "tipo", "subtipo"}
    faltantes = columnas_requeridas - set(df.columns)
    if faltantes:
        raise ValueError(f"Faltan columnas requeridas: {sorted(faltantes)}")

    if df.empty:
        raise ValueError("El DataFrame de entrada está vacío.")

    df_work = df.copy()

    df_work["fecha_hora"] = pd.to_datetime(df_work["fecha_hora"], errors="coerce")
    df_work["inyeccion_retiro"] = pd.to_numeric(df_work["inyeccion_retiro"], errors="coerce")
    df_work = df_work.dropna(subset=["fecha_hora", "inyeccion_retiro", "tipo", "subtipo"]).copy()

    if df_work.empty:
        raise ValueError("No quedaron datos válidos tras limpiar.")

    df_work["tipo"] = df_work["tipo"].astype(str).str.strip()
    df_work["subtipo"] = df_work["subtipo"].astype(str).str.strip()

    df_work["fecha"] = df_work["fecha_hora"].dt.date

    # Usa hora/minuto explícitos si existen
    if {"hora", "minuto"}.issubset(df_work.columns):
        df_work["hora"] = pd.to_numeric(df_work["hora"], errors="coerce").fillna(0)
        df_work["minuto"] = pd.to_numeric(df_work["minuto"], errors="coerce").fillna(0)
    else:
        df_work["hora"] = df_work["fecha_hora"].dt.hour
        df_work["minuto"] = df_work["fecha_hora"].dt.minute

    df_work["hora_decimal"] = df_work["hora"] + df_work["minuto"] / 60.0
    df_work["tipo_subtipo"] = df_work["tipo"] + " | " + df_work["subtipo"]

    # Curvas diarias por combinación tipo-subtipo-hora
    df_agg = (
        df_work.groupby(
            ["fecha", "hora_decimal", "tipo_subtipo"],
            as_index=False
        )["inyeccion_retiro"]
        .sum()
    )

    matriz = df_agg.pivot_table(
        index="fecha",
        columns=["tipo_subtipo", "hora_decimal"],
        values="inyeccion_retiro",
        aggfunc="sum",
        fill_value=0.0
    )

    if matriz.empty:
        raise ValueError("No fue posible construir la matriz diaria.")

    matriz = matriz.sort_index(axis=1)

    media = matriz.mean(axis=0)
    std = matriz.std(axis=0, ddof=0)
    std_safe = std.replace(0, 1.0)

    z = (matriz - media) / std_safe
    distancias = (z ** 2).mean(axis=1)

    fecha_tipica = distancias.idxmin()

    df_dia_tipico = df_work[df_work["fecha"] == fecha_tipica].copy()
    df_dia_tipico = df_dia_tipico.sort_values(
        ["hora", "minuto", "tipo", "subtipo"]
    ).reset_index(drop=True)

    curva_media = media.reset_index()
    curva_media.columns = ["tipo_subtipo", "hora_decimal", "inyeccion_retiro_promedio"]

    tipo_sub_split = curva_media["tipo_subtipo"].str.split(" | ", n=1, expand=True)
    curva_media["tipo"] = tipo_sub_split[0]
    curva_media["subtipo"] = tipo_sub_split[1]

    curva_media = curva_media[
        ["tipo", "subtipo", "hora_decimal", "inyeccion_retiro_promedio"]
    ].sort_values(["tipo", "subtipo", "hora_decimal"]).reset_index(drop=True)

    df_distancias = distancias.reset_index()
    df_distancias.columns = ["fecha", "distancia_tipicidad"]
    df_distancias = df_distancias.sort_values("distancia_tipicidad").reset_index(drop=True)

    return {
        "fecha_tipica": fecha_tipica,
        "df_dia_tipico": df_dia_tipico,
        "distancias": df_distancias,
        "curva_media": curva_media,
        "matriz_diaria": matriz,
    }