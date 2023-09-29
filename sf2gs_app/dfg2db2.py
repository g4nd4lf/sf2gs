import pandas as pd

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
        df2db(dfs[i],data_table)       
    return tzs_y_meteo

def irr2db2():
    import pandas as pd
    '''función que descarga del servidor los datos de tzs y meteo de irriwell, actualiza la base de datos y los devuelve en forma de diccionario'''
    from base64 import b64encode
    urlbase='http://gruporec.csic.es/Irriwell/Datos/'
    urlfiles=['CR6Irriwell1Router_tzs.dat','CR6Irriwell2Meteo_tzs.dat','CR6Irriwell3_tzs.dat','CR6Irriwell4_tzs.dat','CR6Irriwell2Meteo_Met30.dat']
    urls=[urlbase+x for x in urlfiles]
    dfs=[]
    for url in [urls[0]]:
        df = pd.read_csv(url, storage_options={'Authorization': b'Basic %s' % b64encode(b'gruporec:estoma')},skiprows=[0,2,3])
        df['TIMESTAMP']= pd.to_datetime(df['TIMESTAMP'], format='%Y-%m-%d %H:%M:%S')
        df['TIMESTAMP']= df['TIMESTAMP'].round('30min')
        dfs.append(df)
    tzs_y_meteo={}
    for i in range(len([urlfiles[0]])):
        data_table=urlfiles[i].replace(".dat","")
        tzs_y_meteo[data_table]=dfs[i]
        #Esto es necesario para que las querys de SQL no den problemas ccon caracteres especiales:
        dfs[i].columns=dfs[i].columns.str.lower()
        dfs[i].columns=dfs[i].columns.str.replace("[.()]",'_',regex='True')  
        crea_o_actualiza_tabla(data_table,dfs[i])       
    return tzs_y_meteo
def df2db2(df, db):
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
    #filter_columns=
    field_names=', '.join(columnas) #para generar los campos que requieren las consulta sql
    
    #min_field_names = ", ".join([f"MIN({col})" for col in columnas])
    placeholders = ', '.join(['?'] * len(columnas))
    
    if db not in lee_tablas():
        #index_and_fields='id INTEGER PRIMARY KEY AUTOINCREMENT, '+field_names
        consulta = f"CREATE TABLE {db} ({field_names});"
        print(consulta)
        cur.execute(consulta)
    
    insert_query = f"INSERT INTO {db} VALUES ({placeholders})"
    # Iniciar una transacción
    con.execute("BEGIN TRANSACTION;")
    for _, row in df.iterrows():
        #row['timestamp']=row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(row['timestamp'], pd.Timestamp):
            row['timestamp']=row['timestamp'].strftime("%Y-%m-%d %H:%M:%S")
        cur.execute(insert_query, tuple(row))        
    # Confirmar la transacción
    con.execute("COMMIT;")
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

def crea_o_actualiza_tabla(db, df):
    import sqlite3
    from datetime import datetime
    DATABASE='./db/db.sqlite3'
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
    import os
    DATABASE='./db/db.sqlite3'
    DATABASE_ABSOLUTE = os.path.abspath(DATABASE)
    #print("Ruta absoluta de la base de datos:", DATABASE_ABSOLUTE)
    # Obtén el directorio actual
    directorio_actual = os.getcwd()
    #print(directorio_actual)
    # Lista los archivos en el directorio actual
    archivos = os.listdir(directorio_actual)
    archivos.append(DATABASE_ABSOLUTE)
    # Filtra solo los archivos (excluyendo directorios)
    #archivos = [archivo for archivo in archivos if os.path.isfile(os.path.join(directorio_actual, archivo))]

    #Para leer las tablas de la base de datos
    con = sqlite3.connect(DATABASE)
    sql_query="SELECT name FROM sqlite_master WHERE type='table';"
    res = con.execute(sql_query)
    #Hay que añadir lo siguiente porque res.fetchall() devuelve un array de tuplas, no un array de nombres de tablas. Solo nos interesa el primer elemento de cada tupla, que es el nombre de la tabla
    tables = [row[0] for row in res.fetchall()] 
    con.close()
    #tables=[DATABASE_ABSOLUTE,"dos"]
    #tables=archivos
    return(tables)

def db2df(table):
    import sqlite3
    import pandas as pd
    '''Function to read a table from the db and print the resulting df'''
    DATABASE='./db/db.sqlite3'
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

