import pandas as pd
from utils.db_utils import open_connection, close_connection


# =========================================================
# Extrae datos de vertimientos
# =========================================================
def extrae_data_total_vertimientos(batch_size=4800000,fecha_inicio=None, fecha_fin=None,fecha_comparacion_inicio=None,fecha_comparacion_fin=None):
    #Extrae datos de estudio
    conn, ssh_client, stop_event = open_connection()

    query_rows = f"""
    SELECT COUNT(*) AS total_rows
    FROM balance.vertimiento AS vert
    JOIN balance.version AS ver ON ver.id_version = vert.id_version
    WHERE ver.periodo BETWEEN '{fecha_inicio}' AND '{fecha_fin}';
            """

    with conn.cursor() as cursor:
        cursor.execute(query_rows)
        total_rows = cursor.fetchone()['total_rows']

    print(f"Total de filas para estudio en balance.vertimiento: {total_rows}")

    data_estudio = []

    # Iterar en lotes
    for offset in range(0, total_rows, batch_size):
        query_data = f"""
        SELECT 
            TRIM(REPLACE(REPLACE(cen.nombre_central, '\r', ' '), '\n', ' ')) AS nombre_central,
            cen.id_central,
            hor.id_hora,
            TRIM(REPLACE(REPLACE(vert.tipo, '\r', ''), '\n', '')) AS tipo,
            ver.periodo,
            hor.cuarto_hora,
            hor.dia,
            hor.hora,
            hor.minuto,
            vert.vertimiento
        FROM balance.vertimiento AS vert
        JOIN balance.hora_mensual AS hor ON hor.id_hora = vert.id_hora
        JOIN balance.version AS ver ON ver.id_version = vert.id_version
        JOIN balance.central AS cen ON vert.id_central = cen.id_central
        WHERE ver.periodo BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
        LIMIT {batch_size} OFFSET {offset};
        """
        with conn.cursor() as cursor:
            cursor.execute(query_data)
            batch = cursor.fetchall()
            data_estudio.extend(batch)  # acumula los lotes

        print(f"Lote desde {offset} hasta {offset+batch_size} procesado")

    close_connection(conn, ssh_client, stop_event)


    #Extrae datos de comparacion
    conn, ssh_client, stop_event = open_connection()

    query_rows = f"""
    SELECT COUNT(*) AS total_rows
    FROM balance.vertimiento AS vert
    JOIN balance.version AS ver ON ver.id_version = vert.id_version
    WHERE ver.periodo BETWEEN '{fecha_comparacion_inicio}' AND '{fecha_comparacion_fin}';
            """

    with conn.cursor() as cursor:
        cursor.execute(query_rows)
        total_rows = cursor.fetchone()['total_rows']

    print(f"Total de filas para comparacion en balance.vertimiento: {total_rows}")

    data_comparacion = []

    # Iterar en lotes
    for offset in range(0, total_rows, batch_size):
        query_data = f"""
        SELECT 
            TRIM(REPLACE(REPLACE(cen.nombre_central, '\r', ' '), '\n', ' ')) AS nombre_central,
            TRIM(REPLACE(REPLACE(vert.tipo, '\r', ''), '\n', '')) AS tipo,
            ver.periodo,
            hor.cuarto_hora,
            hor.dia,
            hor.hora,
            hor.minuto,
            vert.vertimiento
        FROM balance.vertimiento AS vert
        JOIN balance.hora_mensual AS hor ON hor.id_hora = vert.id_hora
        JOIN balance.version AS ver ON ver.id_version = vert.id_version
        JOIN balance.central AS cen ON vert.id_central = cen.id_central
        WHERE ver.periodo BETWEEN '{fecha_comparacion_inicio}' AND '{fecha_comparacion_fin}'
        LIMIT {batch_size} OFFSET {offset};
        """
        with conn.cursor() as cursor:
            cursor.execute(query_data)
            batch = cursor.fetchall()
            data_comparacion.extend(batch)  # acumula los lotes

        print(f"Lote desde {offset} hasta {offset+batch_size} procesado")

    close_connection(conn, ssh_client, stop_event)


    df_vertimientos = pd.DataFrame(data_estudio)
    df_vertimientos_comparacion =pd.DataFrame(data_comparacion)
    return df_vertimientos,df_vertimientos_comparacion



# =========================================================
# Extrae datos de CMG en lotes
# =========================================================

