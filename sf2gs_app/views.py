import pandas as pd
import plotly.express as px
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
import json
from django.shortcuts import render
from .dfg2db import crea_o_actualiza_tabla,lee_tablas, db2df, gs_days,irr2db, adapt_dfg, gs_days

DBTABLE='gs_irriwell2023'
DATABASE='../db.sqlite3'
#def index(request):
#    return render(request, "sf2gs_app/index2.html")
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
    #Calculamos el rango de nuestros datos
    alldates=set()
    tz_tables=[t for t in alltables if "_tzs" in t]
    for table in tz_tables:
        df=db2df(table)
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