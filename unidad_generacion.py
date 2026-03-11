from utils.db_utils import open_connection, close_connection
import pandas as pd
import os
from pathlib import Path
from rapidfuzz import process, fuzz
import re


BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"
OTROS_DIR = BASE_DIR / "data" / "processed" / "otros"
ruta_ug_it= RAW_DIR / "reporte_unidades-generadoras.xlsx"
ruta_ug_bd= OTROS_DIR / "unidades_generadoras_bd.csv"
#Extrae información de unidades generadoras desde BD

def extrae_ug():
    conn, ssh_client, stop_event = open_connection()

    query = f"""
            SELECT * FROM balance.unidad_generacion
            ;
         """

    with conn.cursor() as cursor:
        cursor.execute(query)
        data_total = cursor.fetchall()  # ya devuelve lista de dicts       
    close_connection(conn, ssh_client, stop_event)
    return pd.DataFrame(data_total)



import re

import re
import unicodedata

def normalizacion_it(df):
    # Seleccionamos las columnas relevantes
    df = df[['Nombre', '11.1.2 Subestación primaria de conexión (ID_S/E "Nombre")']]
    
    # Renombramos la columna larga
    df = df.rename(columns={
        '11.1.2 Subestación primaria de conexión (ID_S/E "Nombre")': 'subestacion'
    })
    
    # Normalizamos la columna 'subestacion' eliminando el patrón ID..._
    df['subestacion'] = df['subestacion'].apply(
        lambda x: re.sub(r'^ID[_]?\d+_', '', str(x))
    )
    
    # Limpiamos la columna 'Nombre':
    # - Eliminamos "PMGD PFV"
    # - Eliminamos "HP"
    # - Quitamos espacios extra
    df['Nombre'] = (
        df['Nombre']
        .str.replace("PMGD PFV", "", regex=False)
        .str.replace("PMG PFV", "", regex=False)
        .str.replace("PMGD HP", "", regex=False)
        .str.replace("PMG HP", "", regex=False)
        .str.replace("PMGD TER", "", regex=False)
        .str.replace("PMG TER", "", regex=False)
        .str.replace("PMGD HE", "", regex=False)
        .str.replace("PMG HE", "", regex=False)
        .str.replace("HP", "", regex=False)
        .str.replace("PFV", "", regex=False)
        .str.replace("TER", "", regex=False)
        .str.replace("HE", "", regex=False)
        .str.replace(" U", "-", regex=False)
        .str.strip()
    )
    
    return df


def normalizacion_bd(df):
    # Creamos la columna 'nombre_limpio' eliminando todo lo que viene después de "_"
    df['nombre_limpio'] = df['Nombre'].apply(lambda x: str(x).split('_')[0])
    return df

def main():
    #Traigo la información de unidades generadoras que está en la bd
    if not os.path.exists(ruta_ug_bd):
        unidades_generadoras_bd = extrae_ug()
        unidades_generadoras_bd.to_csv(
            ruta_ug_bd,
            encoding="utf-8",
            index=False,
            sep=";"
        )
    if os.path.exists(ruta_ug_bd):
        unidades_generadoras_bd=pd.read_csv(ruta_ug_bd, encoding="utf8", sep=";")

    unidades_generadoras_bd=normalizacion_bd(unidades_generadoras_bd)
    # Traigo la información del reporte de infotecnica
    unidades_generadoras_it=pd.read_excel(ruta_ug_it, skiprows=6)
    unidades_generadoras_it=normalizacion_it(unidades_generadoras_it)

    print('Primeras filas de unidades generadoras en bd')
    print(unidades_generadoras_bd.head())
    print('Primeras filas de unidades generadoras infotenica')
    print(unidades_generadoras_it.head())


    
if __name__ == "__main__":
    main()