def extrae_data_cmg(batch_size=2400000,
                    fecha_inicio=None, fecha_fin=None,
                    fecha_inicio_comparacion=None, fecha_fin_comparacion=None):
    # -------------------------------
    # Descarga datos periodo de estudio
    # -------------------------------
    conn, ssh_client, stop_event = open_connection()

    filtros_estudio = f"""
        FROM balance.cmg_barra
        WHERE nombre_cmg IN (
            'CRUCERO_______220',
            'AJAHUEL_______500',
            'P.MONTT_______220'
        )
        AND fecha_hora BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    """

    query_rows = f"SELECT COUNT(*) AS total_rows {filtros_estudio};"

    with conn.cursor() as cursor:
        cursor.execute(query_rows)
        total_rows = cursor.fetchone()["total_rows"]

    print(f"Total de filas filtradas en balance.cmg_barra (estudio): {total_rows}")

    data_estudio = []
    for offset in range(0, total_rows, batch_size):
        query_data = f"""
            SELECT *
            {filtros_estudio}
            ORDER BY fecha_hora, nombre_cmg
            LIMIT {batch_size} OFFSET {offset};
        """
        with conn.cursor() as cursor:
            cursor.execute(query_data)
            batch = cursor.fetchall()
            data_estudio.extend(batch)

        print(f"Lote estudio desde {offset} hasta {min(offset + batch_size, total_rows)} procesado")

    close_connection(conn, ssh_client, stop_event)
    df_cmg_all = pd.DataFrame(data_estudio)

    # -------------------------------
    # Descarga datos periodo de comparación
    # -------------------------------
    conn, ssh_client, stop_event = open_connection()

    filtros_comparacion = f"""
        FROM balance.cmg_barra
        WHERE nombre_cmg IN (
            'CRUCERO_______220',
            'AJAHUEL_______500',
            'P.MONTT_______220'
        )
        AND fecha_hora BETWEEN '{fecha_inicio_comparacion}' AND '{fecha_fin_comparacion}'
    """

    query_rows = f"SELECT COUNT(*) AS total_rows {filtros_comparacion};"

    with conn.cursor() as cursor:
        cursor.execute(query_rows)
        total_rows = cursor.fetchone()["total_rows"]

    print(f"Total de filas filtradas en balance.cmg_barra (comparación): {total_rows}")

    data_comparacion = []
    for offset in range(0, total_rows, batch_size):
        query_data = f"""
            SELECT *
            {filtros_comparacion}
            ORDER BY fecha_hora, nombre_cmg
            LIMIT {batch_size} OFFSET {offset};
        """
        with conn.cursor() as cursor:
            cursor.execute(query_data)
            batch = cursor.fetchall()
            data_comparacion.extend(batch)

        print(f"Lote comparación desde {offset} hasta {min(offset + batch_size, total_rows)} procesado")

    close_connection(conn, ssh_client, stop_event)
    df_cmg_all_comparacion = pd.DataFrame(data_comparacion)

    # -------------------------------
    # Retorno de resultados
    # -------------------------------
    return df_cmg_all, df_cmg_all_comparacion



# =========================================================
# Extrae generación real en lotes
# =========================================================
def extrae_gx_real(batch_size=200000, fecha_inicio=None, fecha_fin=None,
                   fecha_inicio_comparacion=None, fecha_fin_comparacion=None):
    """
    Extrae datos de gx_real en dos rangos de fechas:
    - Rango principal (fecha_inicio, fecha_fin)
    - Rango de comparación (fecha_inicio_comparacion, fecha_fin_comparacion)
    Devuelve dos DataFrames.
    """

    def _extraer(conn, fecha_ini, fecha_fin, batch_size):
        last_id = 0
        all_data = []

        while True:
            query = """
            SELECT
                gx.id_generacion,
                cen.id_central,
                gx.id_hora,
                hor.fecha_hora,
                gx.inyeccion_retiro,
                cen.tipo,
                gx.subtipo
            FROM balance.gx_real gx
            JOIN balance.central cen
                ON cen.id_central = gx.id_central
            JOIN balance.hora_mensual hor
                ON hor.id_hora = gx.id_hora
            WHERE hor.fecha_hora BETWEEN %s AND %s
            AND gx.id_generacion > %s
            ORDER BY gx.id_generacion
            LIMIT %s;
            """
            with conn.cursor() as cursor:  # ya es DictCursor por configuración
                cursor.execute(query, (fecha_ini, fecha_fin, last_id, batch_size))
                batch = cursor.fetchall()

            if not batch:
                break

            all_data.extend(batch)
            last_id = batch[-1]["id_generacion"]

            print(f"Procesado gx_real hasta id_generacion {last_id}")

        return pd.DataFrame(all_data)

    # --- Rango principal ---
    conn, ssh_client, stop_event = open_connection()
    gx_real = _extraer(conn, fecha_inicio, fecha_fin, batch_size)
    close_connection(conn, ssh_client, stop_event)

    # --- Rango comparación ---
    conn, ssh_client, stop_event = open_connection()
    gx_real_comparacion = _extraer(conn, fecha_inicio_comparacion, fecha_fin_comparacion, batch_size)
    close_connection(conn, ssh_client, stop_event)

    return gx_real, gx_real_comparacion



def extrae_gx_real_comparacion(batch_size=200000):  
    fecha_inicio = "2022-01-01"
    fecha_fin = "2022-12-31"   # ojo, había un ":" extra en tu string  
    conn, ssh_client, stop_event = open_connection()

    last_id = 0
    all_data = []

    while True:
        query = f"""
        SELECT
            gx.id_generacion,
            cen.id_central,
            gx.id_hora,
            hor.fecha_hora,
            gx.inyeccion_retiro,
            cen.tipo,
            gx.subtipo
        FROM balance.gx_real gx
        JOIN balance.central cen
            ON cen.id_central = gx.id_central
        JOIN balance.hora_mensual hor
            ON hor.id_hora = gx.id_hora
        WHERE hor.fecha_hora BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
          AND gx.id_generacion > {last_id}
        ORDER BY gx.id_generacion
        LIMIT {batch_size};
        """

        with conn.cursor() as cursor:
            cursor.execute(query)
            batch = cursor.fetchall()

        if not batch:
            break

        all_data.extend(batch)
        last_id = batch[-1]["id_generacion"]

        print(f"Procesado gx_real hasta id_generacion {last_id}")

    close_connection(conn, ssh_client, stop_event)

    return pd.DataFrame(all_data)