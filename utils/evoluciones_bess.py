import numpy as np
import pandas as pd

def evolucion_inyeccion_bess(df_gx_real: pd.DataFrame, df_gx_real_comparacion: pd.DataFrame) -> pd.DataFrame:

    def _calcular_trimestral(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        mask = (
            df["tipo"].astype(str).str.strip().str.lower().eq("bess") &
            df["subtipo"].astype(str).str.strip().str.contains("inye", case=False, na=False)
        )
        df = df[mask].copy()

        if df.empty:
            return pd.DataFrame(columns=["trimestre", "inyeccion_retiro", "anio"])

        df["fecha_hora"] = pd.to_datetime(df["fecha_hora"], errors="coerce")
        df["trimestre"]  = df["fecha_hora"].dt.to_period("Q").astype(str)
        df["anio"]       = df["fecha_hora"].dt.year.astype(str)  # ← año extraído del DF

        return (
            df.groupby(["trimestre", "anio"], as_index=False)["inyeccion_retiro"]
            .sum()
        )

    df_estudio     = _calcular_trimestral(df_gx_real)
    df_comparacion = _calcular_trimestral(df_gx_real_comparacion)

    return pd.concat([df_estudio, df_comparacion], ignore_index=True)