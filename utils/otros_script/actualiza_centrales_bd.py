from utils.db_utils import open_connection, close_connection
import pandas as pd
from pathlib import Path
from rapidfuzz import process, fuzz
import re
import unicodedata
import json

'''Codigo que compara los datos de centrales que están en la base de datos con los datos que
 se descargan del reporte_centrales del coordinador para actualizar la base de datos si es necesario.'''

#Constantes globales
DATA_RAW = Path(__file__).parent / 'data' / 'raw'
DATA_PROCESSED = Path(__file__).parent / 'data' / 'processed'
REPORTE_CENTRALES = DATA_RAW / 'reporte_centrales.xlsx'
COMPARACION = DATA_PROCESSED / 'comparacion_centrales.xlsx'

def normalizar_nombre_db(nombre: str) -> str:
    # Casos específicos
    especificos = {
        "ARRAYAN": "EL ARRAYAN",
        "ARREBOL": "EL ARREBOL",
        "CHINCOL": "EL CHINCOL",
        "GORRIONES": "LOS GORRIONES",
        "LOS_GIRASOLES": "GIRASOLES",
        "GUINDILLAS": "LAS GUINDILLAS",
        "PICURO": "LOS PICUROS",
        "TURPIAL": "EL TURPIAL",
        "SIERRAGORDAE": "SIERRA GORDA ESTE",
        "RAPELU1": "RAPEL",
        "RAPELU2": "RAPEL",
        "RAPELU3": "RAPEL",
        "RAPELU4": "RAPEL",
        "RAPELU5": "RAPEL",
        "TOCOPILLA_TG1": "TOCOPILLA",
        "TOCOPILLA_TG2": "TOCOPILLA",
        "TOCOPILLA_TG3": "TOCOPILLA",
        "TOCOPILLA_U16": "TOCOPILLA",
        "JARDIN_PETORCA": "JARDIN SOLAR PETORCA",
        "EL MANZANO": "MANZANO",
        "MARANON": "MARAÑON",
        "PV_PITOTOY": "PITOTOY",
        "PICURO": "EL PICURO",
        "DALMAGROSOLAR": "DIEGO DE ALMAGRO SOLAR",
        "SOLAR_PACK_V.ALEMANA": "SOLARPACK VILLA ALEMANA",
        "COLBUN_U1": "COLBUN",
        "COLBUN_U2": "COLBUN",
        "CHACAYES_MINEROS": "CHACAYES",
        "CANDELARIA_1DIESEL": "CANDELARIA",
        "CANDELARIA_1GNL": "CANDELARIA",
        "CANDELARIA_2DIE": "CANDELARIA",
        "CANDELARIA_2GNL": "CANDELARIA",
        "CENTRAL_ACONCAGUATG1": "ACONCAGUA",
        "CHAGUAL(ex CONCHAYUYO)": "CHAGUAL",
        "ESPINOS": "LOS ESPINOS",
        "NEHUENCO1_DIE": "NEHUENCO",
        "NEHUENCO1_GNL": "NEHUENCO",
        "NEHUENCO1_GNL_CA": "NEHUENCO",
        "NEHUENCO2_DIE": "NEHUENCO",
        "NEHUENCO2_GNL": "NEHUENCO",
        "NEHUENCO2_GNL_CA": "NEHUENCO",
        "NEHUENCO9BB_GNL": "NEHUENCO",
        "NEWEN_DIE": "NEWEN",
        "NEWEN_GNA": "NEWEN",
        "NEWEN_GNL": "NEWEN",
        "NEWEN_PRO": "NEWEN",
        "PEÑON": "EL PEÑON",
        "RINCON": "EL RINCON",
        "LEBU_III_CRISTORO": "LEBU III",
        "HORMIGA": "HORMIGA SOLAR",
        "VALLE_LUNA_2": "VALLE DE LUNA II",
        "ROSA SHARON": "LA ROSA SHARON",
        "UTFSM_VALPARAISO": "UTFSM VALPARAISO VALDES",
        "SLK_CB9": "SLK CB NUEVE",
        "ZORZAL": "EL ZORZAL",
        "DALMAGRO_SUR": "DIEGO DE ALMAGRO SUR",
        "DONACARMEN": "DOÑA CARMEN SOLAR",
        "UTFSM_VINADELMAR": "PMGD PFV UTFSM VIÑA DEL MAR",
        "PM_FV_NORTHWEST": "PMG NORTH WEST",
        "CHAGUAL(ex Condores)": "CHAGUAL",
        "CASA_BERMEJA": "CASABERMEJA",
        "CENTRAL_ACONCAGUATG": "ACONCAGUA",

    }   



    if nombre in especificos:
        nombre = especificos[nombre]
        # Reemplazar guiones bajos por espacios y limpiar espacios extra
    nombre = nombre.replace("_", " ")
    nombre = re.sub(r"\s+", " ", nombre).strip()

    return nombre


