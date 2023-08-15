import pandas as pd
import plotly.express as px
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
from django.shortcuts import render
from .dfg2db import crea_o_actualiza_tabla,lee_tablas, db2df, gs_days,irr2db, adapt_dfg, gs_days, obtiene_tzyvpd, calculaJs_VPD, irr2db, df2db, irr2db2
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go
import time
from django.http import JsonResponse

#from rest_framework import status

DBTABLE='gs_irriwell2023'
DATABASE='../db/db.sqlite3'
TZ_TABLES=['CR6Irriwell1Router_tzs','CR6Irriwell2Meteo_tzs','CR6Irriwell3_tzs','CR6Irriwell4_tzs']
METEO_TABLE='CR6Irriwell2Meteo_Met30'

#def index(request):
#    return render(request, "sf2gs_app/index2.html")
def updatedb(request):
    print("UPDATE DB OK!")
    #try:
    dfs=irr2db()
    for tz_table in TZ_TABLES:
        df_tz=obtiene_tzyvpd(tz_table,METEO_TABLE)
        df_Js_VPD=calculaJs_VPD(df_tz)
        df_Js_VPD2=df2db(df_Js_VPD,tz_table+"_Jsvpd")
    data = {'message': 'Success!'}         
#except:
    #    data = {'message': 'Error!'}   
    return JsonResponse(data)

def plot_view(request):
    if request.method == "POST":
        time1 = time.time()
        print("start_Time: ", time1)
        #meteo_table='CR6Irriwell2Meteo_Met30'
        body_unicode = request.body.decode('utf-8')
        data = json.loads(body_unicode)
        time1_2=time.time()
        print("time1_2: ", time1_2)
        print("elpased1_2: ",time1_2-time1)
        if type(data['start_date'])==type(""):
            start_date = data['start_date'].split("T")[0]
            end_date = data['end_date'].split("T")[0]
        else:
            start_date = data['start_date']['dateInstance'].split("T")[0]
            end_date = data['end_date']['dateInstance'].split("T")[0]
        station=data['station']
        tree=data['tree']
        thermocouple_depth=data['thermocouple_depth']
        #data= json.loads(request.body)
        print(start_date)
        #tz_tables=['CR6Irriwell1Router_tzs','CR6Irriwell2Meteo_tzs','CR6Irriwell3_tzs','CR6Irriwell4_tzs']
        s=TZ_TABLES.index(station)+1
        label=f"S{s}T{tree}d{thermocouple_depth}"
        fig = make_subplots(rows=1, cols=1,subplot_titles=[label],horizontal_spacing = 0.5,vertical_spacing=0.5)
        fig.update_layout(boxmode='overlay', width=800, height=500)
        time1_3=time.time()
        print("time1_3: ", time1_3)
        print("elpased1_3: ",time1_3-time1)
        Jslimit=60
        tz_table=station
        df_tz=obtiene_tzyvpd(tz_table,METEO_TABLE)
        time1_4=time.time()
        ##ATENCION, para optimizar, habria que reducir sobretodo el tiempo de:
        #  calculaJs_VPD(7seg)
        print("time1_4: ", time1_4)
        print("elpased1_4: ",time1_4-time1)
        #df_Js_VPD=calculaJs_VPD(df_tz)
        df_Js_VPD=db2df(tz_table+"_Jsvpd")
        #df_Js_VPD["timestamp"]=pd.to_datetime(df_Js_VPD["timestamp"])
        time1_5=time.time()
        print("time1_5: ", time1_5)
        print("elpased1_5: ",time1_5-time1)
        #dfmar=df_Js_VPD.query("timestamp>='2023-03-01'").query(f"arbol=={tree} and Js<={Jslimit} and sup=={int(not(thermocouple_depth))}")
        dfmar=df_Js_VPD.query(f"timestamp>='{start_date}'").query(f"timestamp<='{end_date}'").query(f"arbol=={tree} and Js<={Jslimit} and sup=={int(not(thermocouple_depth))}")
        timestamps = pd.to_datetime(dfmar['timestamp'])
        dfmar['month'] = timestamps.dt.month
        time1_6=time.time()
        print("time1_6: ", time1_6)
        print("elpased1_6: ",time1_6-time1)
        scatter1 = px.scatter(dfmar, x="vpd", y="Js", color="month", color_continuous_scale='viridis',
                    title="Js vs vpd")
        scatter1.update_traces(marker=dict(size=6, opacity=0.6), selector=dict(mode='markers'))
        fig.add_trace(scatter1['data'][0], row=1, col=1)
        fig.update_xaxes(title_text="VPD")
        fig.update_yaxes(title_text="Js")
        time1_7=time.time()
        print("time1_7: ", time1_7)
        print("elpased1_7: ",time1_7-time1)
        chart = fig.to_json()
        response_data = {'chart': chart}
        time2=time.time()
        print("End data proccess plot_view: ", time2)
        print("elpased: ",time2-time1)
        return JsonResponse(response_data)
    
