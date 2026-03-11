from utils.db_utils import open_connection, close_connection
import pandas as pd
import os
from pathlib import Path
from rapidfuzz import process, fuzz
import re


BASE_DIR = Path(__file__).parent
RAW_DIR = BASE_DIR / "data" / "raw"
OTROS_DIR = BASE_DIR / "data" / "processed" / "otros"
ruta_centrales_it= RAW_DIR / "reporte_centrales.xlsx"
ruta_centrales_bd= OTROS_DIR / "centrales_bd.csv"
#Extrae información de centrales desde BD

def extrae_centrales():
    conn, ssh_client, stop_event = open_connection()

    query = f"""
            SELECT id_central,nombre,tecnologia,tipo_central,observacion,id_empresa FROM balance.centrales
            ;
         """

    with conn.cursor() as cursor:
        cursor.execute(query)
        data_total = cursor.fetchall()  # ya devuelve lista de dicts       
    close_connection(conn, ssh_client, stop_event)
    return pd.DataFrame(data_total)

def normalizacion_it(df):
     # Seleccionamos las columnas relevantes
    df = df[['Nombre', 'Nombre Coordinado']]
    return df

def main():
    #Traigo la información de centrales que está en la bd
    if not os.path.exists(ruta_centrales_bd):
        unidades_generadoras_bd = extrae_centrales()
        unidades_generadoras_bd.to_csv(
            ruta_centrales_bd,
            encoding="utf-8",
            index=False,
            sep=";"
        )
    if os.path.exists(ruta_centrales_bd):
        unidades_generadoras_bd=pd.read_csv(ruta_centrales_bd, encoding="utf8", sep=";")

    # Traigo la información del reporte de infotecnica
    unidades_generadoras_it=pd.read_excel(ruta_centrales_it, skiprows=6)
    unidades_generadoras_it=normalizacion_it(unidades_generadoras_it)

    print('Primeras filas de unidades generadoras en bd')
    print(unidades_generadoras_bd.head())
    print('Primeras filas de unidades generadoras infotenica')
    print(unidades_generadoras_it.head())
    print('Valores únicos de tecnologia en bd:')
    print(unidades_generadoras_bd['tecnologia'].unique())
    print('Valores únicos de tipo_central en bd:')
    print(unidades_generadoras_bd['tipo_central'].unique())


    
if __name__ == "__main__":
    main()