def normalizar_tecnologia_db(valor: str) -> str:
    if not valor:
        return None
    valor = valor.strip().lower()
    mapping = {
        "fotovoltaica": "fotovoltaica",
        "fotovoltaico": "fotovoltaica",
        "concentradorsolar": "fotovoltaica",
        "bess": "bess",
        "biomasa": "termoelectrica",
        "biogas": "termoelectrica",
        "termica": "termoelectrica",
        "eolico": "eolica",
        "geotermia": "termoelectrica",
        "hidroeléctricapasada": "hidroelectrica",
        "hidroeléctricaembalse": "hidroelectrica",
    }
    return mapping.get(valor, valor.capitalize())


def normalizar_tipo_conversion_reporte(valor: str) -> str:
    if not valor:
        return None
    valor = valor.strip().lower()
    mapping = {
        "fotovoltaica": "fotovoltaica",
        "fotovoltaico": "fotovoltaica",
        "concentradorsolar": "fotovoltaica",
        "termoeléctrica": "termoelectrica",
        "hidroeléctrica": "hidroelectrica",
        "hidroeléctricapasada": "hidroelectrica",
        "hidroeléctricaembalse": "hidroelectrica",
        "eólica": "eolica",
        "biomasa": "termoelectrica",
        "biogás": "termoelectrica",
        "geotermia": "termoelectrica",
    }
    return mapping.get(valor, valor.capitalize())


def quitar_tildes(texto: str) -> str:
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

def normalizar_nombre_reporte(nombre: str) -> str:
    prefijos = ["PMGD PFV", "PMGD PE ", "PMGD PFV PSF ","PMGD TER ", "PMGD HP ", "PFV ", "PMG " "TER ", "HP ", "PE ", "HE ","PMGD ", "PMGD HP ","GEO ", "PE ","PVP ", "TER ",  "PSF ","GR "]
    for prefijo in prefijos:
        if nombre.startswith(prefijo):
            nombre = nombre[len(prefijo):]
    nombre = quitar_tildes(nombre)
    nombre = re.sub(r"\s+", " ", nombre).strip()
    return nombre

