import numpy as np
import pandas as pd
from datetime import datetime

def gx_ver_iny(df_gx_real: pd.DataFrame, df_vertimientos:pd.DataFrame) -> pd.DataFrame:

    # IMPLEMENTACIÓN
    # 1) merge de dfs
    df=pd.merge(df_gx_real, df_vertimientos, how="left", on=["id_central", "id_hora"], suffixes=["gx","vert"] )
    # 2) Mantiene columnas útiles
    columnas_mantener = ["id_hora_gx", "fecha_hora_gx", "inyeccion_retiro_gx", "vertimientos_vert" ,"tipo_gx"]
    df_limpio=df[df[columnas_mantener]].copy()  
    # 3) Limpiar y renombrar columnas
    df_limpio=df_limpio.replace("_gx","")
    df_limpio=df_limpio.replace("_vert","")
    df_limpio["inyeccion"]=df["inyeccion_retiro"]
    # 4)  Limpieza especial fecha_hora
        # Asegurar que es datetime
    if not pd.api.types.is_datetime64_any_dtype(df_limpio["fecha_hora"]):
        df_limpio = pd.to_datetime(df_limpio, errors="coerce")
    # Si la conversión falla, mantener como string
    if pd.notnull(df_limpio):
        df_limpio = df_limpio.strftime("%Y-%m")
    else:
        df_limpio = str(df_limpio.loc[df_limpio, "fecha_hora"])

    df_resultado = df_limpio.groupby("fecha_hora", as_index=False).agg({"inyecciones": "sum",
                                                                        "vertimiento":"sum"})
    return df_resultado


import numpy as np
import pandas as pd
from datetime import datetime

def gx_ver_iny(df_gx_real: pd.DataFrame, df_vertimientos: pd.DataFrame) -> pd.DataFrame:
    # CONSTITUCIÓN
    # Esta función toma el dataframe de gx_real y vertimiento, hace un merge por id_central e id_hora
    # En el merge solo conservar las columnas id_central de gx_real, id_hora de gx_real, fecha_hora de gx_real e inyeccion_retiro de gx_real y vertimiento de vertimientos, tipo de gx_real
    # Luego elimina del df principal valores cuyo tipo sea Bess.
    # a un dato en formato
    # '2025-02'
    # Se limpian columnas y renombra la columna inyeccion_retiro como inyeccion
    # Luego limpia la columna fecha_hora real pasando de un dato en formato:
    # '2025-02-02 00:00:00'
    # Finalmente se calcula un df_resultado a partir de df, haciendo un groupby por fecha_hora_limpio, sumando los valores de la columna inyeccion_retiro 
    # y los valores de la columna vertimiento



    # 1) Merge de dfs
    df = pd.merge(
        df_gx_real,
        df_vertimientos,
        how="left",
        on=["id_central", "id_hora"],
        suffixes=("_gx", "_vert")
    )

    # 2) Mantener columnas útiles 
    columnas_mantener = ["id_hora", "fecha_hora", "inyeccion_retiro", "vertimiento", "tipo_gx"]
    df_limpio = df[columnas_mantener].copy()

    # 3) Renombrar columnas
    df_limpio = df_limpio.rename(columns={
        "id_hora": "id_hora",
        "fecha_hora": "fecha_hora",
        "inyeccion_retiro": "inyeccion",
        "vertimiento": "vertimiento",
        "tipo_gx": "tipo"
    })

    # 4) Eliminar registros tipo Bess
    df_limpio = df_limpio[df_limpio["tipo"] != "Bess"]

    # 5) Limpieza especial fecha_hora → convertir a datetime y luego a formato YYYY-MM
    df_limpio["fecha_hora"] = pd.to_datetime(df_limpio["fecha_hora"], errors="coerce")
    df_limpio["fecha_hora_limpio"] = df_limpio["fecha_hora"].dt.strftime("%Y-%m")

    # 6) Agrupación final
    df_resultado = df_limpio.groupby("fecha_hora_limpio", as_index=False).agg({
        "inyeccion": "sum",
        "vertimiento": "sum"
    })
    # Renombrar fecha_hora_limpio como periodo
    df_resultado = df_resultado.rename(columns={
        "fecha_hora_limpio": "periodo",  
    })


    return df_resultado
