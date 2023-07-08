from dash import html, dcc
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from app import app

# Componentes
from _map import *
from _histogram import *
from _controllers import *



# ================================================
# Data ingestion
# ================================================

df_data = pd.read_csv("dataset\cleaned_data.csv", index_col=0)
# print(df_data)

# Longitude e Latitude dos imoveis (retirados atraves de uma api)
mean_lat = df_data["LATITUDE"].mean()
mean_long = df_data["LONGITUDE"].mean()

# Conversão de medida de Pés para Metros 
df_data["size_m2"] = df_data["GROSS SQUARE FEET"] / 10.764

# Retira os imoveis que estão sem dados de ano
df_data = df_data[df_data["YEAR BUILT"] > 0]

# pré-processamento para arrumar a tipagem da data (estava como objeto pandas, iremos passar para datetime)
df_data["SALE DATE"] = pd.to_datetime(df_data["SALE DATE"])

# Para melhorar a visualização dos imoveis no grafico, quando a metragem do imovel passar de 10.000, eu digo para o grafico que ele tem 10.000 metros² para que não afetar no visual final
df_data.loc[df_data["size_m2"] > 10000, "size_m2"] = 10000

# Seguindo a mesma ideia acima, tambem padronizei alguns valors, para quando o valor do imovel ultrapassar os 50 milhoes, ele exiba apenas os 50 milhores (nesse dataset temos as vendas de varios imoveis, não apenas residenciais por isso os valores podem variar bastante).
df_data.loc[df_data["SALE PRICE"] > 50000000, "SALE PRICE"] = 50000000

# o mesmo so que agora para os menores de 100 mil.
df_data.loc[df_data["SALE PRICE"] < 100000, "SALE PRICE"] = 100000


# ================================================
# Layout
# ================================================

app.layout = dbc.Container(
        children=[
          dbc.Row([
                dbc.Col([controllers], md=3),
                dbc.Col([map, hist], md=9),
              
          ])  
            

        ], fluid=True, )

# ========================================================
# Callbacks 
@app.callback([Output('hist-graph', 'figure'), Output('map-graph', 'figure')],
            [Input('location-dropdown', 'value'), 
            Input('slider-square-size', 'value'), 
            Input('dropdown-color', 'value')]            
            )
def update_hist(location, square_size, color_map):
    if location is None:
            df_intermediate = df_data.copy()
    else:
        df_intermediate = df_data[df_data["BOROUGH"] == location] if location != 0 else df_data.copy()
        size_limit = slider_size[square_size] if square_size is not None else df_data["GROSS SQUARE FEET"].max()
        df_intermediate = df_intermediate[df_intermediate["GROSS SQUARE FEET"] <= size_limit]

    # ==========================
    # Histogram
    hist_fig = px.histogram(df_intermediate, x=color_map, opacity=0.75)
    hist_layout = go.Layout(
        margin=go.layout.Margin(l=10, r=0, t=0, b=50),
        showlegend=False, 
        template="plotly_dark", 
        paper_bgcolor="rgba(0, 0, 0, 0)")
    hist_fig.layout = hist_layout

    # ==========================
    # Map
    px.set_mapbox_access_token(open("keys/mapbox_key").read())
    map_fig = px.scatter_mapbox(df_intermediate, lat="LATITUDE", lon="LONGITUDE", color=color_map, 
                    size="size_m2", size_max=20, zoom=10, opacity=0.4)

    map_fig.update_layout(mapbox=dict(center=go.layout.mapbox.Center(lat=mean_lat, lon=mean_long)), 
            template="plotly_dark", paper_bgcolor="rgba(0, 0, 0, 0)", 
            margin=go.layout.Margin(l=10, r=10, t=10, b=10),)

    return hist_fig, map_fig

if __name__ == '__main__':
    app.run_server(debug=True)