import pandas as pd
from utils.db_utils import open_connection, close_connection
from utils.config_loader import get_config

_cfg = get_config()


# =========================================================
# Helper — convierte timestamp a filtro (año, mes)
# =========================================================

def _filtro_año_mes(fecha_inicio: pd.Timestamp, fecha_fin: pd.Timestamp) -> str:
    """
    Genera un fragmento SQL que filtra por (año, mes) usando los índices
    de hora_mensual, en lugar de filtrar por fecha_hora.

    Para rangos dentro del mismo año usa una sola condición.
    Para rangos multi-año expande cada mes explícitamente si el rango
    es pequeño, o usa comparación de entero compuesto (año*100+mes) si
    es grande — esto garantiza que el optimizador use los índices.
    """
    # Representación compacta: YYYYMM como entero — funciona con índices simples
    ini = fecha_inicio.year * 100 + fecha_inicio.month
    fin = fecha_fin.year   * 100 + fecha_fin.month

    if ini > fin:
        raise ValueError(
            f"fecha_inicio ({fecha_inicio:%Y-%m}) es posterior a "
            f"fecha_fin ({fecha_fin:%Y-%m})"
        )

    # Usamos expresión calculada sobre columnas indexadas.
    # Si el motor no puede usar el índice compuesto directamente,
    # añadir un índice funcional: CREATE INDEX ON hora_mensual ((año*100+mes))
    return f"(hor.año * 100 + hor.mes) BETWEEN {ini} AND {fin}"


def _validar_rango(fecha_inicio: pd.Timestamp, fecha_fin: pd.Timestamp, contexto: str = ""):
    """Lanza un error descriptivo si el rango está invertido o es vacío."""
    if fecha_inicio > fecha_fin:
        raise ValueError(
            f"Rango inválido{' (' + contexto + ')' if contexto else ''}: "
            f"inicio {fecha_inicio:%Y-%m} > fin {fecha_fin:%Y-%m}"
        )
    if fecha_inicio == fecha_fin:
        # Rango de un mes — válido pero lo avisamos
        print(f"⚠️  Rango de un solo mes{' (' + contexto + ')' if contexto else ''}: "
              f"{fecha_inicio:%Y-%m}. Verificar que esto sea intencional.")


# =========================================================
# Extrae datos de vertimientos
# =========================================================

