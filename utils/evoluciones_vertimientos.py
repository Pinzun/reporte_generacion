import numpy as np
import pandas as pd

def evolucion_vertimiento(df_vertimientos: pd.DataFrame, df_vertimientos_comparacion: pd.DataFrame) -> pd.DataFrame:

    def _calcular_trimestral(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        if df.empty:
            return pd.DataFrame(columns=["trimestre", "vertimiento", "anio"])

        df["periodo"]   = pd.to_datetime(df["periodo"], errors="coerce")
        df["trimestre"] = df["periodo"].dt.to_period("Q").astype(str)
        df["anio"]      = df["periodo"].dt.year.astype(str)

        return (
            df.groupby(["trimestre", "anio"], as_index=False)["vertimiento"]
            .sum()
        )

    df_estudio     = _calcular_trimestral(df_vertimientos)
    df_comparacion = _calcular_trimestral(df_vertimientos_comparacion)

    return pd.concat([df_estudio, df_comparacion], ignore_index=True)