import pandas as pd
import plotly.express as px
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
from django.shortcuts import render
from .dfg2db2 import crea_o_actualiza_tabla, db2df, gs_days,irr2db, adapt_dfg, gs_days, obtiene_tzyvpd, \
            calculaJs_VPD, irr2db, df2db, getRangeDateAndStations_tz, createFig, readParameters, filter_Js_VPD

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
        #READ parameters
        start_date, end_date, start_time, end_time, station, tree, thermocouple_depth, vpd_range, par_range,js_range = readParameters(request)

        #Read data from DB
        tz_table=station
        df_Js_VPD=db2df(tz_table+"_Jsvpd")
        
        #Filter data:
        df_filt = filter_Js_VPD(df_Js_VPD,start_date,end_date,start_time,end_time,js_range,vpd_range,par_range,tree,thermocouple_depth)
        
        # Generate csv file to be downloaded
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="data.csv"'
        df_filt.to_csv(path_or_buf=response, index=False)    
        return response
    return JsonResponse({"error": "No file can be downloaded"}, status=400)
    
def plot_view(request):
    if request.method == "POST":

        #READ parameters
        start_date, end_date, start_time, end_time, station, tree, thermocouple_depth, vpd_range, par_range,js_range, vble_to_plot, label_vble_to_plot, vble_x, label_x, vble_to_plot2 = readParameters(request)

        #Read data from DB
        tz_table=station
        df_Js_VPD=db2df(tz_table+"_Jsvpd")
        
        #Filter data:
        df_filt = filter_Js_VPD(df_Js_VPD,start_date,end_date,start_time,end_time,js_range,vpd_range,par_range,tree,thermocouple_depth)
        
        # Use datetime column as index and round times to x:00:00 or x:30:00
        #df_filt.set_index('datetime', inplace=True)
        #df_filt=df_filt.resample('30T').asfreq()
        
        #Create Charts:
        s=TZ_TABLES.index(station)+1
        fig_title=f"S{s}T{tree}d{thermocouple_depth}"
        linemode=False
        if vble_x=='timestamp':
            linemode=True
        chart=createFig(df_filt,vble_x,label_x,vble_to_plot,label_vble_to_plot,fig_title,linemode)
        vble_x2='timestamp'
        chart2=createFig(df_filt,vble_x2,vble_x2,vble_to_plot2,vble_to_plot2,fig_title,True)

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