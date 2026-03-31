import pandas as pd
from utils.db_utils import open_connection, close_connection
from utils.config_loader import get_config

_cfg = get_config()


# =========================================================
# Helper — ventana anual estándar
# =========================================================

def _ventana_anual(fecha_fin: pd.Timestamp):
    """
    Ventana estándar para todos los gráficos:
    - Estudio:     1 enero año en curso → mes de estudio
    - Comparación: año anterior completo (1 enero → 31 diciembre)

    Ej: fecha_fin=2026-01
        estudio:     2026-01-01 → 2026-01
        comparación: 2025-01-01 → 2025-12-31

    Ej: fecha_fin=2026-06
        estudio:     2026-01-01 → 2026-06
        comparación: 2025-01-01 → 2025-12-31
    """
    ini_estudio = pd.Timestamp(year=fecha_fin.year,     month=1,  day=1)
    fin_estudio = fecha_fin
    ini_comp    = pd.Timestamp(year=fecha_fin.year - 1, month=1,  day=1)
    fin_comp    = pd.Timestamp(year=fecha_fin.year - 1, month=12, day=31)
    return ini_estudio, fin_estudio, ini_comp, fin_comp


# =========================================================
# Helper — convierte timestamp a filtro (año, mes)
# =========================================================

def _filtro_año_mes(fecha_inicio: pd.Timestamp, fecha_fin: pd.Timestamp) -> str:
    ini = fecha_inicio.year * 100 + fecha_inicio.month
    fin = fecha_fin.year   * 100 + fecha_fin.month

    if ini > fin:
        raise ValueError(
            f"fecha_inicio ({fecha_inicio:%Y-%m}) es posterior a "
            f"fecha_fin ({fecha_fin:%Y-%m})"
        )
    return f"(hor.año * 100 + hor.mes) BETWEEN {ini} AND {fin}"


def _validar_rango(fecha_inicio: pd.Timestamp, fecha_fin: pd.Timestamp, contexto: str = ""):
    if fecha_inicio > fecha_fin:
        raise ValueError(
            f"Rango inválido{' (' + contexto + ')' if contexto else ''}: "
            f"inicio {fecha_inicio:%Y-%m} > fin {fecha_fin:%Y-%m}"
        )
    if fecha_inicio == fecha_fin:
        print(f"⚠️  Rango de un solo mes{' (' + contexto + ')' if contexto else ''}: "
              f"{fecha_inicio:%Y-%m}. Verificar que esto sea intencional.")


# =========================================================
# Extrae datos de vertimientos
# =========================================================

def extrae_data_total_vertimientos(batch_size=None, fecha_fin=None):
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["vertimientos"]

    fecha_fin = pd.to_datetime(fecha_fin)
    ini_e, fin_e, ini_c, fin_c = _ventana_anual(fecha_fin)

    _validar_rango(ini_e, fin_e, "estudio vertimientos")
    _validar_rango(ini_c, fin_c, "comparación vertimientos")
    print(f"Vertimientos estudio:     {ini_e:%Y-%m} → {fin_e:%Y-%m}")
    print(f"Vertimientos comparación: {ini_c:%Y-%m} → {fin_c:%Y-%m}")

    filtro_estudio     = _filtro_año_mes(ini_e, fin_e)
    filtro_comparacion = _filtro_año_mes(ini_c, fin_c)

    def _extraer_vertimientos(filtro_hor: str, contexto: str) -> pd.DataFrame:
        conn, ssh_client, stop_event = open_connection()

        with conn.cursor() as cursor:
            cursor.execute(f"""
                SELECT COUNT(*) AS total_rows
                FROM balance.vertimiento AS vert
                JOIN balance.version      AS ver ON ver.id_version = vert.id_version
                JOIN balance.hora_mensual AS hor ON hor.id_hora    = vert.id_hora
                WHERE {filtro_hor};
            """)
            total_rows = cursor.fetchone()["total_rows"]

        print(f"Total filas vertimientos ({contexto}): {total_rows}")

        all_data = []
        for offset in range(0, total_rows, batch_size):
            with conn.cursor() as cursor:
                cursor.execute(f"""
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
                """)
                all_data.extend(cursor.fetchall())
            print(f"  Lote {offset}–{offset + batch_size} procesado ({contexto})")

        close_connection(conn, ssh_client, stop_event)
        return pd.DataFrame(all_data)

    return (
        _extraer_vertimientos(filtro_estudio,     "estudio"),
        _extraer_vertimientos(filtro_comparacion, "comparación"),
    )


# =========================================================
# Extrae datos de CMG en lotes
# =========================================================

