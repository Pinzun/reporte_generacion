import pandas as pd
from utils.db_utils import open_connection, close_connection


# =========================================================
# Extrae datos de vertimientos
# =========================================================
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


# =========================================================
# Extrae vertimientos detallados en lotes
# =========================================================
def extrae_data_total_vertimientos(batch_size=2400000, fecha_inicio=None, fecha_fin=None):
    conn, ssh_client, stop_event = open_connection()

    filtros = f"""
        FROM balance.vertimiento AS vert
        JOIN balance.hora_mensual AS hor 
            ON hor.id_hora = vert.id_hora
        JOIN balance.version AS ver 
            ON ver.id_version = vert.id_version
        JOIN balance.central AS cen 
            ON vert.id_central = cen.id_central
        WHERE ver.periodo BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    """

    query_rows = f"""
        SELECT COUNT(*) AS total_rows
        {filtros};
    """

    with conn.cursor() as cursor:
        cursor.execute(query_rows)
        total_rows = cursor.fetchone()["total_rows"]

    print(f"Total de filas filtradas en balance.vertimiento: {total_rows}")

    all_data = []

    for offset in range(0, total_rows, batch_size):
        query_data = f"""
            SELECT
                cen.nombre_central,
                cen.tipo,
                ver.periodo,
                hor.cuarto_hora,
                hor.dia,
                hor.hora,
                hor.minuto,
                vert.vertimiento
            {filtros}
            ORDER BY ver.periodo, hor.cuarto_hora, cen.nombre_central
            LIMIT {batch_size} OFFSET {offset};
        """

        with conn.cursor() as cursor:
            cursor.execute(query_data)
            batch = cursor.fetchall()
            all_data.extend(batch)

        print(f"Lote vertimientos desde {offset} hasta {min(offset + batch_size, total_rows)} procesado")

    close_connection(conn, ssh_client, stop_event)

    return pd.DataFrame(all_data)


# =========================================================
# Extrae datos de CMG en lotes
# =========================================================
def extrae_data_cmg(batch_size=2400000, fecha_inicio=None, fecha_fin=None):
    conn, ssh_client, stop_event = open_connection()

    filtros = f"""
        FROM balance.cmg_barra
        WHERE nombre_cmg IN (
            'CRUCERO_______220',
            'P.AZUCAR______220',
            'QUILLOTA______220',
            'AJAHUEL_______500',
            'CHARRUA_______500',
            'P.MONTT_______220'
        )
        AND fecha_hora BETWEEN '{fecha_inicio}' AND '{fecha_fin}'
    """

    query_rows = f"""
        SELECT COUNT(*) AS total_rows
        {filtros};
    """

    with conn.cursor() as cursor:
        cursor.execute(query_rows)
        total_rows = cursor.fetchone()["total_rows"]

    print(f"Total de filas filtradas en balance.cmg_barra: {total_rows}")

    all_data = []

    for offset in range(0, total_rows, batch_size):
        query_data = f"""
            SELECT *
            {filtros}
            ORDER BY fecha_hora, nombre_cmg
            LIMIT {batch_size} OFFSET {offset};
        """

        with conn.cursor() as cursor:
            cursor.execute(query_data)
            batch = cursor.fetchall()
            all_data.extend(batch)

        print(f"Lote cmg_barra desde {offset} hasta {min(offset + batch_size, total_rows)} procesado")

    close_connection(conn, ssh_client, stop_event)

    return pd.DataFrame(all_data)


# =========================================================
# Extrae generación real en lotes
# =========================================================
def extrae_gx_real(batch_size=200000, fecha_inicio=None, fecha_fin=None):
    conn, ssh_client, stop_event = open_connection()

    last_id = 0
    all_data = []

    while True:
        query = f"""
        SELECT
            gx.id_generacion,
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