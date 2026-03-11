from utils.db_utils import open_connection, close_connection

BATCH_SIZE = 100000  # ajusta según rendimiento

conn, ssh_client, stop_event = open_connection()
cursor = conn.cursor()

# lista de IdVersion que quieres procesar
#id_versions = [33,34,35,36,38,39,40,41,42,43,44,45,46,47,48,49,50,51,52]
id_versiones = range(1, 53)  # ejemplo: IdVersion del 33 al 52

for i in id_versiones:
    while True:
        """query = f'''
        UPDATE balance.cmg c
        JOIN balance.hora_mensual_new hmn
          ON c.IdVersion = hmn.id_version
         AND c.Hora_Mensual = hmn.cuarto_hora
        SET c.id_hora = hmn.id_hora
        WHERE c.id_hora IS NULL
          AND c.IdVersion = {i}
        LIMIT {BATCH_SIZE};
        '''"""
        query=f'''
        UPDATE balance.retiro AS ret
        JOIN balance.medidores AS med
        ON ret.clave = med.clave
        SET ret.id_medidor = med.id_medidor
        WHERE ret.id_medidor IS NULL
          AND ret.id_version = {i}
        LIMIT {BATCH_SIZE}
        ;
        '''


        """query=f'''
        UPDATE balance.retiro
        SET clave = 'COPEC_REÑACA'
        WHERE clave = 'COPEC_REÃ‘ACA'
        LIMIT {BATCH_SIZE}
        ;
        '''"""

        cursor.execute(query)
        conn.commit()
        filas = cursor.rowcount
        if filas == 0:
            print(f"IdVersion={i} completado")
            break
        else:
            print(f"IdVersion={i}, filas actualizadas={filas}")

cursor.close()
close_connection(conn, ssh_client, stop_event)
print("Datos actualizados exitosamente en la tabla 'retiro'")


