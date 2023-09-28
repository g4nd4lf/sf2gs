import pandas as pd
import plotly.express as px
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
from django.shortcuts import render
from .dfg2db2 import crea_o_actualiza_tabla, db2df, gs_days,irr2db, adapt_dfg, gs_days, obtiene_tzyvpd, \
            calculaJs_VPD, irr2db, df2db, getRangeDateAndStations_tz, createFig, readParameters

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

        #READ parameters
        start_date, end_date, start_time, end_time, station, tree, thermocouple_depth, vpd_range, par_range,js_range, vble_to_plot, label_vble_to_plot, vble_x, label_x, vble_to_plot2 = readParameters(request)

        s=TZ_TABLES.index(station)+1
        label=f"S{s}T{tree}d{thermocouple_depth}"
        
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
        ###CHART1:
        
        #Create Charts:
        linemode=False
        if vble_x=='timestamp':
            linemode=True
        chart=createFig(df_filt,vble_x,label_x,vble_to_plot,label_vble_to_plot,label,linemode)
        vble_x2='timestamp'
        chart2=createFig(df_filt,vble_x2,vble_x2,vble_to_plot2,vble_to_plot2,label,True)

        response_data = {'chart': chart,'chart2': chart2}
        return JsonResponse(response_data)
        
def index(request):
    #Find stations and range dates for tz measurements from DB:
    firstday,lastday, stations = getRangeDateAndStations_tz() #tzs
    rangedate={"start":firstday,"end":lastday}
    return render(request, 'sf2gs_app/index.html', {"stations":stations, "rangedate":rangedate})

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