# def lee_tablas():
#     import sqlite3
#     #Para leer las tablas de la base de datos
#     DATABASE='../db.sqlite3'
#     con = sqlite3.connect(DATABASE)
#     sql_query="SELECT name FROM sqlite_master WHERE type='table';"
#     res = con.execute(sql_query)
#     #Hay que añadir lo siguiente porque res.fetchall() devuelve un array de tuplas, no un array de nombres de tablas. Solo nos interesa el primer elemento de cada tupla, que es el nombre de la tabla
#     tables = [row[0] for row in res.fetchall()] 
#     con.close()
#     return(tables)

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

def obtiene_vpdypar(meteo_file):
    import pandas as pd
    #Leemos de la base de datos las medidas de meteo
    df=db2df(meteo_file)
    
    df=df.rename(columns={'vpd_avg': 'vpd'})
    df=df.rename(columns={'rad_par_avg': 'par'})
    #df=dfg[['tz','vpd']]
    meteo=df[['vpd','par']]
    return meteo

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

def roundbox2023(gs_table,station,tree,tree_zone='ALL',delta_gmt=2):
    '''  To calculate the avergage of each round of measurments of gs. 
    During every round several repetitions (leaves) of gs are measured in each tree. Every round is splitted asuming 
    a time span higher than 500 seconds between measurements in the same tree.
    The return of this function is a dataframe keeping the avearage of all the repetitions of each tree.
    '''
    import pandas as pd
    #tree_zone='DCHA' if tree_zone=='RIGHT' else 'IZDA' #data in DB is labeled in spanish: 'DCHA'=Right and 'IZDA'=Left
    dfg0=db2df(gs_table)
    #Convert date to GMT:
    dfg0['timestamp']=pd.to_datetime(dfg0['timestamp'])-pd.Timedelta(hours=delta_gmt)
    #dfg=dfg0.query(f"irriwell=={station} and arbol=={tree} and parte_arbol=='{tree_zone}'")[["timestamp","gsw"]]
    if tree_zone=='ALL':
        dfg=dfg0.query(f"irriwell=={station} and arbol=={tree}")[["timestamp","gsw"]] 
    else:
        if tree_zone=='RIGHT':
            tree_zone='DCHA'
        else:
            tree_zone='IZDA'
        dfg=dfg0.query(f"irriwell=={station} and arbol=={tree} and parte_arbol=='{tree_zone}'")[["timestamp","gsw"]] 

    dfg=dfg.reset_index(drop=True)
    #Every round is splitted asuming a time span higher than 500 seconds between measurements in the same tree.
    dfg['date_time'] = pd.to_datetime(dfg['timestamp'])
    dfg['timediff'] = dfg['date_time'].diff()
    dfg.loc[0,'timediff']=dfg.loc[1,'timediff']*0
    mask = dfg['timediff'] > pd.Timedelta(seconds=500)
    dfg['round'] = mask.cumsum()
    #dfg = dfg.drop(['timediff', 'date_time'], axis=1)
    #rounds = dfg.groupby('round').mean()
    #rounds.set_index('timestamp', inplace=True)
    return dfg

def getRangeDateAndStations_tz():
    '''Get date range of tz measurements (from when and to when data were collected)
       and the stations installed (dataloggers) to fill the menus that allows the
       user to filter for range or station.
    '''
    #Read all tables from DB
    alltables=lee_tablas()
    #Find the stations
    tz_tables=[t for t in alltables if (("_tzs" in t) and ("_Jsvpd" not in t))]
    #Find date range from tz tables:
    alldates=set()
    first="no data"
    last="no data"
    if len(tz_tables)>0:
        for table in tz_tables:
            df=db2df(table)
            if not df.empty:
                mydates=pd.to_datetime(df['timestamp']).sort_values()
                first=mydates[0]
                last=mydates.iloc[-1]
                alldates.add(first)
                alldates.add(last)
        first=min(alldates).strftime('%Y-%m-%d')
        last=max(alldates).strftime('%Y-%m-%d')
    return first,last,tz_tables