def index_pru(request):
    #Ejemplo de como enviar graficas

    data = {
        "Poblacion": [8175133, 3792621, 2695598, 2100263, 1445632],
        "Ciudad": ["Nueva York", "Los Ángeles", "Chicago", "Houston", "Phoenix"]
    }
    df = pd.DataFrame(data)

    # Crear la gráfica de barras interactiva con Plotly
    fig = px.bar(df, x='Ciudad', y='Poblacion', title='Población por Ciudad')

    data2 = [{"x": [1, 2, 3, 4, 5], 
              "y": [10, 11, 12, 13, 14], 
              "type": 'scatter', 
              "mode": 'lines+markers',
                "name": 'Línea 1'}]
    layout = {
            "title": "Gráfica Interactiva",
            "xaxis": {
                "title": "Eje X"
            },
            "yaxis": {
                "title": "Eje Y"
            }
        }
    chart = fig.to_json()
    return render(request, 'sf2gs_app/index.html', 
                  {"data": chart, "data2":json.dumps(data2), 
                   "layout":json.dumps(layout)})

def index(request):
    alltables=lee_tablas()
    print("tablas:")
    print(alltables)
    #return HttpResponse(alltables)
    #Calculamos el rango de nuestros datos
    alldates=set()
    tz_tables=[t for t in alltables if (("_tzs" in t) and ("_Jsvpd" not in t))]
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
        print(first," - ",last)
        #gs:
    df=db2df(DBTABLE)
    gsdays=gs_days(df)
    print(gsdays)
    fstations=[{"str":t} for t in tz_tables]
    fdays=[{"str":d} for d in gsdays]
    rangedate={"start":first,"end":last}
    #for t in tablas:
    #    tz=db2df(tablas)
    return render(request, 'sf2gs_app/index.html', 
                  {"gsdays": fdays, "stations":fstations, "rangedate":rangedate}
                )

def upload_file(request):
    import io, re
    if request.method == "POST": #and request.FILES.getlist("files"):
        #files = request.FILES.getlist("files")
        files = request.FILES.getlist("files")
        sheets=[]
        if files:
            # Process each uploaded file (read binary content)
            dfs = []
            for file in files:
                # Process each uploaded file
                content = file.read()  # Read the binary content of the file
                
                # Here you can process 'content', e.g., parse Excel content using libraries
                # Example:
                myexcelfile=io.BytesIO(content)
                xl = pd.ExcelFile(myexcelfile,engine='openpyxl')
                all_sheets=xl.sheet_names  # see all sheet names
                date_pattern = r'\d{2}\.\d{2}\.\d{4}'  # Patrón de fecha (dd.mm.yyyy)                
                sheets = [item for item in all_sheets if re.search(date_pattern, item) and len(item)==10]
                #print(sheets)
                for sheet in sheets:
                    print(sheet)
                    df=pd.read_excel(myexcelfile,sheet_name=sheet,skiprows=[1],usecols=range(38))
                    df=adapt_dfg(df,sheet)
                    crea_o_actualiza_tabla(DBTABLE,df)
    
                #df = pd.read_excel(io.BytesIO(content),sheet_name=0,engine='openpyxl')
                #dfs.append(df)#.to_dict())
                print(df)
                # You'll need to adjust this part based on your exact requirements
                
                # For demonstration purposes, let's just collect the filenames
                #results.append(file.name)
                print(file.name)
        #results = [df.to_json(orient='records') for df in dfs]            
        #return JsonResponse({"results": df.to_json(orient='records')})
        response_data = {'measurement_dats': sheets}
        return JsonResponse(response_data)
    else:
        return JsonResponse({"error": "No files were uploaded"}, status=400)
    
def upload_index(request):
    
    df=db2df(DBTABLE)
    print(df)
    tz_vpd=irr2db()
    print(tz_vpd)
    days=gs_days(df)
    fdays =[{"daytime":day.strftime('%d/%m/%Y'),"str":day.strftime('%d/%m/%Y')} for day in days]
    tables=list(tz_vpd.keys())
    tables.append(DBTABLE)
    ftables=[{"table":t,"str":t} for t in tables]
    print(fdays)
    return render(request, "sf2gs_app/upload_index.html",{ "days": fdays,"tables":ftables})