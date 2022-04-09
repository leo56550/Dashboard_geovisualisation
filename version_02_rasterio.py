import os
import math

import numpy as np
import rasterio as rio

try:
    from dash import Dash, html, dcc, Input, Output
except:
    from dash import Dash
    import dash_html_components as html
    import dash_core_components as dcc
    from dash.dependencies import Input, Output
import plotly.express as px
from plotly.subplots import make_subplots

# Data preparation and storage
data_folder = r'.\data'
store = {}

for filename in os.listdir(data_folder):
    if os.path.isfile(os.path.join(data_folder, filename)):
        band_name = filename.replace('.', '_').split(sep='_')[-2]
        with rio.open(os.path.join(data_folder, filename)) as dataset:
            nb_band = dataset.count
            if nb_band == 1:
                data = dataset.read(1)
            else:
                data = dataset.read(tuple(range(1, nb_band + 1)))

            if band_name == 'triband':
                data = np.swapaxes(data, 2, 0)
                data = np.swapaxes(data, 0, 1)
                store[band_name] = data.astype(float)
            else:
                store[f'B{band_name}'] = data.astype(float)

index_store = {
    'TCARI': (store['B03']*((store['B05']-store['B04'])-0.2*(store['B05']-store['B03'])*(store['B05']/store['B04']))),
    'VI700': ((store['B05'] - store['B04']) / (store['B05'] + store['B04'])),
    'Soil Composition Index': ((store['B11'] - store['B08A']) / (store['B11'] + store['B08A'])),
}

min_max = {k: (np.min(index_store[k]), np.max(index_store[k]), np.median(index_store[k])) for k in index_store.keys()}

# Initialisation of Plotly graphs
fig = make_subplots(rows=1, cols=3, shared_xaxes=True, shared_yaxes=True)
fig.add_trace(
    px.imshow(store['triband']).data[0],
    row=1, col=1
)

fig.add_trace(
    px.imshow(index_store['TCARI']).data[0],
    row=1, col=2
)

fig.add_trace(
    px.imshow(np.where(index_store['TCARI'] >= np.median(index_store['TCARI']),
                       0.8 * np.max(index_store['TCARI']),
                       0.8 * np.min(index_store['TCARI']))
              ).data[0],
    row=1, col=3
)

fig.update_xaxes(matches='x', showticklabels=False, showgrid=False, zeroline=False)
fig.update_yaxes(matches='y', showticklabels=False, showgrid=False, zeroline=False)
fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), plot_bgcolor='rgba(0, 0, 0, 0)', paper_bgcolor='rgba(0, 0, 0, 0)')


# Functions
def set_limit(limits, idx):
    if limits[idx] < 0:
        val = round(math.floor(limits[idx] * 100.) / 100., 1)
    else:
        val = round(math.ceil(limits[idx] * 100.) / 100., 1)
    return val



# Application structure and content
app = Dash(__name__)

app.layout = html.Div(children=[
    html.Div(children =[
        html.H1(children='Land Analyzer', style={'padding': 10, 'flex': 1}),

        html.Div(children=[
            html.H3('Remote sensing indicator'),
            dcc.Dropdown(id='indices-list', options=['TCARI', 'VI700', 'Soil Composition Index'], value='TCARI')
        ], style={'padding': 10, 'flex': 1}),

        html.Div(children=[
            html.H3('Threshold'),
            dcc.Slider(min=set_limit(min_max['TCARI'], 0),
                       max=set_limit(min_max['TCARI'], 1),
                       marks=None,
                       tooltip={"placement": "bottom", "always_visible": True},
                       value=set_limit(min_max['TCARI'], 2),
                       id='my-slider')
        ], style={'padding': 10, 'flex': 1})

    ], style={'display': 'flex', 'flex-direction': 'row'}),

    html.Div(className="plots", children=[

        html.Div(children=[
            dcc.Graph(
                id='graph1',
                figure=fig,
                responsive=True
            )
        ], style={'padding': 1, 'flex': 3}),
    ], style={'height': '100%', 'display': 'flex', 'flex-direction': 'row'}),
], style={'height': '100%'})

# Callbacks
@app.callback(
    Output('graph1', 'figure'),
    [Input('indices-list', 'value'),
     Input('my-slider', 'value')])
def update_figure(selected_index, thd):
    fig2 = make_subplots(rows=1, cols=3)
    fig2.add_trace(
        px.imshow(store['triband']).data[0],
        row=1, col=1
    )
    fig2.add_trace(
        px.imshow(index_store[selected_index]).data[0],
        row=1, col=2
    )
    fig2.add_trace(
        px.imshow(np.where(index_store[selected_index] >= thd,
                           0.8 * np.max(index_store[selected_index]),
                           0.8 * np.min(index_store[selected_index]))
                  ).data[0],
        row=1, col=3
    )
    fig2.update_xaxes(matches='x', showticklabels=False, showgrid=False, zeroline=False)
    fig2.update_yaxes(matches='y', showticklabels=False, showgrid=False, zeroline=False)
    fig2.update_layout(margin=dict(l=0, r=0, t=0, b=0),
                       plot_bgcolor='rgba(0, 0, 0, 0)',
                       paper_bgcolor='rgba(0, 0, 0, 0)',
                       uirevision="Don't change"
                       )
    return fig2


@app.callback(
    [Output('my-slider', 'min'),
     Output('my-slider', 'max'),
     Output('my-slider', 'value')],
    Input('indices-list', 'value'))
def update_slider(selected_index):
    new_min = set_limit(min_max[selected_index], 0)
    new_max = set_limit(min_max[selected_index], 1)
    new_value = set_limit(min_max[selected_index], 2)
    return new_min, new_max, new_value

if __name__ == '__main__':
    app.run_server(debug=False)