def extrae_data_cmg(batch_size=None, fecha_fin=None):
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["cmg"]

    fecha_fin = pd.to_datetime(fecha_fin)
    ini_e, fin_e, ini_c, fin_c = _ventana_anual(fecha_fin)

    # CMg necesita incluir todas las horas del último mes
    fin_e_inc = fin_e + pd.offsets.MonthEnd(0)
    fin_c_inc = fin_c + pd.offsets.MonthEnd(0)

    _validar_rango(ini_e, fin_e, "estudio CMg")
    _validar_rango(ini_c, fin_c, "comparación CMg")
    print(f"CMg estudio:     {ini_e:%Y-%m} → {fin_e:%Y-%m}")
    print(f"CMg comparación: {ini_c:%Y-%m} → {fin_c:%Y-%m}")

    _barras     = _cfg["consultas"]["cmg_barras"]
    _barras_sql = ", ".join(f"'{b}'" for b in _barras)

    def _extraer_cmg(f_ini: pd.Timestamp, f_fin_inc: pd.Timestamp, contexto: str) -> pd.DataFrame:
        conn, ssh_client, stop_event = open_connection()

        filtro = f"""
            nombre_cmg IN ({_barras_sql})
            AND fecha_hora BETWEEN '{f_ini:%Y-%m-%d}' AND '{f_fin_inc:%Y-%m-%d %H:%M:%S}'
        """

        with conn.cursor() as cursor:
            cursor.execute(f"SELECT COUNT(*) AS total_rows FROM balance.cmg_barra WHERE {filtro};")
            total_rows = cursor.fetchone()["total_rows"]

        print(f"Total filas CMg ({contexto}): {total_rows}")

        all_data = []
        for offset in range(0, total_rows, batch_size):
            with conn.cursor() as cursor:
                cursor.execute(f"""
                    SELECT fecha_hora, nombre_cmg, CMG_DOLAR_MWH
                    FROM balance.cmg_barra
                    WHERE {filtro}
                    ORDER BY fecha_hora, nombre_cmg
                    LIMIT {batch_size} OFFSET {offset};
                """)
                all_data.extend(cursor.fetchall())
            print(f"  Lote {offset}–{min(offset + batch_size, total_rows)} procesado ({contexto})")

        close_connection(conn, ssh_client, stop_event)
        return pd.DataFrame(all_data)

    return (
        _extraer_cmg(ini_e, fin_e_inc, "estudio"),
        _extraer_cmg(ini_c, fin_c_inc, "comparación"),
    )


# =========================================================
# Extrae generación real en lotes
# =========================================================

def extrae_gx_real(batch_size=None, fecha_fin=None):
    """
    Estudio:     1 enero año en curso → mes de estudio
    Comparación: año anterior completo
    El mes en curso se filtra en main.py para gx_real_tipico.
    """
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["gx_real"]

    fecha_fin = pd.to_datetime(fecha_fin)
    ini_e, fin_e, ini_c, fin_c = _ventana_anual(fecha_fin)

    _validar_rango(ini_e, fin_e, "estudio gx_real")
    _validar_rango(ini_c, fin_c, "comparación gx_real")
    print(f"gx_real estudio:     {ini_e:%Y-%m} → {fin_e:%Y-%m}")
    print(f"gx_real comparación: {ini_c:%Y-%m} → {fin_c:%Y-%m}")

    def _extraer(conn, f_ini: pd.Timestamp, f_fin: pd.Timestamp) -> pd.DataFrame:
        filtro_hor = _filtro_año_mes(f_ini, f_fin)
        last_id, all_data = 0, []
        while True:
            with conn.cursor() as cursor:
                cursor.execute(f"""
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
                """)
                batch = cursor.fetchall()
            if not batch:
                break
            all_data.extend(batch)
            last_id = batch[-1]["id_generacion"]
            print(f"  gx_real hasta id {last_id}")
        return pd.DataFrame(all_data)

    conn, ssh_client, stop_event = open_connection()
    df_estudio = _extraer(conn, ini_e, fin_e)
    close_connection(conn, ssh_client, stop_event)

    conn, ssh_client, stop_event = open_connection()
    df_comparacion = _extraer(conn, ini_c, fin_c)
    close_connection(conn, ssh_client, stop_event)

    return df_estudio, df_comparacion


# =========================================================
# Extrae generación real — comparación fija (ej: 2022)
# =========================================================

def extrae_gx_real_comparacion(batch_size=None, mes: int = None):
    """
    Extrae gx_real del año fijo de comparación (ej: 2022),
    solo para el mes equivalente al mes del reporte.
    """
    if batch_size is None:
        batch_size = _cfg["consultas"]["batch_sizes"]["gx_real"]

    anio_fijo = pd.to_datetime(_cfg["reporte"]["fecha_comparacion_fija_inicio"]).year

    if mes is not None:
        fecha_inicio = pd.Timestamp(year=anio_fijo, month=mes, day=1)
        fecha_fin_   = fecha_inicio
    else:
        fecha_inicio = pd.to_datetime(_cfg["reporte"]["fecha_comparacion_fija_inicio"])
        fecha_fin_   = pd.to_datetime(_cfg["reporte"]["fecha_comparacion_fija_fin"])

    # Solo formatear mes si está definido
    contexto = f"comparación fija gx_real {anio_fijo}-{mes:02d}" if mes else "comparación fija gx_real"
    _validar_rango(fecha_inicio, fecha_fin_, contexto)
    print(f"gx_real comparación fija: {fecha_inicio:%Y-%m}")

    filtro_hor = _filtro_año_mes(fecha_inicio, fecha_fin_)

    conn, ssh_client, stop_event = open_connection()
    last_id, all_data = 0, []

    while True:
        with conn.cursor() as cursor:
            cursor.execute(f"""
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
            """)
            batch = cursor.fetchall()
        if not batch:
            break
        all_data.extend(batch)
        last_id = batch[-1]["id_generacion"]
        print(f"  gx_real_comparacion_fija hasta id {last_id}")

    close_connection(conn, ssh_client, stop_event)
    return pd.DataFrame(all_data)