def comparar_nombres_df(nombres_db, nombres_db_norm,
                        nombres_reporte, nombres_reporte_norm,
                        tecnologias_db, conversiones_reporte,
                        threshold=90):
    resultados = []
    for nombre_db, nombre_db_norm, tecnologia_db in zip(nombres_db, nombres_db_norm, tecnologias_db):
        match = process.extractOne(nombre_db_norm, nombres_reporte_norm, scorer=fuzz.token_set_ratio)

        if match:
            idx = nombres_reporte_norm.index(match[0])
            nombre_reporte_final = nombres_reporte[idx]
            nombre_reporte_norm_final = nombres_reporte_norm[idx]
            conversion_final = conversiones_reporte[idx]
        else:
            nombre_reporte_final = None
            nombre_reporte_norm_final = None
            conversion_final = None

        tecnologia_norm = normalizar_tecnologia_db(tecnologia_db)
        conversion_norm = normalizar_tipo_conversion_reporte(conversion_final)

        # Comparaciones con token_set_ratio
        similitud_nombre = fuzz.token_set_ratio(nombre_db_norm, nombre_reporte_norm_final) if nombre_reporte_norm_final else 0
        similitud_tecnologia = fuzz.token_set_ratio(tecnologia_norm, conversion_norm) if conversion_norm else 0
        cadena_db = f"{nombre_db_norm} {tecnologia_norm}".strip()
        cadena_reporte = f"{nombre_reporte_norm_final} {conversion_norm}".strip() if conversion_norm else nombre_reporte_norm_final
        similitud_combinada = fuzz.token_set_ratio(cadena_db, cadena_reporte) if cadena_reporte else 0

        resultados.append({
            "nombre_db": nombre_db,
            "nombre_db_normalizado": nombre_db_norm,
            "tecnologia_db": tecnologia_db,
            "tecnologia_db_normalizada": tecnologia_norm,
            "nombre_reporte": nombre_reporte_final,
            "nombre_reporte_normalizado": nombre_reporte_norm_final,
            "tipo_conversion_energia_reporte": conversion_final,
            "tipo_conversion_energia_reporte_normalizada": conversion_norm,
            "similitud_nombre": similitud_nombre,
            "similitud_tecnologia": similitud_tecnologia,
            "similitud_combinada": similitud_combinada,
            "coincidencia_nombre": similitud_nombre >= threshold,
            "coincidencia_tecnologia": similitud_tecnologia >= threshold,
            "coincidencia_combinada": similitud_combinada >= threshold
        })

    return pd.DataFrame(resultados)



def extract_centrales_data():
    conn, ssh_client, stop_event = open_connection()

    query_centrales = """
        SELECT * FROM balance.centrales;
    """

    with conn.cursor() as cursor:
        cursor.execute(query_centrales)
        data_centrales = cursor.fetchall()  # ya devuelve lista de dicts

    close_connection(conn, ssh_client, stop_event)

    return pd.DataFrame(data_centrales)

def extract_reporte_centrales():
    # Leer el reporte de centrales desde el archivo Excel
    df_reporte = pd.read_excel(REPORTE_CENTRALES, skiprows=6)
    #conserva solo las columnas necesarias y renombra para que coincidan con la base de datos
    columnas_necesarias = ['ID', 'Nombre', 'Nombre Propietario', 'Comuna', 'Tipo Central', 'Nemotecnico', 'Tipo Central', 'Estado (operativa/en pruebas/en construcción)', '11.1.1 Cantidad unidades generadoras','11.1.2 Puntos de conexión al SI a través de los cuales inyecta energía.', '11.1.6 Capacidad máxima, potencia neta efectiva','11.1.11 Fecha de entrada en operación','10.1.35 Tipo de conversión de energía','11.1.35 Combustible (solo para termoeléctricas)', '11.1.38 Tipo de tecnología de la central', '10.1.35 Medio de generación según DS 125-2019 y DS 88-2020']
    df_reporte = df_reporte[columnas_necesarias]
    df_reporte.rename(columns={
        'ID': 'id',
        'Nombre': 'nombre',
        'Nombre Propietario': 'nombre_propietario',
        'Comuna': 'comuna',
        'Tipo Central': 'tipo_central',
        'Nemotecnico': 'nemotecnico',
        'Tecnología': 'tecnologia',
        'Estado (operativa/en pruebas/en construcción)': 'estado',
        '11.1.1 Cantidad unidades generadoras': 'n_unidades_generadoras',
        '11.1.2 Puntos de conexión al SI a través de los cuales inyecta energía.': 'punto_conexion_sen',
        '11.1.6 Capacidad máxima, potencia neta efectiva': 'capacidad_maxima_mw',
        '11.1.11 Fecha de entrada en operación': 'fecha_entrada_operacion',
        '10.1.35 Tipo de conversión de energía': 'tipo_conversion_energia',
        '11.1.35 Combustible (solo para termoeléctricas)': 'combustible',
        '11.1.38 Tipo de tecnología de la central': 'tipo_tecnologia',
        '10.1.35 Medio de generación según DS 125-2019 y DS 88-2020': 'medio_generacion_ds'
    }, inplace=True)
    return df_reporte


