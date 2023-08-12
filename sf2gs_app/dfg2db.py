
def irr2dic():
    import pandas as pd
    '''función que descarga del servidor los datos de tzs y meteo de irriwell y los guarda en dataframes'''
    from base64 import b64encode
    urlbase='http://gruporec.csic.es/Irriwell/Datos/'
    urlfiles=['CR6Irriwell1Router_tzs.dat','CR6Irriwell2Meteo_tzs.dat','CR6Irriwell3_tzs.dat','CR6Irriwell4_tzs.dat','CR6Irriwell2Meteo_Met30.dat']
    urls=[urlbase+x for x in urlfiles]
    dfs=[]
    for url in urls:
        df = pd.read_csv(url, storage_options={'Authorization': b'Basic %s' % b64encode(b'gruporec:estoma')},skiprows=[0,2,3])
        df['TIMESTAMP']= pd.to_datetime(df['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
        df['TIMESTAMP']= df['TIMESTAMP'].round('30min')
        dfs.append(df)
    tzs_y_meteo={}
    for i in range(len(urlfiles)):
        tzs_y_meteo[urlfiles[i].replace(".dat","")]=dfs[i]
    return tzs_y_meteo

def irr2db():
    import pandas as pd
    '''función que descarga del servidor los datos de tzs y meteo de irriwell, actualiza la base de datos y los devuelve en forma de diccionario'''
    from base64 import b64encode
    urlbase='http://gruporec.csic.es/Irriwell/Datos/'
    urlfiles=['CR6Irriwell1Router_tzs.dat','CR6Irriwell2Meteo_tzs.dat','CR6Irriwell3_tzs.dat','CR6Irriwell4_tzs.dat','CR6Irriwell2Meteo_Met30.dat']
    urls=[urlbase+x for x in urlfiles]
    dfs=[]
    for url in urls:
        df = pd.read_csv(url, storage_options={'Authorization': b'Basic %s' % b64encode(b'gruporec:estoma')},skiprows=[0,2,3])
        df['TIMESTAMP']= pd.to_datetime(df['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
        df['TIMESTAMP']= df['TIMESTAMP'].round('30min')
        dfs.append(df)
    tzs_y_meteo={}
    for i in range(len(urlfiles)):
        data_table=urlfiles[i].replace(".dat","")
        tzs_y_meteo[data_table]=dfs[i]
        #Esto es necesario para que las querys de SQL no den problemas ccon caracteres especiales:
        dfs[i].columns=dfs[i].columns.str.lower()
        dfs[i].columns=dfs[i].columns.str.replace("[.()]",'_',regex='True')  
        crea_o_actualiza_tabla(data_table,dfs[i])       
    return tzs_y_meteo

def crea_o_actualiza_tabla(db, df):
    import sqlite3
    from datetime import datetime
    DATABASE='../db.sqlite3'
    # Eliminar duplicados del DataFrame
    df = df.drop_duplicates()    
    # Crear conexión a la base de datos
    con = sqlite3.connect(DATABASE)
    cur = con.cursor()
    
    # Crear la tabla si no existe
    #2. Creamos la tabla db vacia si no existe
    columnas = df.columns.tolist()
    field_names=', '.join(columnas) #para generar los campos que requieren las consulta sql
    if db not in lee_tablas():
        consulta = f"CREATE TABLE {db} ({field_names});"
        print(consulta)
        cur.execute(consulta)
    placeholders = ', '.join(['?'] * len(df.columns))
    insert_query = f"INSERT INTO {db} VALUES ({placeholders})"
    # Iniciar una transacción
    con.execute("BEGIN TRANSACTION;")
    for _, row in df.iterrows():
        row['timestamp']=row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(insert_query, tuple(row))        
    # Confirmar la transacción
    con.execute("COMMIT;")
    cur.execute(f"DELETE FROM {db} WHERE rowid NOT IN (SELECT MIN(rowid) FROM {db} GROUP BY timestamp);")
    # Confirmar la transacción
    con.execute("COMMIT;")
    # Cerrar la conexión
    con.close()

def lee_tablas():
    import sqlite3
    DATABASE='../db.sqlite3'
    #Para leer las tablas de la base de datos
    con = sqlite3.connect(DATABASE)
    sql_query="SELECT name FROM sqlite_master WHERE type='table';"
    res = con.execute(sql_query)
    #Hay que añadir lo siguiente porque res.fetchall() devuelve un array de tuplas, no un array de nombres de tablas. Solo nos interesa el primer elemento de cada tupla, que es el nombre de la tabla
    tables = [row[0] for row in res.fetchall()] 
    con.close()
    return(tables)

def db2df(table):
    import sqlite3
    import pandas as pd
    '''Function to read a table from the db and print the resulting df'''
    DATABASE='../db.sqlite3'
    con = sqlite3.connect(DATABASE)
    sql_query = "SELECT * FROM '"+table+"';"
    df = pd.read_sql(sql_query, con)
    con.close()
    return df

def gs_days(df_gs):
    import numpy as np
    import pandas as pd
    if type(df_gs.index)==pd.RangeIndex: #if timestamp is a column in the dataframe
        df_gs['timestamp']=pd.to_datetime(df_gs['timestamp'])
        df_gs.set_index('timestamp', inplace=True)
    gs_days = np.unique(df_gs.index.date) 
    return(gs_days)

def adapt_dfg(dfg,date):
    import unicodedata
    import pandas as pd
    dfg.columns = [unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode().lower() for col in dfg.columns]
    #eliminamos espacios
    dfg.columns=[x.replace(' ','_') for x in dfg.columns]
    #eliminamos almohadilla
    dfg.columns=[x.replace('#','_num') for x in dfg.columns]
    #eliminamos puntos, barra inclinada y comilla
    dfg.columns=[x.replace('.','_').replace('/','_').replace("'",'_') for x in dfg.columns]
    # Eliminar las columnas duplicadas de forma sucinta y eficiente
    dfg = dfg.loc[:, ~dfg.columns.duplicated()]    
    #Para crear la columna 'timestamp' con fecha y hora:
    dfg['time']=pd.to_datetime(dfg['time'], format='%H:%M:%S')#.round("30min") esta parte mejor no hacerla para no perder info
    dfg['date']=pd.to_datetime(date, format='%d.%m.%Y')
    # Combina la fecha y la hora en un solo objeto datetime
    dfg['timestamp'] = dfg['date'].dt.strftime('%Y-%m-%d') + ' ' + dfg['time'].dt.strftime('%H:%M:%S')
    dfg['timestamp']=pd.to_datetime(dfg['timestamp'])
    dfg = dfg.drop('time', axis=1)
    dfg = dfg.drop('date', axis=1)
    #Eliminamos las filas vacias (las que tienen NaT en la columna de timestamp)
    dfg = dfg.dropna(subset=['timestamp']).reset_index(drop=True)
    return(dfg)

def lee_tablas():
    import sqlite3
    #Para leer las tablas de la base de datos
    DATABASE='../db.sqlite3'
    con = sqlite3.connect(DATABASE)
    sql_query="SELECT name FROM sqlite_master WHERE type='table';"
    res = con.execute(sql_query)
    #Hay que añadir lo siguiente porque res.fetchall() devuelve un array de tuplas, no un array de nombres de tablas. Solo nos interesa el primer elemento de cada tupla, que es el nombre de la tabla
    tables = [row[0] for row in res.fetchall()] 
    con.close()
    return(tables)