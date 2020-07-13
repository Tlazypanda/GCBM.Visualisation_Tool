"""The Dash-based front-end"""
import dash
import dash_core_components as dcc
import dash_html_components as html
import dash_leaflet as dl
import plotly.graph_objects as go
import terracotta as tc
from dash.dependencies import Input, Output


def _get_data():
    driver = tc.get_driver(tc.get_settings().DRIVER_PATH)
    data = {}
    with driver.connect():
        for k in driver.get_datasets():
            title, year = k
            if not title in data:
                data[title] = {}
            data[title][year] = driver.get_metadata(k)
    return data


def format_bounds(bounds):
    """Formats tuple of bounds for Leaflet.

    Args:
        bounds: A 4 element tuple of bounds.

    Returns:
        Nested list as required by Leaflet.
    """
    return [[bounds[1], bounds[0]], [bounds[3], bounds[2]]]


def get_app(tc_app):
    """Create a new Dash instance with a Terracotta instance embedded in it.

    Args:
        tc_app: Flask instance of Terracotta

    Returns:
        A Flask instance of a Dash app.
    """
    # pylint: disable=unused-variable
    data = _get_data()
    app = dash.Dash(__name__, server=tc_app, routes_pathname_prefix='/dash/')
    options = [{'label': k, 'value': k} for k in list(data)]
    app.layout = html.Div(
        [
            dcc.Dropdown(id='title-dropdown',
                         clearable=False,
                         options=options,
                         value=options[0]['value'],
                         style={
                             'position': 'relative',
                             'top': '10px',
                             'z-index': '500',
                             'height': '0',
                             'max-width': '200px',
                             'margin-left': 'auto',
                             'margin-right': '10px'
                         }),
            html.Div(id='main-map',
                     style={
                         'position': 'relative',
                         'width': '100%',
                         'height': '70%',
                         'top': '0',
                         'left': '0'
                     }),
            html.Div(
                [dcc.Slider(
                    id='year-slider',
                    step=None,
                    value=0,
                )],
                style={
                    'position': 'relative',
                    'top': '-75px',
                    'z-index': '500',
                    'height': '0'
                }),
            dcc.Graph(id='indicator-change-graph', style={'width': '100%'})
        ],
        style={
            'position': 'absolute',
            'width': '100%',
            'height': '100%',
            'top': '0',
            'left': '0',
            'font-family': 'sans-serif'
        })

    @app.callback(
        Output('main-map', 'children'),
        [Input('title-dropdown', 'value'),
         Input('year-slider', 'value')])
    def update_map(title, year):
        bounds = format_bounds(data[title][str(year)]['bounds'])
        xyz = '{z}/{x}/{y}'
        leafmap = dl.Map([
            dl.TileLayer(),
            dl.TileLayer(url=f'/singleband/{title}/{year}/{xyz}.png')
        ],
                         bounds=bounds)
        return leafmap

    @app.callback([
        Output('year-slider', 'marks'),
        Output('year-slider', 'min'),
        Output('year-slider', 'max'),
        Output('year-slider', 'value'),
    ], [Input('title-dropdown', 'value')])
    def update_slider(title):
        mark_style = {'color': '#fff', 'text-shadow': '1px 1px 2px #000'}
        marks = {
            int(k): dict(label=k, style=mark_style)
            for k in data[title].keys()
        }
        value = min(marks.keys())
        return marks, value, max(marks.keys()), value

    @app.callback(Output('indicator-change-graph', 'figure'),
                  [Input('title-dropdown', 'value')])
    def update_graph(title):
        fig = go.Figure()
        x_marks = []
        y_margs = []
        for year, meta in data[title].items():
            x_marks.append(year)
            y_margs.append(meta['metadata'][title])
        fig.add_trace(go.Scatter(x=x_marks, y=y_margs, mode='lines+markers'))
        fig.update_layout(autosize=False,
                          xaxis_title='Year',
                          yaxis_title=title,
                          xaxis_type='category',
                          height=150,
                          margin=dict(t=10, b=0))
        return fig

    return app