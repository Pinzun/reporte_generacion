import pandas as pd
from utils.db_utils import open_connection, close_connection
# Extrae datos de la base de datos
def extract_data_vertimientos(fecha_inicio=None, fecha_fin=None):
    conn, ssh_client, stop_event = open_connection()

    query_total = f"""
            SELECT ver.periodo, SUM(vert.kwh)/1000 AS vertimiento_mwh
            FROM balance.vertimiento AS vert
            JOIN balance.version AS ver ON ver.id_version = vert.idversion
            WHERE periodo BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
            GROUP BY ver.id_version, ver.periodo
            ORDER BY ver.periodo ASC
            ;
         """

    with conn.cursor() as cursor:
        cursor.execute(query_total)
        data_total = cursor.fetchall()  # ya devuelve lista de dicts

    query_max = f"""
        -- Para obtener maximo mensual por hora
        SELECT ver.periodo, hor.cuarto_hora, hor.dia, hor.hora, hor.minuto, MAX(vert.kwh) AS vertimiento_kwh
        FROM balance.vertimiento AS vert
        JOIN balance.hora_mensual AS hor ON hor.id_hora = vert.id_hora
        JOIN balance.version AS ver ON ver.id_version = vert.idversion
        WhERE ver.periodo BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        GROUP BY vert.idversion;"""
    
    with conn.cursor() as cursor:
        cursor.execute(query_max)
        data_max =   cursor.fetchall()  # ya devuelve lista de dicts
    
    close_connection(conn, ssh_client, stop_event)

    return pd.DataFrame(data_total), pd.DataFrame(data_max)

def extract_data_total_vertimientos(batch_size=2400000,fecha_inicio=None, fecha_fin=None):
    conn, ssh_client, stop_event = open_connection()

    query_rows = """SELECT COUNT(*) AS total_rows FROM balance.vertimiento;"""
    with conn.cursor() as cursor:
        cursor.execute(query_rows)
        total_rows = cursor.fetchone()['total_rows']

    print(f"Total de filas en balance.vertimiento: {total_rows}")

    all_data = []

    # Iterar en lotes
    for offset in range(0, total_rows, batch_size):
        query_data = f"""
            SELECT cen.nombre_infotecnica,cen.tecnologia, ver.periodo, hor.cuarto_hora, hor.dia, hor.hora, hor.minuto, vert.kwh
            FROM balance.vertimiento AS vert
            JOIN balance.hora_mensual AS hor ON hor.id_hora = vert.id_hora
            JOIN balance.version AS ver ON ver.id_version = vert.idversion
            JOIN balance.unidad_generacion AS ud ON vert.idUnidadgen = ud.id_unidad_generacion
            JOIN balance.centrales AS cen ON ud.id_central = cen.id_central
            WhERE ver.periodo BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
            LIMIT {batch_size} OFFSET {offset};
        """
        with conn.cursor() as cursor:
            cursor.execute(query_data)
            batch = cursor.fetchall()
            all_data.extend(batch)  # acumula los lotes

        print(f"Lote desde {offset} hasta {offset+batch_size} procesado")

    close_connection(conn, ssh_client, stop_event)

    return pd.DataFrame(all_data)

def extract_data_cmg(fecha_inicio, fecha_fin):
    conn, ssh_client, stop_event = open_connection()

    query_total = f"""
            SELECT *
            FROM balance.cmg_barra
            WHERE nombre_cmg IN (
            'CRUCERO_______220',
            'P.AZUCAR______220',
            'QUILLOTA______220',
            'AJAHUEL_______500',
            'CHARRUA_______500',
            'P.MONTT_______220'
            )
            AND fecha_version BETWEEN '{fecha_inicio}' AND '{fecha_fin}';
         """

    with conn.cursor() as cursor:
        cursor.execute(query_total)
        data_total = cursor.fetchall()  # ya devuelve lista de dicts     
    close_connection(conn, ssh_client, stop_event)
    return pd.DataFrame(data_total)