def createFig(df,vble_x,label_x,vble_y,label_y,title,linemode):
            import plotly.express as px
            from plotly.subplots import make_subplots
            scatter1 = px.scatter(df, x=vble_x, y=vble_y, color="daterange", color_continuous_scale='viridis',
                    title="Js vs vpd")
            scatter1.update_traces(marker=dict(size=6, opacity=0.6), selector=dict(mode='markers'))
            fig = make_subplots(rows=1, cols=1,subplot_titles=[title],horizontal_spacing = 0.5,vertical_spacing=0.5)
            fig.update_layout(boxmode='overlay', width=800, height=500)
            fig.add_trace(scatter1['data'][0], row=1, col=1)
            fig.update_xaxes(title_text=label_x)
            fig.update_yaxes(title_text=label_y)
            fig.update_layout(coloraxis=dict(colorscale='viridis'), showlegend=True,paper_bgcolor='rgba(0,0,0,0)')
            if linemode:
                fig.update_traces(mode='lines')
            chart = fig.to_json()
            return chart

def readParameters(request):
    import json
    body_unicode = request.body.decode('utf-8')
    data = json.loads(body_unicode)
    
    start_date=[]
    for date in data['start_date']:
        if type(date)==type(""):
            start_date.append(date.split("T")[0])
        else:
            start_date.append(date['dateInstance'].split("T")[0])
    end_date=[]
    for date in data['end_date']:
        if type(date)==type(""):
            end_date.append(date.split("T")[0])
        else:
            end_date.append(date['dateInstance'].split("T")[0])
    start_time=data['start_time']
    end_time=data['end_time']
    station=data['station']
    tree=data['tree']
    thermocouple_depth=data['thermocouple_depth']
    vpd_range=data['vpd_range']
    par_range=data['par_range']
    js_range=data['js_range']
    vble_to_plot="Js"
    label_vble_to_plot="Js"
    vble_x="vpd"
    label_x="VPD"
    if request.path=='/sf2gs/plot':
        if data['vble_to_plot']=="Js_vpd":
            vble_to_plot="Js_VPD"
            label_vble_to_plot="Js/VPD"
        elif data['vble_to_plot']=="Js_vs_t":
            vble_to_plot="Js"
            label_vble_to_plot="Js"
            vble_x="timestamp"
            label_x="timestamp"
        elif data['vble_to_plot']=="Js_vpd_vs_t":
            vble_to_plot="Js_VPD"
            label_vble_to_plot="Js/VPD"
            vble_x="timestamp"
            label_x="timestamp"
        vble_to_plot2="vpd"
        if data['vble_to_plot2']=="vpd_vs_time":
            vble_to_plot2="vpd"
        elif data['vble_to_plot2']=="par_vs_time":
            vble_to_plot2="par"
        return start_date, end_date, start_time, end_time, station, tree, thermocouple_depth, vpd_range, par_range,js_range, vble_to_plot, label_vble_to_plot, vble_x, label_x, vble_to_plot2
    else:
        return start_date, end_date, start_time, end_time, station, tree, thermocouple_depth, vpd_range, par_range,js_range

def filter_Js_VPD(df_Js_VPD,start_date,end_date,start_time,end_time,js_range,vpd_range,par_range,tree,thermocouple_depth):
            datefilter=f"((timestamp>='{start_date[0]}') and (timestamp<='{end_date[0]}'))"
            df_Js_VPD["daterange"]=0
            df_Js_VPD.loc[(df_Js_VPD['timestamp'] >= start_date[0]) & (df_Js_VPD['timestamp'] <= end_date[0]), 'daterange'] = 0
            for i in range(1,len(start_date)):
                newDateFilter=f"((timestamp>='{start_date[i]}') and (timestamp<='{end_date[i]}'))"
                df_Js_VPD.loc[(df_Js_VPD['timestamp'] >= start_date[i]) & (df_Js_VPD['timestamp'] <= end_date[i]), 'daterange'] = i
                datefilter+=" or "+newDateFilter
            jsfilter=f"(Js>={js_range[0]} and Js<={js_range[1]})"
            vpdfilter=f"(vpd>={vpd_range[0]} and vpd<={vpd_range[1]})"
            parfilter=f"(par>={par_range[0]} and par<={par_range[1]})"
            df_filt=df_Js_VPD.query(datefilter).query(f"arbol=={tree} and sup=={int(not(int(thermocouple_depth)))}")
            df_filt=df_filt.query(jsfilter).query(vpdfilter).query(parfilter)
            
            timestamps = pd.to_datetime(df_filt['timestamp'])
            df_filt['datetime']= pd.to_datetime(df_filt['timestamp'])
            df_filt['month'] = timestamps.dt.month
            
            df_filt['time'] = timestamps.dt.strftime('%H:%M')
            timefilter=f"((time>='{start_time}' and time<'{end_time}'))"
            df_filt=df_filt.query(timefilter)
            return df_filt