def extrae_data_total_vertimientos(
    batch_size=None,
    fecha_inicio=None, fecha_fin=None,
    fecha_comparacion_inicio=None, fecha_comparacion_fin=None,
):
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["vertimientos"]

    # Convertir a Timestamp si vienen como string
    fecha_inicio             = pd.to_datetime(fecha_inicio)
    fecha_fin                = pd.to_datetime(fecha_fin)
    fecha_comparacion_inicio = pd.to_datetime(fecha_comparacion_inicio)
    fecha_comparacion_fin    = pd.to_datetime(fecha_comparacion_fin)

    _validar_rango(fecha_inicio, fecha_fin, "estudio vertimientos")
    _validar_rango(fecha_comparacion_inicio, fecha_comparacion_fin, "comparación vertimientos")

    filtro_estudio     = _filtro_año_mes(fecha_inicio, fecha_fin)
    filtro_comparacion = _filtro_año_mes(fecha_comparacion_inicio, fecha_comparacion_fin)

    def _extraer_vertimientos(filtro_hor: str, contexto: str) -> pd.DataFrame:
        conn, ssh_client, stop_event = open_connection()

        # hora_mensual ahora se filtra por año/mes — el JOIN actúa como filtro
        query_rows = f"""
            SELECT COUNT(*) AS total_rows
            FROM balance.vertimiento AS vert
            JOIN balance.version     AS ver ON ver.id_version = vert.id_version
            JOIN balance.hora_mensual AS hor ON hor.id_hora  = vert.id_hora
            WHERE {filtro_hor};
        """
        with conn.cursor() as cursor:
            cursor.execute(query_rows)
            total_rows = cursor.fetchone()["total_rows"]

        print(f"Total filas vertimientos ({contexto}): {total_rows}")

        all_data = []
        for offset in range(0, total_rows, batch_size):
            query_data = f"""
                SELECT
                    TRIM(REPLACE(REPLACE(cen.nombre_central, '\\r', ' '), '\\n', ' ')) AS nombre_central,
                    cen.id_central,
                    hor.id_hora,
                    TRIM(REPLACE(REPLACE(vert.tipo, '\\r', ''), '\\n', '')) AS tipo,
                    ver.periodo,
                    hor.cuarto_hora,
                    hor.dia,
                    hor.hora,
                    hor.minuto,
                    hor.año   AS anio,
                    hor.mes,
                    vert.vertimiento
                FROM balance.vertimiento AS vert
                JOIN balance.version      AS ver ON ver.id_version = vert.id_version
                JOIN balance.hora_mensual AS hor ON hor.id_hora    = vert.id_hora
                JOIN balance.central      AS cen ON vert.id_central = cen.id_central
                WHERE {filtro_hor}
                LIMIT {batch_size} OFFSET {offset};
            """
            with conn.cursor() as cursor:
                cursor.execute(query_data)
                all_data.extend(cursor.fetchall())
            print(f"  Lote {offset}–{offset + batch_size} procesado ({contexto})")

        close_connection(conn, ssh_client, stop_event)
        return pd.DataFrame(all_data)

    df_estudio     = _extraer_vertimientos(filtro_estudio,     "estudio")
    df_comparacion = _extraer_vertimientos(filtro_comparacion, "comparación")

    return df_estudio, df_comparacion


# =========================================================
# Extrae datos de CMG en lotes
# =========================================================

def extrae_data_cmg(
    batch_size=None,
    fecha_inicio=None, fecha_fin=None,
    fecha_inicio_comparacion=None, fecha_fin_comparacion=None,
):
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["cmg"]

    fecha_inicio             = pd.to_datetime(fecha_inicio)
    fecha_fin                = pd.to_datetime(fecha_fin)
    fecha_inicio_comparacion = pd.to_datetime(fecha_inicio_comparacion)
    fecha_fin_comparacion    = pd.to_datetime(fecha_fin_comparacion)

    _validar_rango(fecha_inicio, fecha_fin, "estudio CMg")
    _validar_rango(fecha_inicio_comparacion, fecha_fin_comparacion, "comparación CMg")

    _barras     = _cfg["consultas"]["cmg_barras"]
    _barras_sql = ", ".join(f"'{b}'" for b in _barras)

    # CMg filtra por fecha_hora directamente — la tabla no usa hora_mensual,
    # así que aquí no aplica el cambio de año/mes. Se mantiene BETWEEN original.
    def _extraer_cmg(f_ini: pd.Timestamp, f_fin: pd.Timestamp, contexto: str) -> pd.DataFrame:
        conn, ssh_client, stop_event = open_connection()

        # Fin de mes para incluir todas las horas del último mes
        f_fin_inclusive = f_fin + pd.offsets.MonthEnd(0)

        filtro = f"""
            nombre_cmg IN ({_barras_sql})
            AND fecha_hora BETWEEN '{f_ini:%Y-%m-%d}' AND '{f_fin_inclusive:%Y-%m-%d %H:%M:%S}'
        """

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total_rows FROM balance.cmg_barra WHERE {filtro};")
            total_rows = cursor.fetchone()["total_rows"]

        print(f"Total filas CMg ({contexto}): {total_rows}")

        all_data = []
        for offset in range(0, total_rows, batch_size):
            query = f"""
                SELECT *
                FROM balance.cmg_barra
                WHERE {filtro}
                ORDER BY fecha_hora, nombre_cmg
                LIMIT {batch_size} OFFSET {offset};
            """
            with conn.cursor() as cursor:
                cursor.execute(query)
                all_data.extend(cursor.fetchall())
            print(f"  Lote {offset}–{min(offset + batch_size, total_rows)} procesado ({contexto})")

        close_connection(conn, ssh_client, stop_event)
        return pd.DataFrame(all_data)

    df_estudio     = _extraer_cmg(fecha_inicio, fecha_fin, "estudio")
    df_comparacion = _extraer_cmg(fecha_inicio_comparacion, fecha_fin_comparacion, "comparación")

    return df_estudio, df_comparacion


