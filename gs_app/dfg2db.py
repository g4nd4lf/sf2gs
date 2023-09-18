
#FUNCIONES

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
    DATABASE='./db/db.sqlite3'
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
def obtiene_vpdypar(meteo_file):
    import pandas as pd
    #Leemos de la base de datos las medidas de meteo
    df=db2df(meteo_file)
    
    df=df.rename(columns={'vpd_avg': 'vpd'})
    df=df.rename(columns={'rad_par_avg': 'par'})
    #df=dfg[['tz','vpd']]
    meteo=df[['timestamp','vpd','par']]
    return meteo

#Función para leer datos de tz y meteo desde la base de datos,
#se agrupan y sincronizan y se limpian
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

def interpoleJs(df_Js_VPD,df_gs):
    import pandas as pd
    import numpy as np
    import matplotlib.pyplot as plt
    '''Esta función interpola los datos de Js/VPD de un dia a las hras de medida de gs.
    df_Js_VPD: dataframe con los datos de Js/VPD de un día, una estación, arbol y profundidad concretos.
    df_gs: dataframe con las medidas media de gs y su timestamp correspondiente al mismo dia de Js/VPD
    '''
    #INTERPOLAMOS, requiere varios pasos. Parece que para que la interpolación funcione bien
    #  hay que interpolar para cada día por separado y solo entre las fechas cercanas a las medidas
    #  del porómetro. Por tanto:
    # 1. Filtramos de todos los datos de Js_VPD los que correspondan a los dias y a las horas de medidas de gs
    # 2. Para cada dia, interpolamos para las horas de medida de gs
    dfj=df_Js_VPD.copy()
    #Eliminamos la columnas 'arbol' y 'sup' que nos estorban para los cálculos
    dfj=dfj.reset_index(level=['arbol','sup'], drop=True)
    dfj.index=pd.to_datetime(dfj.index)
    df_gs.set_index('timestamp', inplace=True)
    df_gs.index=pd.to_datetime(df_gs.index)
    inicio = df_gs.index[0] - pd.Timedelta(minutes=30)
    fin = df_gs.index[-1] + pd.Timedelta(minutes=30)
    # Filtrar el DataFrame 2 para quedarnos con los datos entre el primer y último valor existente en el DataFrame 1
    dfj_dia=dfj[(dfj.index>=inicio)& (dfj.index<=fin)]
    dfj_dia.index=pd.to_datetime(dfj_dia.index)
    gs_index=df_gs.index#pd.to_datetime(df_gs2_dia['timestamp'])
    dfj_index=dfj_dia.index
    gs_and_dfj_index = pd.concat([pd.Series(gs_index), pd.Series(dfj_index)]).sort_values()
    dfj2 = dfj_dia.reindex(gs_and_dfj_index.round("1s"))
    #print(dfj2)
    dfj2['Js_VPD'] = pd.to_numeric(dfj2['Js_VPD'])
    dfj2=dfj2.interpolate(method='time')#method='spline',order=3)
    dfj3=dfj2.reindex(gs_index.round("1s"))
    #print(dfj3)
    #df2_filtrado = df2_filtrado[(df2_filtrado.index >= primer_valor) & (df2_filtrado.index <= ultimo_valor)]
    #df = pd.concat([df, dfj3], ignore_index=False)
    #dfji=df_.copy()
    df_gs.index=df_gs.index.round('1s') #Para que coincidan los tiempos de ambos df hay que eliminar los milisegundos del timestamp
    newdf = pd.merge(dfj3, df_gs, on='timestamp', how='inner')
    #print(newdf)
    #r=regresion(newdf)
    return newdf

def regresion(df):
    import plotly.graph_objs as go
    from scipy import stats
    import numpy as np

    #x = [5.4,7,8,7,2,17,2,9,4,11,12,9,6]
    #y = [99.2,86,87,88,111,86,103,87,94,78,77,85,86]
    x=np.array(df['gsw'].values)
    y=np.array(df['Js_VPD'].values)
    slope, intercept, r, p, std_err = stats.linregress(x, y)
    r_squared=r**2
    line = slope*x+intercept
    if intercept >= 0:
        line_str = f"y = {slope:.2f}x + {intercept:.2f}, R^2 = {r_squared:.4f}"
    else:
        line_str = f"y = {slope:.2f}x - {abs(intercept):.2f}, R^2 = {r_squared:.4f}"

    # Creating the dataset, and generating the plot
    trace1 = go.Scatter(
                    x=x,
                    y=y,
                    mode='markers',
                    marker=go.Marker(color='rgb(255, 127, 14)'),
                    name='Data'
                    )

    trace2 = go.Scatter(
                    x=x,
                    y=line,
                    mode='lines',
                    marker=go.Marker(color='rgb(31, 119, 180)'),
                    name='Fit'
                    )
    if len(df)<=2:
        annotation = go.Annotation(
                        x=x[0],
                        y=y[0],
                        text=line_str,
                        showarrow=False,
                        font=go.Font(size=16)
                        )
    else:
        annotation = go.Annotation(
                        x=x[2],
                        y=y[2],
                        text=line_str,
                        showarrow=False,
                        font=go.Font(size=16)
                        )
    layout = go.Layout(
                    title='Js/VPD vs gs',
                    plot_bgcolor='rgb(229, 229, 229)',
                    xaxis=go.XAxis(zerolinecolor='rgb(255,255,255)', gridcolor='rgb(255,255,255)'),
                    yaxis=go.YAxis(zerolinecolor='rgb(255,255,255)', gridcolor='rgb(255,255,255)'),
                    annotations=[annotation]
                    )

    data = [trace1, trace2]
    fig = go.Figure(data=data, layout=layout)
    fig.update_xaxes(title_text="<b>gs</b>")
    fig.update_yaxes(title_text="<b>Js/VPD</b>")
    fig.update_layout(height=400,margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="LightSteelBlue")

    print({"slope":slope,"intercept":intercept,"r2":r*r,"p":p,"std_err":std_err})
    return(fig)