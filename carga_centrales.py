from utils.db_utils import open_connection, close_connection
from pathlib import Path
import pandas as pd

# Archivo para cargar datos de centrales 
DATA_PROCESSED = Path(__file__).parent / 'data' / 'processed'
CENTRALES_CSV = DATA_PROCESSED / 'carga_centrales.csv'

# Importa dataframe de centrales para cargar a la base de datos
def load_centrales():
    df_centrales = pd.read_csv(CENTRALES_CSV)
    return df_centrales

# Query para cargar los datos
def cargar_centrales(df_centrales):
    conn, ssh_client, stop_event = open_connection()
    cursor = conn.cursor()

    query = '''
        UPDATE balance.centrales
        SET
            id_infotecnica = %s,
            nombre_infotecnica = %s,
            nombre_propietario = %s,
            comuna = %s,
            tipo_central = %s,
            nemotecnico = %s,
            estado = %s,
            n_unidades_generadoras = %s,
            punto_conexion_sen = %s,
            capacidad_maxima_mw = %s,
            fecha_entrada_operacion = %s,
            tipo_conversion_energia = %s,
            combustible = %s,
            tipo_tecnologia = %s,
            segmento_generacion = %s,
            cut_comuna = %s
        WHERE id_central = %s;
    '''

    for _, row in df_centrales.iterrows():
        cursor.execute(query, (
            None if pd.isna(row['id_infotecnica']) else row['id_infotecnica'],
            None if pd.isna(row['nombre_infotecnica']) else row['nombre_infotecnica'],
            None if pd.isna(row['nombre_propietario']) else row['nombre_propietario'],
            None if pd.isna(row['comuna']) else row['comuna'],
            None if pd.isna(row['tipo_central']) else row['tipo_central'],
            None if pd.isna(row['nemotecnico']) else row['nemotecnico'],
            None if pd.isna(row['estado']) else row['estado'],
            None if pd.isna(row['n_unidades_generadoras']) else float(row['n_unidades_generadoras']),
            None if pd.isna(row['punto_conexion_sen']) else row['punto_conexion_sen'],
            None if pd.isna(row['capacidad_maxima_mw']) else str(row['capacidad_maxima_mw']),  # ahora texto
            None if pd.isna(row['fecha_entrada_operacion']) else row['fecha_entrada_operacion'],
            None if pd.isna(row['tipo_conversion_energia']) else row['tipo_conversion_energia'],
            None if pd.isna(row['combustible']) else row['combustible'],
            None if pd.isna(row['tipo_tecnologia']) else row['tipo_tecnologia'],
            None if pd.isna(row['segmento_generacion']) else row['segmento_generacion'],
            None if pd.isna(row['cut_comuna']) else int(row['cut_comuna']),
            row['id_central']  # condición del WHERE
        ))


    conn.commit()
    cursor.close()
    close_connection(conn, ssh_client, stop_event)
    print("Datos actualizados exitosamente en la tabla 'centrales'")

if __name__ == "__main__":
    df_centrales = load_centrales()

    # Normalizar fechas
    df_centrales['fecha_entrada_operacion'] = pd.to_datetime(
        df_centrales['fecha_entrada_operacion'],
        format='%d-%m-%Y',
        errors='coerce'
    ).dt.strftime('%Y-%m-%d')

    # Convertir n_unidades_generadoras a numérico
    df_centrales['n_unidades_generadoras'] = pd.to_numeric(
        df_centrales['n_unidades_generadoras'],
        errors='coerce'
    )

    # Convertir cut_comuna a numérico
    df_centrales['cut_comuna'] = pd.to_numeric(
        df_centrales['cut_comuna'],
        errors='coerce'
    )

    # Reemplazar todos los NaN por None
    df_centrales = df_centrales.where(pd.notnull(df_centrales), None)

    cargar_centrales(df_centrales)

