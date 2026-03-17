import numpy as np
import pandas as pd

def top_vertimientos(df_vertimientos: pd.DataFrame, top=10, agrupar_por_periodo=False) -> pd.DataFrame:
    """
    Calcula el vertimiento total por central (y opcionalmente por periodo) 
    y devuelve el top N de los que más han vertido.
    """
    # Definir columnas de agrupación
    if agrupar_por_periodo:
        cols_group = ["periodo", "nombre_central", "tipo"]
    else:
        cols_group = ["nombre_central", "tipo"]

    # Agrupar y sumar
    df_top = (
        df_vertimientos.groupby(cols_group, as_index=False)
        .agg({"vertimiento": "sum"})
    )

    # Ordenar y seleccionar top N
    df_top = df_top.sort_values("vertimiento", ascending=False).head(top)
    df_top["nombre_central"] = df_top["nombre_central"].str.title()
    df_top["tipo"] = df_top["tipo"].str.title()

    return df_top