### Luego de validada la comparación, se pueden actualizar los valores en la base de datos
#  usando el resultado del dataframe de comparación para hacer un update en la base de datos.

# Diccionario de normalización plural → singular
map_tipo_central = {
    "termoelectricas": "termoelectrica",
    "eolicas": "eolica",
    "solares": "solar",
    "hidroelectricas": "hidroelectrica"
}

#Diccionario de normalización medio generación según segmento de generación
map_pgmds = {
    "instalaciones de generacion": "utility",
    "pequenos medio de generacion o pmg": "pmg",
    "pequenos medio de generacion distribuida o pmgd": "pmgd",}

# Diccionario de cut_comunas desde json
with open('utils/cut_comunas.json', 'r', encoding='utf-8') as f:    
    cut_comunas = json.load(f)

# Función para limpiar texto: minúsculas y sin tildes
def limpiar_key(texto: str) -> str:
    texto = texto.lower()
    texto = ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )
    return texto

# Crear nuevo diccionario con keys normalizadas
cut_comunas_normalizado = {limpiar_key(k): v for k, v in cut_comunas.items()}


def generar_csv_carga(df_resultados, df_centrales_db, df_reporte_centrales, ruta_salida):
    # Filtrar coincidencias
    df_filtrado = df_resultados[
        (df_resultados['coincidencia_tecnologia']) &
        (df_resultados['coincidencia_combinada'])
    ].copy()

    # Traer id_central desde la BD
    df_filtrado = df_filtrado.merge(
        df_centrales_db[['nombre', 'id_central']],  # nombre BD y su id
        left_on='nombre_db',
        right_on='nombre',
        how='left'
    ).rename(columns={'id_central': 'id_central'}).drop(columns=['nombre'])

    # Traer todas las variables del reporte usando nombre_reporte
    df_filtrado = df_filtrado.merge(
        df_reporte_centrales,
        left_on='nombre_reporte',
        right_on='nombre',
        how='left',
        suffixes=('', '_reporte')
    )
    '''
    nombre_db,
    nombre_db_normalizado,
    tecnologia_db,
    tecnologia_db_normalizada,
    nombre_reporte,
    nombre_reporte_normalizado,
    tipo_conversion_energia_reporte,
    tipo_conversion_energia_reporte_normalizada,
    similitud_nombre,
    similitud_tecnologia,
    similitud_combinada,
    coincidencia_nombre,
    coincidencia_tecnologia,
    coincidencia_combinada,
    id_central,
    id,
    nombre,
    nombre_propietario,
    comuna,
    tipo_central,
    nemotecnico,
    tipo_central,
    estado,
    n_unidades_generadoras,
    punto_conexion_sen,
    capacidad_maxima_mw,
    fecha_entrada_operacion,
    tipo_conversion_energia,
    combustible,
    tipo_tecnologia,
    medio_generacion_ds,
    nombre_reporte_normalizado_reporte
    '''
    # Eliminar columnas innecesarias para la carga a la base de datos
    columnas_para_carga = [
        'id_central',
        'id',
        'nombre',
        'nombre_propietario',
        'comuna',
        'tipo_central',
        'nemotecnico',
        'estado',
        'n_unidades_generadoras',
        'punto_conexion_sen',
        'capacidad_maxima_mw',
        'fecha_entrada_operacion',
        'tipo_conversion_energia',
        'combustible',
        'tipo_tecnologia',
        'medio_generacion_ds'
    ]
    df_filtrado = df_filtrado[columnas_para_carga]
    # Renommbramos columna id
    df_filtrado.rename(columns={'id': 'id_infotecnica','nombre': 'nombre_infotecnica'}, inplace=True)
    #Eliminamos columna duplicada
    df_filtrado = df_filtrado.loc[:, ~df_filtrado.columns.duplicated()]
    # Pasar a minúsculas
    df_filtrado = df_filtrado.applymap(lambda x: x.lower() if isinstance(x, str) else x)
    #eliminamos tildes
    df_filtrado = df_filtrado.applymap(lambda x: quitar_tildes(x)   if isinstance(x, str) else x)
    # Aplicar normalización
    df_filtrado['tipo_central'] = df_filtrado['tipo_central'].replace(map_tipo_central)
    # Normalizar medio_generacion_ds usando map_pgmds
    df_filtrado['segmento_generacion'] = df_filtrado['medio_generacion_ds'].replace(map_pgmds)
    # Eliminar columna medio_generacion_ds ya que no es necesaria para la carga
    df_filtrado.drop(columns=['medio_generacion_ds'], inplace=True)
    # agregar cut_comuna usando el diccionario cut_comunas_normalizado y la comuna de cada central
    df_filtrado['cut_comuna'] = df_filtrado['comuna'].replace(cut_comunas_normalizado)
    #pasar nombre_infotecnica a mayúsculas y eliminar prefijos comunes    
    # Eliminar prefijos de la columna nombre
    df_filtrado['nombre_infotecnica'] = df_filtrado['nombre_infotecnica'].str.upper()
    df_filtrado['nombre_propietario'] = df_filtrado['nombre_propietario'].str.upper()
    df_filtrado['comuna'] = df_filtrado['comuna'].str.upper()
    df_filtrado['tipo_conversion_energia'] = df_filtrado['tipo_conversion_energia'].str.upper()
    df_filtrado['combustible'] = df_filtrado['combustible'].str.upper()
    df_filtrado['tipo_tecnologia'] = df_filtrado['tipo_tecnologia'].str.upper()
    df_filtrado['segmento_generacion'] = df_filtrado['segmento_generacion'].str.upper()
    df_filtrado['combustible'] = df_filtrado['combustible'].str.upper()
    df_filtrado['nemotecnico'] = df_filtrado['nemotecnico'].str.upper()
    df_filtrado['estado'] = df_filtrado['estado'].str.upper()
    df_filtrado['tipo_central'] = df_filtrado['tipo_central'].str.upper()
    df_filtrado['punto_conexion_sen'] = df_filtrado['punto_conexion_sen'].str.upper()
    prefijos = ["PMGD PFV", "PMGD PE ", "PMGD PFV PSF ","PMGD TER ", "PMGD HP ", "PFV ", "PMG " "TER ", "HP ", "PE ", "HE ","PMGD ", "PMGD HP ","GEO ", "PE ","PVP ", "TER ",  "PSF ","GR "]
    for prefijo in prefijos:
        df_filtrado['nombre_infotecnica'] = df_filtrado['nombre_infotecnica'].str.replace(f"^{prefijo}", "", regex=True)

    # Guardar CSV
    df_filtrado.to_csv(ruta_salida, index=False)
    return df_filtrado

def main():
    df_centrales_db = extract_centrales_data()
    df_reporte_centrales = extract_reporte_centrales()

    # Normalizaciones
    df_centrales_db['nombre_db_normalizado'] = df_centrales_db['nombre'].apply(normalizar_nombre_db)
    df_reporte_centrales['nombre_reporte_normalizado'] = df_reporte_centrales['nombre'].apply(normalizar_nombre_reporte).str.upper()

    # Comparación
    df_resultados = comparar_nombres_df(
        df_centrales_db['nombre'].tolist(),
        df_centrales_db['nombre_db_normalizado'].tolist(),
        df_reporte_centrales['nombre'].tolist(),
        df_reporte_centrales['nombre_reporte_normalizado'].tolist(),
        df_centrales_db['tecnologia'].tolist(),
        df_reporte_centrales['tipo_conversion_energia'].tolist(),
        threshold=84
    )
    

    # Generar CSV de carga
    ruta_csv = DATA_PROCESSED / "carga_centrales.csv"
    df_carga = generar_csv_carga(df_resultados, df_centrales_db, df_reporte_centrales, ruta_csv)

    print("CSV de carga generado:")
    print(df_carga.head())



if __name__ == "__main__":
    main()



