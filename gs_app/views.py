from django.shortcuts import render
from django.http import Http404, HttpResponse, JsonResponse

from django.http import HttpResponseRedirect
from django.urls import reverse
import json
import pandas as pd
import io
import re
import unicodedata
from .dfg2db import crea_o_actualiza_tabla,lee_tablas, db2df, gs_days, adapt_dfg
from .dfg2db import obtiene_vpdypar, obtiene_tzyvpd,calculaJs_VPD,calculaJs_VPD,interpoleJs,regresion, roundbox2023
import scipy.stats as st
#st.i
DBTABLE='gs_irriwell2023'
DATABASE='./db/db.sqlite3'
METEO_TABLE='CR6Irriwell2Meteo_Met30'
TZ_TABLE=['CR6Irriwell1Router_tzs','CR6Irriwell2Meteo_tzs','CR6Irriwell3_tzs','CR6Irriwell4_tzs']
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
    else: 
        return render(request, "gs_app/upload.html")

def findOutliers(data):
    import numpy as np
    
    mean=np.mean(data)
    median=np.quantile(data,0.5,method='hazen')
    Q1 = np.percentile(data,25, interpolation='hazen')
    Q3 = np.percentile(data,75, interpolation='hazen')
    IQR = Q3-Q1
    lower_limit = Q1 - 1.5*IQR
    upper_limit = Q3 + 1.5*IQR
    outliers = [x for x in data if x < lower_limit or x > upper_limit]
    print(f"mean,median,Q1,Q3,IQR,lower_limit,upper_limit:{[mean,median,Q1,Q3,IQR,lower_limit,upper_limit]}")
    return(outliers)
def g_averages(data):
    pass
