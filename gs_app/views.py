from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse

from django.http import HttpResponseRedirect
from django.urls import reverse
import json
import pandas as pd
import io
import re
import unicodedata
from .dfg2db import crea_o_actualiza3,lee_tablas, db2df, gs_days

DBTABLE='gs_irriwell2023'
DATABASE='../db.sqlite3'

def adapt_dfg(dfg,date):
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

def upload_view(request):
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
                    crea_o_actualiza3(DBTABLE,df)
    
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
        
def read_gs(request):
    body_data = request.body.decode('utf-8')  # Decodificar los bytes en una cadena
    json_data = json.loads(body_data)
    print("day: ",json_data['day'])
    #return (HttpResponse(json_data['day']))
    response=JsonResponse(json_data)
    return HttpResponse(response)
    
def index(request):
    
    df=db2df(DBTABLE)
    print(df)
    days=gs_days(df)
    fdays =[{"daytime":day.strftime('%d/%m/%Y'),"str":day.strftime('%d/%m/%Y')} for day in days]
    print(fdays)
    return render(request, "gs_app/index.html",{ "days": fdays})