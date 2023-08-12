
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

def obtiene_tzyvpd(tz_file,meteo_file):
    import pandas as pd
    #Leemos de la base de datos las medidas de tz y meteo
    tzs_i1=db2df(tz_file)
    meteo=db2df(meteo_file)
    
    # unimos los dos conjuntos de datos haciendo coincidir los timestamps
    df = pd.merge(tzs_i1, meteo, on='timestamp', how='inner')
    
    #Vamos a expandir el dataframe, porque no quiero los tzs como columnas diferentes en una misma fila
    #sino que cada uno tenga su propia fila y un valor de 'arbol' y 'sup' que defina que termopar concreto es
    #Primero se definen las columnas que no van a modfiicarse, osea aquellas que no contengan 'tz' en su nombre
    cols_nochange=[x for x in df.columns if 'tz' not in x]
    #Usamos la funcion melt para expandir las columnas con tz
    df = df.melt(id_vars=cols_nochange,
                 var_name='tz_label',
                 value_name='tz')
    #así defino la correspondencia entre cada etiqueta y el (arbol,termopar) que representan
    #sup=1 para el termopar más superficial y sup=0 para el menos superficial
    #(revisar en campo que esto coincide con el orden de medida en el datalogger de cada termopar)
    tr={'tz1_1_':(1,1),'tz1_2_':(1,0),'tz1_3_':(2,1),'tz1_4_':(2,0)}
    arbol=[tr[x][0] for x in df['tz_label']]
    sup=[tr[x][1] for x in df['tz_label']]
    #df2=df.copy()
    df['arbol']=arbol
    df['sup']=sup
    #df.head()
    #Agrupamos, haciendo media, por timestamp, arbol y termopar. 
    #Como solo hay un valor en el que coincidan estos 3 parametros la media es irrelevante
    dfg=df.groupby(['timestamp', 'arbol','sup']).mean(numeric_only=True)
    dfg=dfg.rename(columns={'vpd_avg': 'vpd'})
    dfg=dfg.rename(columns={'rad_par_avg': 'par'})
    #df=dfg[['tz','vpd']]
    df=dfg[['tz','vpd','par']]
    return df
    
#Calculamos Js/VPD:
def calculaJs_VPD(df):
    import pandas as pd
    def tz2Js(tz):
        a_0=-0.5984
        a_1=1.4873
        a_2=0.054
        #wood parameters
        Fwood= 0.381877421946182#0.156 #Fraction_wood
        Fwat= 0.343890128864018#0.756 #Fraction_water
        FactorX=0.441
        Vc2J=FactorX*Fwood+Fwat #0.824796
    
        #Heat pulse velocity (cm/h)
        hpv=3600*(1-0.5)/(2*tz)
        #Corrected heat pulse velocity (cm/h)
        hpvc=a_0+a_1*hpv+a_2*hpv**2
        Js=hpvc*Vc2J
        return(Js)
    df['Js'] = df.apply(lambda row: tz2Js(row['tz']), axis=1)
    df['Js_VPD'] = df.apply(lambda row: tz2Js(row['tz']) / row['vpd'] if row['vpd']>0.01 else pd.NA, axis=1)
    
    df=df.dropna()
    return df