# =========================================================
# Extrae generación real en lotes
# =========================================================

def extrae_gx_real(
    batch_size=None,
    fecha_inicio=None, fecha_fin=None,
    fecha_inicio_comparacion=None, fecha_fin_comparacion=None,
):
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["gx_real"]

    fecha_inicio             = pd.to_datetime(fecha_inicio)
    fecha_fin                = pd.to_datetime(fecha_fin)
    fecha_inicio_comparacion = pd.to_datetime(fecha_inicio_comparacion)
    fecha_fin_comparacion    = pd.to_datetime(fecha_fin_comparacion)

    _validar_rango(fecha_inicio, fecha_fin, "estudio gx_real")
    _validar_rango(fecha_inicio_comparacion, fecha_fin_comparacion, "comparación gx_real")

    def _extraer(conn, f_ini: pd.Timestamp, f_fin: pd.Timestamp, batch_size: int) -> pd.DataFrame:
        filtro_hor = _filtro_año_mes(f_ini, f_fin)
        last_id    = 0
        all_data   = []

        while True:
            query = f"""
                SELECT
                    gx.id_generacion,
                    cen.id_central,
                    gx.id_hora,
                    hor.fecha_hora,
                    hor.año   AS anio,
                    hor.mes,
                    gx.inyeccion_retiro,
                    cen.tipo,
                    gx.subtipo
                FROM balance.gx_real gx
                JOIN balance.central      cen ON cen.id_central = gx.id_central
                JOIN balance.hora_mensual hor ON hor.id_hora    = gx.id_hora
                WHERE {filtro_hor}
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
            print(f"  Procesado gx_real hasta id_generacion {last_id}")

        return pd.DataFrame(all_data)

    conn, ssh_client, stop_event = open_connection()
    df_estudio = _extraer(conn, fecha_inicio, fecha_fin, batch_size)
    close_connection(conn, ssh_client, stop_event)

    conn, ssh_client, stop_event = open_connection()
    df_comparacion = _extraer(conn, fecha_inicio_comparacion, fecha_fin_comparacion, batch_size)
    close_connection(conn, ssh_client, stop_event)

    return df_estudio, df_comparacion


# =========================================================
# Extrae generación real — comparación fija (ej: 2022)
# =========================================================

def extrae_gx_real_comparacion(batch_size=None):
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["gx_real"]

    fecha_inicio = pd.to_datetime(_cfg["reporte"]["fecha_comparacion_fija_inicio"])
    fecha_fin    = pd.to_datetime(_cfg["reporte"]["fecha_comparacion_fija_fin"])

    _validar_rango(fecha_inicio, fecha_fin, "comparación fija gx_real")

    filtro_hor = _filtro_año_mes(fecha_inicio, fecha_fin)

    conn, ssh_client, stop_event = open_connection()

    last_id  = 0
    all_data = []

    while True:
        query = f"""
            SELECT
                gx.id_generacion,
                cen.id_central,
                gx.id_hora,
                hor.fecha_hora,
                hor.año   AS anio,
                hor.mes,
                gx.inyeccion_retiro,
                cen.tipo,
                gx.subtipo
            FROM balance.gx_real gx
            JOIN balance.central      cen ON cen.id_central = gx.id_central
            JOIN balance.hora_mensual hor ON hor.id_hora    = gx.id_hora
            WHERE {filtro_hor}
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
        print(f"  Procesado gx_real_comparacion hasta id_generacion {last_id}")

    close_connection(conn, ssh_client, stop_event)
    return pd.DataFrame(all_data)