def read_gs(request):
    import plotly.graph_objects as go
    import plotly.express as px
    from plotly.subplots import make_subplots
    import pandas as pd
    #import sf2gs_app.dfg2db2 as dfg
    from datetime import datetime
    
    body_data = request.body.decode('utf-8')  # Decodificar los bytes en una cadena
    json_data = json.loads(body_data)
    outliers_removed=json_data['outliers_removed']
    rounds_removed=json_data['rounds_removed']
    print("OUTLIERS REMOVED: ",outliers_removed)
    print("ROUNDS REMOVED: ",rounds_removed)
    
    received_date=json_data['day']
    station=int(json_data['station'])
    tree=int(json_data['tree'].split(" ")[1])
    depth=int(json_data['depth'])
    canopy_zone=str(json_data['canopy_zone'])
    target_date = datetime.strptime(received_date, '%d/%m/%Y').date()
    label=f"S{station}T{tree}"
    #target_date = pd.to_datetime(recived_date, format='%d/%m/%Y').strftime('%Y-%m-%d')
    # Filtra el DataFrame por la fecha concreta utilizando df.query()
    #vdate=target_date.split("/")
    #vdate.reverse()
    #target_date="/".join(vdate)
    #print("day: ",target_date)
    
    #Read gs from DB and add round column to identify each round of repetitions
    DBTABLE='gs_irriwell2023'
    df=roundbox2023(DBTABLE,station=station,tree=tree,tree_zone=canopy_zone)
    rounds = df.groupby('round').agg({'timestamp': 'mean', 'gsw': 'mean'}).reset_index()

    #rounds.head()
    timestamps = pd.to_datetime(rounds["timestamp"])
    #print("timestamps",timestamps)
    tminutes = (timestamps - pd.Timestamp('1970-01-01')) // pd.Timedelta('1min')
    #print("pd.Timedelta('1min')",pd.Timedelta('1min'))
    #print("tminutes",tminutes)
    tminutes = tminutes.astype(int)
    #print("tminutes2",tminutes)

    tminutes=tminutes-tminutes[0]
    df["roundtime"]=[tminutes[r] for r in df["round"]]

    #Filtering by day:

    df['date']=df['timestamp'].dt.date
    #Removing outliers from dataframe:
    for o in outliers_removed:
        filter_outliers = (df['roundtime'] == int(float(o.split(' , ')[0]))) & (df['gsw'] == float(o.split(' , ')[2]))
        df=df[~filter_outliers]
    
    #df=df.query
    #days=sorted(list(set(df['date']))) #Days of measurement:
    #dfp=df.query('date == @target_date')
    dfp = df[df['date'] == target_date].copy()

    #rounds = df.groupby('round').agg({'timestamp': 'mean', 'gsw': 'mean'}).reset_index()
    rounds_day = dfp.groupby('round').agg({'roundtime': 'mean','timestamp': 'mean', 'gsw': 'mean'}).reset_index()
    timestamps = pd.to_datetime(rounds_day["timestamp"])
    #dfp["rounddate"] = dfp["round"].apply(lambda r: rounds["timestamp"][r])
    dfp.loc[:, "rounddate"] = dfp["round"].apply(lambda r: rounds_day.loc[rounds_day['round'] == r, 'timestamp'].iloc[0])

    #dfp["rounddate"]=[rounds["timestamp"][r] for r in dfp["round"]]
    #dfp["labels"] = dfp["rounddate"].apply(lambda t: t.strftime('%d/%m %H:%M'))
    dfp.loc[:, "labels"] = dfp["rounddate"].apply(lambda t: t.strftime('%d/%m %H:%M'))
    for r in rounds_removed:
        filter_rounds = (dfp['labels'] == r)
        dfp=dfp[~filter_rounds]
    #dfp["labels"]=[t.strftime('%d/%m %H:%M') for t in dfp["rounddate"]]
    dfg=g_averages(dfp)
    x_label = 'roundtime'
    y_label = 'gsw'
    #dfp=df.iloc[:36,:]
    fig = go.Figure(data=go.Box(x=dfp[x_label], y=dfp[y_label],boxpoints="all", boxmean=True))
    fig.update_layout(boxmode='overlay', height=400)
    fig.update_layout(title="gs variability "+label,title_x=0.5)
    fig.update_layout(margin=dict(l=20, r=20, t=40, b=20), paper_bgcolor="LightSteelBlue")

    fig.update_xaxes(
        tickmode='array',
        tickvals=dfp[x_label],
        ticktext=dfp["labels"],
        tickangle=45,
        #title_text="Date"
    )
    #print(dfp[[x_label,y_label]])
    outliers = dfp.groupby(x_label)[y_label].apply(findOutliers).reset_index()
    outliers_list=[]
    print("Listing outliers with timestamp")
    for id,r in enumerate(outliers[y_label]):
        if len(r)>0:
            for x in r:
                outlier_roundtime=rounds_day.loc[id,'roundtime']
                outlier_time=rounds_day.loc[id,'timestamp'].strftime('%Y-%m-%d %H:%M')
                outlier=str(outlier_roundtime)+" , "+outlier_time+" , "+str(x)
                outliers_list.append(outlier)
                #.push(outlier)
                #print("type: ",type(rounds_day.loc[id,'timestamp']))
                #print(outlier_time,", gsoutlier: ",x)
                print(outlier)
    
    rounds_list = list(set(dfp['labels']))
    rounds_list.sort()
    #print("rounds_day",rounds_day)
    #print(outliers)
    fig.update_yaxes(title_text="gs")
    chart = fig.to_json()

    meteo=obtiene_vpdypar(METEO_TABLE)
    meteo['timestamp']=pd.to_datetime(meteo['timestamp'])
    meteo['date']=meteo['timestamp'].dt.date
    dfpmet = meteo[meteo['date'] == target_date].copy()

    #INTERPOLATION gs vs Js/VPD
    #Calculate Js/vpd
    df_tz=obtiene_tzyvpd(TZ_TABLE[station-1],METEO_TABLE)
    df_Js_VPD=calculaJs_VPD(df_tz)
    #df_Js_VPD.to_excel(f"Js_VPD_Est{s}")
    dfj0=df_Js_VPD.copy()
    # particularize for a specific tree and thermocouple depth (in DB thermocouple deepth use oposite notation 0: deep  and 1: shalow)
    dfj=dfj0.query(f"arbol=={tree} and sup=={int(not(depth))}")[["Js_VPD"]] 
    #2. Interpolate Js/VPD to the times where gs was measured

    dfgs = dfp.groupby('round').agg({'rounddate': 'first', 'gsw': 'mean'}).reset_index()#['gsw'].mean().reset_index()

    # Seleccionar solo las columnas 'timestamp' y 'gsw' promediado
    dfgs = dfgs[['rounddate', 'gsw']]
    dfgs = dfgs.rename(columns={'rounddate': 'timestamp'})
    dfjg=interpoleJs(dfj,dfgs) #the resulting dataframe includes the interpolated Js/VPD and gs at the corresponding measuring times
    #3. Linear regresion correlation
    fig_reg=regresion(dfjg)

    # #vble_to_plot2='par'
    # vble_x2='timestamp'
    # scatter2 = px.scatter(dfpmet, x=vble_x2, y='par',
    #             title="")
    # scatter2.update_traces(marker=dict(size=6, opacity=0.6), selector=dict(mode='markers'))
    # scatter3 = px.scatter(dfpmet, x=vble_x2, y='vpd',
    #             title="", name='vpd')
    # scatter3.update_traces(marker=dict(size=6, opacity=0.6), selector=dict(mode='markers'))

    # fig2 = make_subplots(rows=1, cols=1,horizontal_spacing = 0.5,vertical_spacing=0.5, shared_xaxes=True,specs=[[{'secondary_y': True}]])
    # fig2.update_layout(boxmode='overlay', width=800, height=300)
    # fig2.add_trace(scatter2['data'][0], row=1, col=1, secondary_y=False)
    # fig2.add_trace(scatter3['data'][0], row=1, col=1, secondary_y=True)
    # # Configurar el primer eje (izquierdo)
    # fig2.update_yaxes(title_text='par', secondary_y=True)

    # # Configurar el segundo eje (derecho)
    # fig2.update_yaxes(title_text='vpd', secondary_y=True, overlaying='y', side='right')
    # fig2.update_traces(mode='lines')
    # fig2.update_traces(line_color='red', selector=dict(name='vpd'))
    # #fig2.update_xaxes(title_text=vble_x2)
    # #fig2.update_yaxes(title_text='par',side='left')
    # fig2.update_layout(coloraxis=dict(colorscale='viridis'), showlegend=True,margin=dict(l=20, r=20, t=20, b=20),
    # paper_bgcolor="LightSteelBlue") #,paper_bgcolor='rgba(0,0,0,0)'
    # Create figure with secondary y-axis
    # fig2 = make_subplots(specs=[[{"secondary_y": True}]])
    # fig2.add_trace(go.Scatter(x=dfpmet['timestamp'], y=dfpmet['par'], name="PAR2"),secondary_y=False,)
    # fig2.add_trace(go.Scatter(x=dfpmet['timestamp'], y=dfpmet['vpd'], name="VPD2"),secondary_y=True,)
    # fig2.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    # fig2.update_yaxes(title_text="<b>PAR2</b>", secondary_y=False)
    # fig2.update_yaxes(title_text="<b>VPD2</b>", secondary_y=True)
    # fig2.update_layout(paper_bgcolor="LightSteelBlue",legend=dict(x=0,y=1,traceorder='normal',orientation='h',xanchor='left',yanchor='top'))
    chart2 = fig_reg.to_json()
    fig3 = make_subplots(specs=[[{"secondary_y": True}]])
    fig3.add_trace(go.Scatter(x=dfpmet['timestamp'], y=dfpmet['par'], name="PAR"),secondary_y=False,)
    fig3.add_trace(go.Scatter(x=dfpmet['timestamp'], y=dfpmet['vpd'], name="VPD"),secondary_y=True,)
    fig3.update_layout(height=400, margin=dict(l=20, r=20, t=20, b=20))
    fig3.update_yaxes(title_text="<b>PAR</b>", secondary_y=False)
    fig3.update_yaxes(title_text="<b>VPD</b>", secondary_y=True)
    fig3.update_layout(paper_bgcolor="LightSteelBlue",legend=dict(x=0,y=1,traceorder='normal',orientation='h',xanchor='left',yanchor='top'))
    chart3 = fig3.to_json()


    response_data = {'chart': chart,'chart2': chart2,'chart3': chart3,'outliers': outliers_list,'rounds': rounds_list}
    return JsonResponse(response_data)
    
def index(request):
    
    df=db2df(DBTABLE)
    print(df)
    days=gs_days(df)
    stations=list(set(df['irriwell']))
    fdays =[{"daytime":day.strftime('%d/%m/%Y'),"str":day.strftime('%d/%m/%Y')} for day in days]
    #print(fdays)
    #return render(request, "gs_app/gs.html",{ "days": fdays,"df":df.to_html()})
    return render(request, "gs_app/gs.html",{ "days": fdays,"stations":stations})
