def df2db(df, db):
    import sqlite3
    import pandas as pd
    print(f"Updating {db}")
    DATABASE='./db/db.sqlite3'
    #Convertir indices a columnas
    df=df.reset_index()
    if 'index' in df.columns:
        del df['index']
    # Eliminar duplicados del DataFrame
    df = df.drop_duplicates()    
    # Crear conexión a la base de datos
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    # Crear la tabla si no existe
    #2. Creamos la tabla db vacia si no existe
    columnas = df.columns.tolist()
    field_names=', '.join(columnas) #para generar los campos que requieren las consulta sql
    
    df.to_sql(db, con, if_exists='append', index=False)

    #Eliminamos duplicados:
    query = f"""
        DELETE FROM {db}
        WHERE rowid NOT IN (
        SELECT MIN(rowid)
        FROM {db}
        GROUP BY {field_names}
        );
    """
    cur.execute(query)
    # Confirmar la transacción
    con.execute("COMMIT;")
    # Cerrar la conexión
    con.close()
    print(f"Database {db} updated")
    return df

def tableTypes(db,table):
    import sqlite3

    # Conectar a la base de datos
    conn = sqlite3.connect(db)  # Reemplaza con el nombre de tu base de datos

    # Obtener los tipos de datos de la tabla
    cursor = conn.execute(f"c")
    column_info = cursor.fetchall()

    # Cerrar la conexión a la base de datos
    conn.close()

    # Imprimir los tipos de datos
    for column in column_info:
        print(f"Nombre de columna: {column[1]}, Tipo de dato: {column[2]}")


def delDuplicado(db,table):
    import sqlite3
    conn = sqlite3.connect(db)
    cursor = conn.cursor()
    cons=f'PRAGMA table_info({table});'
    cursor.execute(cons)
    res=cursor.fetchall()
    campos = [campo[1] for campo in res]
    # DELETE FROM CR6Irriwell1Router_tzs_Jsvpd
    #     WHERE ROWID NOT IN (
    #         SELECT MIN(ROWID)
    #         FROM CR6Irriwell1Router_tzs_Jsvpd
    #         GROUP BY timestamp, arbol, sup
    #     );
    consulta = f'''
        DELETE FROM {table}
        WHERE ROWID NOT IN (
            SELECT MIN(ROWID)
            FROM {table}
            GROUP BY {', '.join(campos)}
        )
    '''

    cursor.execute(consulta)
    conn.commit()
    conn.close()

def creadf():
    import pandas as pd
    import numpy as np
    import sqlite3

    # Generar datos aleatorios
    #datos_aleatorios = np.random.rand(4, 5)
    datos=[[1,2,3,4,5],[3]*5,[2]*5,[3]*5]
    # Crear DataFrame
    df = pd.DataFrame(datos, columns=['Columna1', 'Columna2', 'Columna3', 'Columna4', 'Columna5'])

    # Conectar a la base de datos (si no existe, se creará)
    conn = sqlite3.connect('mydb.db')

    # Guardar el DataFrame como una tabla en la base de datos
    df.to_sql('mytable', conn, if_exists='replace', index=False)

    # Cerrar la conexión
    conn.close()

    # Mostrar el DataFrame
    #print(df)
    #print(datos)
#creadf()
def leedb():
    import sqlite3
    import pandas as pd

    # Conectar a la base de datos SQLite
    conn = sqlite3.connect('db.sqlite3')  # Reemplaza con el nombre de tu base de datos

    # Ejecutar la consulta y obtener los resultados en un DataFrame
    #query = "SELECT rowid, * FROM CR6Irriwell1Router_tzs_Jsvpd WHERE timestamp='2022-07-09 05:30:00' AND arbol=1 AND sup=1 AND tz = 75.4;"
    query = "SELECT * FROM CR6Irriwell1Router_tzs_Jsvpd WHERE timestamp='2022-07-09 05:30:00' AND arbol=1 AND sup=1 AND tz = 75.4;"
    df = pd.read_sql_query(query, conn)

    # Cerrar la conexión a la base de datos
    conn.close()

    # Imprimir el DataFrame
    print(df)
    return df
# import sqlite3
# df= leedb()
# # Conectar a la base de datos (si no existe, se creará)
# conn = sqlite3.connect('mydb3.db')

# # Guardar el DataFrame como una tabla en la base de datos
# df.to_sql('mytable2', conn, if_exists='replace', index=False)

# # Cerrar la conexión
# conn.close()
# #delDuplicado('mydb3.db','mytable')
tableTypes('db.sqlite3','CR6Irriwell1Router_tzs_Jsvpd')