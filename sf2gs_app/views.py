import pandas as pd
import plotly.express as px
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
from django.shortcuts import render
from .dfg2db2 import crea_o_actualiza_tabla,lee_tablas, db2df, gs_days,irr2db, adapt_dfg, gs_days, obtiene_tzyvpd, calculaJs_VPD, irr2db, df2db, irr2db2
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
def download_view(request):
    if request.method == "POST":
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
       
        tz_table=station
        df_Js_VPD=db2df(tz_table+"_Jsvpd")
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
        df_filt=df_Js_VPD.query(datefilter).query(f"arbol=={tree} and sup=={int(not(thermocouple_depth))}")
        df_filt=df_filt.query(jsfilter).query(vpdfilter).query(parfilter)
        timestamps = pd.to_datetime(df_filt['timestamp'])
        df_filt['month'] = timestamps.dt.month
        df_filt['date'] = timestamps.dt.strftime('%d/%m/%Y')
        # Crea una columna 'time' con solo la hora (hora:minuto)
        df_filt['time'] = timestamps.dt.strftime('%H:%M')
        timefilter=f"((time>='{start_time}' and time<'{end_time}'))"
        df_filt=df_filt.query(timefilter)
        print(df_filt)
        # Generar el archivo CSV en memoria
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data.csv"'
        df_filt.to_csv(path_or_buf=response, index=False)    
        return response
    return JsonResponse({"error": "No file can be downloaded"}, status=400)
    
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
        #data= json.loads(request.body)
        print(start_date)
        print(end_date)
        #tz_tables=['CR6Irriwell1Router_tzs','CR6Irriwell2Meteo_tzs','CR6Irriwell3_tzs','CR6Irriwell4_tzs']
        s=TZ_TABLES.index(station)+1
        label=f"S{s}T{tree}d{thermocouple_depth}"
        
        time1_3=time.time()
        print("time1_3: ", time1_3)
        print("elpased1_3: ",time1_3-time1)
        #Jslimit=60
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
        datefilter=f"((timestamp>='{start_date[0]}') and (timestamp<='{end_date[0]}'))"
        df_Js_VPD["daterange"]=0
        df_Js_VPD.loc[(df_Js_VPD['timestamp'] >= start_date[0]) & (df_Js_VPD['timestamp'] <= end_date[0]), 'daterange'] = 0
        #df_Js_VPD.query(datefilter)["daterange"]=0
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
        
        # Crea una columna 'date' con solo la fecha (día/mes/año)
        df_filt.set_index('datetime', inplace=True)
        df_filt=df_filt.resample('30T').asfreq()
        #print(df_filt.head(50))
        # Generar el archivo CSV en memoria
        time1_6=time.time()
        print("time1_6: ", time1_6)
        print("elpased1_6: ",time1_6-time1)
        scatter1 = px.scatter(df_filt, x=vble_x, y=vble_to_plot, color="daterange", color_continuous_scale='viridis',
                    title="Js vs vpd")
        scatter1.update_traces(marker=dict(size=6, opacity=0.6), selector=dict(mode='markers'))
        fig = make_subplots(rows=1, cols=1,subplot_titles=[label],horizontal_spacing = 0.5,vertical_spacing=0.5)
        fig.update_layout(boxmode='overlay', width=800, height=500)
        fig.add_trace(scatter1['data'][0], row=1, col=1)
        fig.update_xaxes(title_text=label_x)
        fig.update_yaxes(title_text=label_vble_to_plot)
        fig.update_layout(coloraxis=dict(colorscale='viridis'), showlegend=True,paper_bgcolor='rgba(0,0,0,0)')
        #paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)'
        time1_7=time.time()
        print("time1_7: ", time1_7)
        print("elpased1_7: ",time1_7-time1)
        if vble_x=='timestamp':
            #fig.update_traces(selector=dict(type='scatter'), mode='lines')
            #fig.update_traces(line=dict(width=2))
            fig.update_traces(mode='lines')

            #fig.get_trace("my_trace").update_traces(line=dict(width=2), selector=dict(mode='lines+markers'))
        chart = fig.to_json()

        #####CHART2
        vble_x2='timestamp'
        scatter2 = px.scatter(df_filt, x=vble_x2, y=vble_to_plot2, color="daterange", color_continuous_scale='viridis',
                    title="")
        scatter2.update_traces(marker=dict(size=6, opacity=0.6), selector=dict(mode='markers'))
        fig2 = make_subplots(rows=1, cols=1,subplot_titles=[label],horizontal_spacing = 0.5,vertical_spacing=0.5)
        fig2.update_layout(boxmode='overlay', width=800, height=500)
        fig2.add_trace(scatter2['data'][0], row=1, col=1)
        fig2.update_xaxes(title_text=vble_x2)
        fig2.update_yaxes(title_text=vble_to_plot2)
        fig2.update_layout(coloraxis=dict(colorscale='viridis'), showlegend=True,paper_bgcolor='rgba(0,0,0,0)')
        fig2.update_traces(mode='lines')
        chart2 = fig2.to_json()
        response_data = {'chart': chart,'chart2': chart2}
        time2=time.time()
        print("End data proccess plot_view: ", time2)
        print("elpased: ",time2-time1)
        return JsonResponse(response_data)
    
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